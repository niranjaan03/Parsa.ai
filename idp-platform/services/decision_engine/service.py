"""
Decision Engine — Phase 7 (Stage 8).

Routes documents to one of four outcomes based on TrustScore:
  1. Auto-approve  → confidence ≥ threshold, no critical flags
  2. Reprocess     → specific stage failed, retryable
  3. Human review  → edge case, low confidence, prioritized by impact
  4. Reject        → fraud detected, unsupported format

The review queue is prioritized by:
  value × regulatory importance × field criticality × anomaly score × SLA
"""

from __future__ import annotations

import logging
from typing import Any

from libs.common.schemas import (
    DecisionOutcome,
    DecisionResult,
    ExtractionOutput,
    TenantConfig,
    TrustScore,
)
from libs.common.job_states import JobState

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Makes auto-approve / review / reject decisions for processed documents.

    Thresholds are configurable per tenant:
      - auto_approve_threshold: minimum composite confidence for auto-approval
      - Fraud risk "high" → always reject/quarantine
      - Critical validation flags → always human review
    """

    def __init__(
        self,
        default_auto_threshold: float = 0.90,
        default_review_threshold: float = 0.60,
    ) -> None:
        self.default_auto_threshold = default_auto_threshold
        self.default_review_threshold = default_review_threshold

    async def decide(
        self,
        extraction: ExtractionOutput,
        trust_score: TrustScore,
        tenant_config: TenantConfig | None = None,
    ) -> DecisionResult:
        """
        Make a routing decision based on trust score and tenant policy.

        Decision matrix:
          fraud_risk == "high"           → REJECTED / QUARANTINED
          has_critical_flags             → HUMAN_REVIEW (high priority)
          confidence >= auto_threshold   → AUTO_APPROVED
          confidence >= review_threshold → HUMAN_REVIEW
          confidence < review_threshold  → REPROCESS (try again with different strategy)
        """
        auto_threshold = self.default_auto_threshold
        review_threshold = self.default_review_threshold

        if tenant_config:
            auto_threshold = tenant_config.auto_approve_threshold
            review_threshold = tenant_config.ml_approve_threshold

        # ── Rule 1: Fraud → Reject ──
        if trust_score.fraud_risk == "high":
            return DecisionResult(
                doc_id=trust_score.doc_id,
                tenant_id=trust_score.tenant_id,
                outcome=DecisionOutcome.QUARANTINED,
                reason=f"High fraud risk detected (anomaly_score={trust_score.anomaly_score:.2f})",
                review_priority=1.0,
            )

        # ── Rule 2: Critical flags → Human review ──
        if trust_score.has_critical_flags:
            return DecisionResult(
                doc_id=trust_score.doc_id,
                tenant_id=trust_score.tenant_id,
                outcome=DecisionOutcome.HUMAN_REVIEW,
                reason=f"Critical validation flags: {trust_score.error_count} errors",
                review_priority=self._compute_priority(trust_score),
            )

        # ── Rule 3: High confidence → Auto-approve ──
        if trust_score.composite_confidence >= auto_threshold:
            return DecisionResult(
                doc_id=trust_score.doc_id,
                tenant_id=trust_score.tenant_id,
                outcome=DecisionOutcome.AUTO_APPROVED,
                reason=f"Confidence {trust_score.composite_confidence:.2f} >= {auto_threshold}",
            )

        # ── Rule 4: Medium confidence → Human review ──
        if trust_score.composite_confidence >= review_threshold:
            return DecisionResult(
                doc_id=trust_score.doc_id,
                tenant_id=trust_score.tenant_id,
                outcome=DecisionOutcome.HUMAN_REVIEW,
                reason=f"Confidence {trust_score.composite_confidence:.2f} "
                f"below auto-approve ({auto_threshold}) "
                f"but above review ({review_threshold})",
                review_priority=self._compute_priority(trust_score),
            )

        # ── Rule 5: Very low confidence → Reprocess ──
        # Try OCR again with a different strategy before sending to human
        reprocess_stage = self._select_reprocess_stage(trust_score, extraction)

        return DecisionResult(
            doc_id=trust_score.doc_id,
            tenant_id=trust_score.tenant_id,
            outcome=DecisionOutcome.REPROCESS,
            reprocess_target_stage=reprocess_stage,
            reason=f"Very low confidence {trust_score.composite_confidence:.2f} "
            f"< {review_threshold}, attempting reprocess at {reprocess_stage.value}",
            review_priority=self._compute_priority(trust_score),
        )

    def _compute_priority(self, trust_score: TrustScore) -> float:
        """
        Compute review queue priority (0-1, higher = more urgent).

        Factors:
          - Business impact (critical > high > medium > low)
          - Anomaly score
          - Number of error flags
          - Inverse of confidence (lower confidence = higher priority)
        """
        impact_weights = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
        impact = impact_weights.get(trust_score.business_impact, 0.3)

        priority = (
            0.3 * impact
            + 0.2 * trust_score.anomaly_score
            + 0.2 * min(1.0, trust_score.error_count * 0.2)
            + 0.3 * (1.0 - trust_score.composite_confidence)
        )

        return max(0.0, min(1.0, priority))

    def _select_reprocess_stage(
        self,
        trust_score: TrustScore,
        extraction: ExtractionOutput,
    ) -> JobState:
        """
        Determine which pipeline stage to reprocess.

        Heuristic:
          - Many low-confidence fields → re-run OCR (maybe with different settings)
          - Missing fields → re-run extraction
          - Arithmetic errors → re-run normalization
        """
        flag_types = {f.flag_type for f in trust_score.validation_flags}

        if "missing_field" in flag_types:
            return JobState.OCR_EXTRACTION  # Re-OCR might catch missed regions
        if "arithmetic_error" in flag_types:
            return JobState.NORMALIZING  # Re-normalize might fix parsing
        if "low_confidence" in flag_types:
            return JobState.OCR_EXTRACTION  # Re-OCR with enhanced settings

        # Default: re-run pre-processing with more aggressive enhancement
        return JobState.PREPROCESSING
