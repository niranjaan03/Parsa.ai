"""
Job State Machine — States, transitions, and terminal conditions.

Implements the full lifecycle:
  Uploaded → Security Check → Profiling → Pre-processing → OCR/Extraction
  → Normalizing → Validating → Decision → Review/Delivery → Completed

Terminal/error states:
  Security Rejected, Awaiting Password, Unsupported Format,
  Delivery Failed, Cancelled, Expired
"""

from __future__ import annotations

from enum import StrEnum, unique


@unique
class JobState(StrEnum):
    """Every state a document job can occupy."""

    # ── Happy path ──────────────────────────────────────────────
    UPLOADED = "uploaded"
    SECURITY_CHECK = "security_check"
    PROFILING = "profiling"
    PREPROCESSING = "preprocessing"
    OCR_EXTRACTION = "ocr_extraction"
    NORMALIZING = "normalizing"
    VALIDATING = "validating"
    DECISION = "decision"
    REVIEW_REQUIRED = "review_required"
    REVIEW_PENDING = "review_pending"
    DELIVERY_PENDING = "delivery_pending"
    COMPLETED = "completed"

    # ── Terminal / error states ─────────────────────────────────
    SECURITY_REJECTED = "security_rejected"
    AWAITING_PASSWORD = "awaiting_password"
    UNSUPPORTED_FORMAT = "unsupported_format"
    DELIVERY_FAILED = "delivery_failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    ERROR = "error"


# Valid transitions: { current_state: [allowed_next_states] }
TRANSITIONS: dict[JobState, list[JobState]] = {
    JobState.UPLOADED: [JobState.SECURITY_CHECK],
    JobState.SECURITY_CHECK: [
        JobState.PROFILING,
        JobState.SECURITY_REJECTED,
        JobState.AWAITING_PASSWORD,
        JobState.UNSUPPORTED_FORMAT,
    ],
    JobState.PROFILING: [JobState.PREPROCESSING, JobState.ERROR],
    JobState.PREPROCESSING: [JobState.OCR_EXTRACTION, JobState.ERROR],
    JobState.OCR_EXTRACTION: [JobState.NORMALIZING, JobState.ERROR],
    JobState.NORMALIZING: [JobState.VALIDATING, JobState.ERROR],
    JobState.VALIDATING: [JobState.DECISION, JobState.ERROR],
    JobState.DECISION: [
        JobState.DELIVERY_PENDING,
        JobState.REVIEW_REQUIRED,
        # Reprocess loops back to a specific stage:
        JobState.PREPROCESSING,
        JobState.OCR_EXTRACTION,
        JobState.NORMALIZING,
        JobState.ERROR,
    ],
    JobState.REVIEW_REQUIRED: [JobState.REVIEW_PENDING, JobState.CANCELLED],
    JobState.REVIEW_PENDING: [
        JobState.DELIVERY_PENDING,
        # Reviewer sends back for reprocessing:
        JobState.PREPROCESSING,
        JobState.OCR_EXTRACTION,
        JobState.CANCELLED,
    ],
    JobState.DELIVERY_PENDING: [JobState.COMPLETED, JobState.DELIVERY_FAILED],
    # Terminal states have no outgoing transitions
    JobState.COMPLETED: [],
    JobState.SECURITY_REJECTED: [],
    JobState.AWAITING_PASSWORD: [JobState.SECURITY_CHECK],  # retry after password
    JobState.UNSUPPORTED_FORMAT: [],
    JobState.DELIVERY_FAILED: [JobState.DELIVERY_PENDING],  # retry delivery
    JobState.CANCELLED: [],
    JobState.EXPIRED: [],
    JobState.ERROR: [
        # Any prior stage can be retried from error
        JobState.SECURITY_CHECK,
        JobState.PROFILING,
        JobState.PREPROCESSING,
        JobState.OCR_EXTRACTION,
        JobState.NORMALIZING,
        JobState.VALIDATING,
        JobState.CANCELLED,
    ],
}

TERMINAL_STATES: frozenset[JobState] = frozenset(
    {
        JobState.COMPLETED,
        JobState.SECURITY_REJECTED,
        JobState.UNSUPPORTED_FORMAT,
        JobState.CANCELLED,
        JobState.EXPIRED,
    }
)

# Stages that correspond to pipeline processing steps (for reprocessing engine)
PIPELINE_STAGES: list[JobState] = [
    JobState.SECURITY_CHECK,
    JobState.PROFILING,
    JobState.PREPROCESSING,
    JobState.OCR_EXTRACTION,
    JobState.NORMALIZING,
    JobState.VALIDATING,
    JobState.DECISION,
]


class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed."""

    def __init__(self, current: JobState, target: JobState) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Invalid transition: {current.value} → {target.value}. "
            f"Allowed: {[s.value for s in TRANSITIONS.get(current, [])]}"
        )


def validate_transition(current: JobState, target: JobState) -> None:
    """Raise InvalidTransitionError if the transition is not allowed."""
    allowed = TRANSITIONS.get(current, [])
    if target not in allowed:
        raise InvalidTransitionError(current, target)
