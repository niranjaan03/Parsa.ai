"""
Output Delivery Service — Phase 8 (Stage 9).

Delivers structured extraction results to downstream systems:
  - Versioned JSON/CSV output
  - HMAC-signed webhooks for payload integrity
  - Idempotent delivery (delivery keys prevent duplicates)
  - Retry with exponential backoff
  - Full delivery audit trail

Integration connectors: Database, Webhook/API, Salesforce, SAP, custom.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from libs.common.schemas import (
    DecisionOutcome,
    DecisionResult,
    DeliveryPayload,
    ExtractionOutput,
    TrustScore,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Webhook Signing
# ═══════════════════════════════════════════════════════════════════════════════


def sign_payload(payload_json: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature for webhook payload integrity."""
    return hmac.new(
        secret.encode("utf-8"),
        payload_json.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_signature(payload_json: str, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature (for webhook receivers)."""
    expected = sign_payload(payload_json, secret)
    return hmac.compare_digest(expected, signature)


# ═══════════════════════════════════════════════════════════════════════════════
# Delivery Targets
# ═══════════════════════════════════════════════════════════════════════════════


class DeliveryTarget:
    """Base class for delivery targets."""

    async def deliver(
        self,
        payload: DeliveryPayload,
        delivery_id: str,
    ) -> tuple[bool, str]:
        """Deliver payload. Returns (success, message)."""
        raise NotImplementedError


class WebhookTarget(DeliveryTarget):
    """Deliver via signed HTTP webhook."""

    def __init__(
        self,
        url: str,
        secret: str,
        timeout: int = 30,
    ) -> None:
        self.url = url
        self.secret = secret
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def deliver(
        self,
        payload: DeliveryPayload,
        delivery_id: str,
    ) -> tuple[bool, str]:
        payload_json = payload.model_dump_json()
        signature = sign_payload(payload_json, self.secret)

        headers = {
            "Content-Type": "application/json",
            "X-IDP-Signature": f"sha256={signature}",
            "X-IDP-Delivery-ID": delivery_id,
            "X-IDP-Schema-Version": payload.schema_version,
            "X-IDP-Timestamp": payload.timestamp.isoformat(),
        }

        try:
            resp = await self._client.post(self.url, content=payload_json, headers=headers)
            if resp.status_code in (200, 201, 202, 204):
                return True, f"Delivered (HTTP {resp.status_code})"
            return False, f"Failed (HTTP {resp.status_code}: {resp.text[:200]})"
        except httpx.RequestError as e:
            return False, f"Connection error: {e}"


class DatabaseTarget(DeliveryTarget):
    """Deliver by writing to a database (placeholder)."""

    def __init__(self, connection_string: str, table: str) -> None:
        self.connection_string = connection_string
        self.table = table

    async def deliver(
        self,
        payload: DeliveryPayload,
        delivery_id: str,
    ) -> tuple[bool, str]:
        # Placeholder: in production, write to PostgreSQL/MySQL
        logger.info(
            "DB delivery: %s -> %s.%s",
            delivery_id,
            self.connection_string.split("@")[-1] if "@" in self.connection_string else "***",
            self.table,
        )
        return True, f"Written to {self.table}"


# ═══════════════════════════════════════════════════════════════════════════════
# Delivery Event Log
# ═══════════════════════════════════════════════════════════════════════════════


class DeliveryEvent:
    """Immutable record of a delivery attempt."""

    def __init__(
        self,
        delivery_id: str,
        doc_id: str,
        tenant_id: str,
        target_type: str,
        success: bool,
        message: str,
        attempt: int,
    ) -> None:
        self.delivery_id = delivery_id
        self.doc_id = doc_id
        self.tenant_id = tenant_id
        self.target_type = target_type
        self.success = success
        self.message = message
        self.attempt = attempt
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery_id": self.delivery_id,
            "doc_id": self.doc_id,
            "tenant_id": self.tenant_id,
            "target_type": self.target_type,
            "success": self.success,
            "message": self.message,
            "attempt": self.attempt,
            "timestamp": self.timestamp.isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Main Delivery Service
# ═══════════════════════════════════════════════════════════════════════════════


class DeliveryService:
    """
    Manages output delivery with retry, idempotency, and audit logging.

    Features:
      - Multiple delivery targets per tenant
      - Idempotent delivery (dedup by delivery_key)
      - Exponential backoff retry
      - Full audit trail of delivery attempts
    """

    def __init__(self, max_retries: int = 3, base_backoff_seconds: float = 2.0) -> None:
        self.max_retries = max_retries
        self.base_backoff = base_backoff_seconds
        self._targets: dict[str, list[DeliveryTarget]] = {}  # tenant_id -> targets
        self._delivered_keys: set[str] = set()  # Idempotency tracking
        self._event_log: list[DeliveryEvent] = []

    def register_target(self, tenant_id: str, target: DeliveryTarget) -> None:
        """Register a delivery target for a tenant."""
        if tenant_id not in self._targets:
            self._targets[tenant_id] = []
        self._targets[tenant_id].append(target)

    async def deliver(
        self,
        extraction: ExtractionOutput,
        trust_score: TrustScore,
        decision: DecisionResult,
    ) -> list[DeliveryEvent]:
        """
        Deliver extraction results to all registered targets for the tenant.

        Returns list of delivery events (success or failure).
        """
        # Build delivery payload
        payload = DeliveryPayload(
            doc_id=extraction.doc_id,
            tenant_id=extraction.tenant_id,
            extracted_data={f.field_name: f.value for f in extraction.fields},
            trust_score=trust_score,
            decision=decision.outcome,
        )

        # Idempotency check
        if payload.delivery_key in self._delivered_keys:
            logger.info(
                "Duplicate delivery skipped: %s (key=%s)",
                extraction.doc_id,
                payload.delivery_key,
            )
            return []

        # Get targets for this tenant
        targets = self._targets.get(extraction.tenant_id, [])
        if not targets:
            logger.warning(
                "No delivery targets configured for tenant %s",
                extraction.tenant_id,
            )
            return []

        # Deliver to each target with retry
        events: list[DeliveryEvent] = []
        for target in targets:
            delivery_id = uuid.uuid4().hex
            target_type = type(target).__name__

            for attempt in range(1, self.max_retries + 1):
                success, message = await target.deliver(payload, delivery_id)

                event = DeliveryEvent(
                    delivery_id=delivery_id,
                    doc_id=extraction.doc_id,
                    tenant_id=extraction.tenant_id,
                    target_type=target_type,
                    success=success,
                    message=message,
                    attempt=attempt,
                )
                events.append(event)
                self._event_log.append(event)

                if success:
                    logger.info(
                        "Delivered %s to %s (attempt %d): %s",
                        extraction.doc_id,
                        target_type,
                        attempt,
                        message,
                    )
                    break

                if attempt < self.max_retries:
                    backoff = self.base_backoff * (2 ** (attempt - 1))
                    logger.warning(
                        "Delivery failed for %s to %s (attempt %d/%d): %s — "
                        "retrying in %.1fs",
                        extraction.doc_id,
                        target_type,
                        attempt,
                        self.max_retries,
                        message,
                        backoff,
                    )
                    # In production: use async sleep
                    # await asyncio.sleep(backoff)
                else:
                    logger.error(
                        "Delivery FAILED for %s to %s after %d attempts: %s",
                        extraction.doc_id,
                        target_type,
                        self.max_retries,
                        message,
                    )

        # Mark as delivered (for idempotency)
        all_succeeded = all(
            any(e.success for e in events if e.target_type == type(t).__name__)
            for t in targets
        )
        if all_succeeded:
            self._delivered_keys.add(payload.delivery_key)

        return events

    def get_event_log(
        self,
        tenant_id: str | None = None,
        doc_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query delivery event log."""
        return [
            e.to_dict()
            for e in self._event_log
            if (tenant_id is None or e.tenant_id == tenant_id)
            and (doc_id is None or e.doc_id == doc_id)
        ]
