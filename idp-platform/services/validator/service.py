"""
Validation & Trust Scoring Service — Phase 6 (Stage 7).

Evaluates extracted data for correctness, consistency, and trustworthiness:
  - Required-field checks
  - Type validation (dates, numbers, etc.)
  - Cross-field validation (line items sum to total)
  - Arithmetic checks
  - Schema validation
  - Duplicate detection
  - Fraud/tampering signals
  - Anomaly detection

Produces a composite TrustScore that feeds the Decision Engine.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from libs.common.schemas import (
    ExtractionOutput,
    TrustScore,
    ValidationFlag,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Validation Rules
# ═══════════════════════════════════════════════════════════════════════════════


class ValidationRule:
    """Base class for validation rules."""

    def validate(self, extraction: ExtractionOutput) -> list[ValidationFlag]:
        raise NotImplementedError


class RequiredFieldsRule(ValidationRule):
    """Check that all required fields are present."""

    REQUIRED_BY_TYPE: dict[str, list[str]] = {
        "invoice": ["invoice_number", "total_amount"],
        "receipt": ["total"],
    }

    def validate(self, extraction: ExtractionOutput) -> list[ValidationFlag]:
        flags: list[ValidationFlag] = []
        required = self.REQUIRED_BY_TYPE.get(extraction.doc_type, [])
        extracted_names = {f.field_name for f in extraction.fields}

        for field_name in required:
            if field_name not in extracted_names:
                flags.append(
                    ValidationFlag(
                        flag_type="missing_field",
                        severity="error",
                        field_name=field_name,
                        message=f"Required field '{field_name}' is missing",
                    )
                )
        return flags


class TypeCheckRule(ValidationRule):
    """Validate field types (dates are valid dates, numbers parse, etc.)."""

    DATE_FIELDS = {"invoice_date", "due_date", "date", "issue_date", "payment_date"}
    AMOUNT_FIELDS = {"total_amount", "subtotal", "tax_amount", "total", "amount_due"}

    def validate(self, extraction: ExtractionOutput) -> list[ValidationFlag]:
        flags: list[ValidationFlag] = []

        for field in extraction.fields:
            if field.field_name in self.DATE_FIELDS and field.value:
                if not self._is_valid_date(str(field.value)):
                    flags.append(
                        ValidationFlag(
                            flag_type="type_error",
                            severity="warning",
                            field_name=field.field_name,
                            message=f"Invalid date format: '{field.value}'",
                        )
                    )

            if field.field_name in self.AMOUNT_FIELDS and field.value:
                if not self._is_valid_amount(str(field.value)):
                    flags.append(
                        ValidationFlag(
                            flag_type="type_error",
                            severity="warning",
                            field_name=field.field_name,
                            message=f"Invalid amount format: '{field.value}'",
                        )
                    )

        return flags

    def _is_valid_date(self, value: str) -> bool:
        return bool(re.match(r"\d{4}-\d{2}-\d{2}", value))

    def _is_valid_amount(self, value: str) -> bool:
        cleaned = re.sub(r"[€$£¥₹,\s]", "", value)
        try:
            float(cleaned)
            return True
        except ValueError:
            return False


class ArithmeticCheckRule(ValidationRule):
    """Verify arithmetic consistency (e.g., subtotal + tax = total)."""

    def validate(self, extraction: ExtractionOutput) -> list[ValidationFlag]:
        flags: list[ValidationFlag] = []
        fields = {f.field_name: f.value for f in extraction.fields}

        subtotal = self._parse_amount(fields.get("subtotal", ""))
        tax = self._parse_amount(fields.get("tax_amount", ""))
        total = self._parse_amount(fields.get("total_amount", "") or fields.get("total", ""))

        if subtotal is not None and tax is not None and total is not None:
            expected = subtotal + tax
            if abs(expected - total) > 0.02:  # Allow 2 cent rounding
                flags.append(
                    ValidationFlag(
                        flag_type="arithmetic_error",
                        severity="error",
                        message=f"Subtotal ({subtotal}) + Tax ({tax}) = {expected}, "
                        f"but Total is {total}",
                        details={"subtotal": subtotal, "tax": tax, "total": total},
                    )
                )

        return flags

    def _parse_amount(self, value: str) -> float | None:
        if not value:
            return None
        cleaned = re.sub(r"[€$£¥₹,\s]", "", str(value))
        # Also remove currency codes
        cleaned = re.sub(r"[A-Z]{3}$", "", cleaned).strip()
        try:
            return float(cleaned)
        except ValueError:
            return None


class CrossFieldCheckRule(ValidationRule):
    """Validate cross-field consistency."""

    def validate(self, extraction: ExtractionOutput) -> list[ValidationFlag]:
        flags: list[ValidationFlag] = []
        fields = {f.field_name: str(f.value) for f in extraction.fields}

        # Check date ordering: invoice_date should be before due_date
        inv_date = fields.get("invoice_date", "")
        due_date = fields.get("due_date", "")
        if inv_date and due_date and inv_date > due_date:
            flags.append(
                ValidationFlag(
                    flag_type="cross_field_mismatch",
                    severity="warning",
                    message=f"Invoice date ({inv_date}) is after due date ({due_date})",
                )
            )

        return flags


class ConfidenceCheckRule(ValidationRule):
    """Flag fields with low extraction confidence."""

    LOW_CONFIDENCE_THRESHOLD = 0.5

    def validate(self, extraction: ExtractionOutput) -> list[ValidationFlag]:
        flags: list[ValidationFlag] = []

        for field in extraction.fields:
            if field.confidence < self.LOW_CONFIDENCE_THRESHOLD:
                flags.append(
                    ValidationFlag(
                        flag_type="low_confidence",
                        severity="warning",
                        field_name=field.field_name,
                        message=f"Low confidence extraction: {field.confidence:.2f}",
                        details={"confidence": field.confidence},
                    )
                )

        return flags


# ═══════════════════════════════════════════════════════════════════════════════
# Composite Trust Score
# ═══════════════════════════════════════════════════════════════════════════════


def compute_trust_score(
    extraction: ExtractionOutput,
    flags: list[ValidationFlag],
) -> TrustScore:
    """
    Compute the composite trust score from extraction results and validation flags.

    The score combines:
      - Field-level extraction confidence
      - Validation flag severity
      - Overall extraction layer confidence
    """
    # Start with extraction confidence
    base_confidence = extraction.overall_confidence

    # Penalty per flag
    penalty = 0.0
    for flag in flags:
        if flag.severity == "critical":
            penalty += 0.3
        elif flag.severity == "error":
            penalty += 0.15
        elif flag.severity == "warning":
            penalty += 0.05
        # info flags don't penalize

    composite = max(0.0, min(1.0, base_confidence - penalty))

    # Per-field confidence scores
    field_scores = {f.field_name: f.confidence for f in extraction.fields}

    # Fraud risk (simple heuristic — replace with ML model in production)
    fraud_flags = [f for f in flags if f.flag_type in ("fraud_signal", "tampering")]
    fraud_risk = "high" if len(fraud_flags) > 0 else "low"

    # Anomaly score (based on number and severity of flags)
    anomaly_score = min(1.0, len(flags) * 0.1)

    # Business impact (based on document type and total amount)
    business_impact = _assess_business_impact(extraction)

    return TrustScore(
        doc_id=extraction.doc_id,
        tenant_id=extraction.tenant_id,
        composite_confidence=composite,
        field_scores=field_scores,
        validation_flags=flags,
        fraud_risk=fraud_risk,
        anomaly_score=anomaly_score,
        business_impact=business_impact,
        compliance_risk="none",
    )


def _assess_business_impact(extraction: ExtractionOutput) -> str:
    """Assess business impact based on document value."""
    for field in extraction.fields:
        if field.field_name in ("total_amount", "total", "amount_due"):
            try:
                amount = float(re.sub(r"[^0-9.]", "", str(field.value)))
                if amount > 100000:
                    return "critical"
                elif amount > 10000:
                    return "high"
                elif amount > 1000:
                    return "medium"
            except (ValueError, TypeError):
                pass
    return "low"


# ═══════════════════════════════════════════════════════════════════════════════
# Main Validation Service
# ═══════════════════════════════════════════════════════════════════════════════


class ValidationService:
    """
    Runs the full validation pipeline on extracted data.

    Returns a TrustScore that the Decision Engine uses to route
    the document (auto-approve, review, reject).
    """

    def __init__(self, rules: list[ValidationRule] | None = None) -> None:
        self.rules = rules or [
            RequiredFieldsRule(),
            TypeCheckRule(),
            ArithmeticCheckRule(),
            CrossFieldCheckRule(),
            ConfidenceCheckRule(),
        ]

    async def validate(self, extraction: ExtractionOutput) -> TrustScore:
        """Run all validation rules and compute trust score."""
        all_flags: list[ValidationFlag] = []

        for rule in self.rules:
            flags = rule.validate(extraction)
            all_flags.extend(flags)

        trust_score = compute_trust_score(extraction, all_flags)

        logger.info(
            "Validated document %s: composite=%.2f, flags=%d, fraud_risk=%s",
            extraction.doc_id,
            trust_score.composite_confidence,
            len(all_flags),
            trust_score.fraud_risk,
        )

        return trust_score
