"""
Core data models for the IDP pipeline.

Every service reads and writes these schemas. They form the contract between
pipeline stages, ensuring each stage produces typed, versioned artifacts that
downstream stages can consume without coupling to implementation details.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from enum import StrEnum, unique
from typing import Any

from pydantic import BaseModel, Field, computed_field

from .job_states import JobState


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════


@unique
class InputSource(StrEnum):
    WEB_UPLOAD = "web_upload"
    MOBILE_UPLOAD = "mobile_upload"
    SFTP = "sftp"
    API = "api"
    EMAIL = "email"
    CLOUD_STORAGE = "cloud_storage"
    SCANNER = "scanner"
    WEBHOOK = "webhook"


@unique
class SecurityStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    REJECTED = "rejected"
    AWAITING_PASSWORD = "awaiting_password"


@unique
class ContentType(StrEnum):
    """Detected content type within a page region."""
    PRINTED_TEXT = "printed_text"
    HANDWRITING = "handwriting"
    TABLE = "table"
    FORM = "form"
    CHECKBOX = "checkbox"
    BARCODE = "barcode"
    QR_CODE = "qr_code"
    SIGNATURE = "signature"
    STAMP = "stamp"
    IMAGE = "image"
    HEADER = "header"
    FOOTER = "footer"
    PARAGRAPH = "paragraph"


@unique
class OCREngine(StrEnum):
    """Available OCR / extraction engines."""
    UNLIMITED_OCR = "unlimited_ocr"
    NATIVE_PDF = "native_pdf"
    TESSERACT = "tesseract"
    TEXTRACT = "textract"
    AZURE_DOC_INTEL = "azure_doc_intel"


@unique
class ExtractionLayer(StrEnum):
    RULES_TEMPLATES = "rules_templates"
    SMALL_MODEL = "small_model"
    LLM_ESCALATION = "llm_escalation"


@unique
class DecisionOutcome(StrEnum):
    AUTO_APPROVED = "auto_approved"
    REPROCESS = "reprocess"
    HUMAN_REVIEW = "human_review"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"


# ═══════════════════════════════════════════════════════════════════════════════
# Geometry / Regions
# ═══════════════════════════════════════════════════════════════════════════════


class BoundingBox(BaseModel):
    """Axis-aligned bounding box in pixel coordinates."""
    x: float = Field(ge=0, description="Left edge x")
    y: float = Field(ge=0, description="Top edge y")
    width: float = Field(gt=0)
    height: float = Field(gt=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def x2(self) -> float:
        return self.x + self.width

    @computed_field  # type: ignore[prop-decorator]
    @property
    def y2(self) -> float:
        return self.y + self.height


class Region(BaseModel):
    """A detected region within a page (output of OCR / layout analysis)."""
    region_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    content_type: ContentType
    bbox: BoundingBox | None = None
    content: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reading_order: int = Field(default=0, description="Order in reading flow")
    metadata: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Document Profile (output of Stage 2)
# ═══════════════════════════════════════════════════════════════════════════════


class PageProfile(BaseModel):
    """Per-page analysis from the profiler."""
    page_num: int = Field(ge=1)
    width_px: int = 0
    height_px: int = 0
    is_native_text: bool = False
    quality_score: float = Field(ge=0.0, le=1.0, default=0.5)
    detected_languages: list[str] = Field(default_factory=list)
    regions: list[Region] = Field(default_factory=list)
    preprocessing_strategy: str = "default"


class DocumentProfile(BaseModel):
    """Complete document analysis (output of Stage 2: Profiling)."""
    doc_id: str
    tenant_id: str
    is_native_text: bool = False
    primary_language: str = "en"
    detected_languages: list[str] = Field(default_factory=list)
    overall_quality_score: float = Field(ge=0.0, le=1.0, default=0.5)
    page_count: int = Field(ge=1, default=1)
    doc_type_prediction: str = "unknown"
    doc_type_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    pages: list[PageProfile] = Field(default_factory=list)
    preprocessing_strategy: str = "default"
    metadata: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Extraction Results (output of Stage 4: OCR)
# ═══════════════════════════════════════════════════════════════════════════════


class PageExtractionResult(BaseModel):
    """OCR / extraction result for a single page."""
    page_num: int = Field(ge=1)
    raw_text: str = ""
    regions: list[Region] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    engine: OCREngine = OCREngine.UNLIMITED_OCR
    latency_ms: int = 0
    token_count: int = 0
    raw_engine_output: str = ""


class ExtractionResult(BaseModel):
    """Combined extraction result for an entire document."""
    doc_id: str
    tenant_id: str
    pages: list[PageExtractionResult] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    primary_engine: OCREngine = OCREngine.UNLIMITED_OCR
    total_latency_ms: int = 0
    total_tokens: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_text(self) -> str:
        """Concatenated text from all pages."""
        return "\n\n".join(p.raw_text for p in self.pages if p.raw_text)


# ═══════════════════════════════════════════════════════════════════════════════
# Normalized Output (output of Stage 5: Normalization)
# ═══════════════════════════════════════════════════════════════════════════════


class NormalizedField(BaseModel):
    """A single normalized key-value field."""
    key: str
    raw_value: str
    normalized_value: str
    field_type: str = "string"  # string, date, currency, number, entity
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    source_region_id: str | None = None
    source_page: int | None = None


class NormalizedOutput(BaseModel):
    """Output of Stage 5: Normalization."""
    doc_id: str
    tenant_id: str
    fields: list[NormalizedField] = Field(default_factory=list)
    normalized_text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Extracted Fields (output of Stage 6: Information Extraction)
# ═══════════════════════════════════════════════════════════════════════════════


class ExtractedField(BaseModel):
    """A structured field extracted from the document."""
    field_name: str
    value: Any
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    extraction_layer: ExtractionLayer = ExtractionLayer.RULES_TEMPLATES
    source_span: str | None = None  # Reference to source text
    source_page: int | None = None
    source_region_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SemanticSegmentMember(BaseModel):
    """A member chunk/span contributing to a semantic segment."""
    page_no: int = Field(ge=1, default=1)
    bbox: list[float] = Field(default_factory=list, description="[x0, y0, x1, y1] or [x, y, w, h]")
    source_index: int = Field(default=0, description="Index in parent chunk list")
    text: str = ""


class SemanticSegment(BaseModel):
    """A RAG-ready semantic chunk split at structural boundaries."""
    segment_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    content: str = Field(..., description="Markdown or text representation of segment")
    char_count: int = Field(default=0)
    pages: list[int] = Field(default_factory=list)
    bounding_boxes: list[dict[str, Any]] = Field(default_factory=list)
    members: list[SemanticSegmentMember] = Field(default_factory=list)
    chunk_type: str = "text"  # text, table, figure, mixed


class SemanticChunkingResult(BaseModel):
    """Complete semantic chunking output for RAG systems."""
    segments: list[SemanticSegment] = Field(default_factory=list)
    total_segments: int = Field(default=0)
    chunk_size_target: int = Field(default=1000)
    page_dimensions: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractionOutput(BaseModel):
    """Output of Stage 6: Information Extraction."""
    doc_id: str
    tenant_id: str
    doc_type: str = "unknown"
    fields: list[ExtractedField] = Field(default_factory=list)
    extraction_layer_used: ExtractionLayer = ExtractionLayer.RULES_TEMPLATES
    overall_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    escalation_reason: str | None = None
    semantic_chunking: SemanticChunkingResult | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Trust Score (output of Stage 7: Validation)
# ═══════════════════════════════════════════════════════════════════════════════


class ValidationFlag(BaseModel):
    """A validation issue found during Stage 7."""
    flag_type: str  # "missing_field", "type_error", "cross_field_mismatch", "arithmetic_error", "fraud_signal"
    severity: str = "warning"  # "info", "warning", "error", "critical"
    field_name: str | None = None
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class TrustScore(BaseModel):
    """Composite trust score — output of Stage 7: Validation."""
    doc_id: str
    tenant_id: str
    composite_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    field_scores: dict[str, float] = Field(default_factory=dict)
    validation_flags: list[ValidationFlag] = Field(default_factory=list)
    fraud_risk: str = "unknown"  # low, medium, high
    anomaly_score: float = Field(ge=0.0, le=1.0, default=0.0)
    business_impact: str = "unknown"  # low, medium, high, critical
    compliance_risk: str = "none"  # none, low, medium, high
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_critical_flags(self) -> bool:
        return any(f.severity == "critical" for f in self.validation_flags)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def error_count(self) -> int:
        return sum(1 for f in self.validation_flags if f.severity in ("error", "critical"))


# ═══════════════════════════════════════════════════════════════════════════════
# Decision (output of Stage 8)
# ═══════════════════════════════════════════════════════════════════════════════


class DecisionResult(BaseModel):
    """Output of Stage 8: Decision Engine."""
    doc_id: str
    tenant_id: str
    outcome: DecisionOutcome
    reprocess_target_stage: JobState | None = None  # If outcome == REPROCESS
    review_priority: float = Field(ge=0.0, le=1.0, default=0.5)
    reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Delivery (output of Stage 9)
# ═══════════════════════════════════════════════════════════════════════════════


class DeliveryPayload(BaseModel):
    """Versioned, signed payload for output delivery."""
    doc_id: str
    tenant_id: str
    schema_version: str = "1.0.0"
    delivery_key: str = Field(default_factory=lambda: uuid.uuid4().hex)
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    trust_score: TrustScore | None = None
    decision: DecisionOutcome = DecisionOutcome.AUTO_APPROVED
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signature: str = ""  # HMAC signature

    def compute_signature(self, secret: str) -> str:
        """Compute HMAC-SHA256 signature over the payload."""
        payload_str = self.model_dump_json(exclude={"signature"})
        return hashlib.sha256(f"{payload_str}{secret}".encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# Job / Document Record (top-level entity)
# ═══════════════════════════════════════════════════════════════════════════════


class DocumentJob(BaseModel):
    """
    Top-level record tracking a document through the entire pipeline.

    This is the persistent entity stored in the metadata store.
    Each stage writes its artifact and updates this record with the new state.
    """
    job_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    doc_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    tenant_id: str
    state: JobState = JobState.UPLOADED
    idempotency_key: str = ""
    source: InputSource = InputSource.API
    content_type: str = ""  # MIME type
    original_filename: str = ""
    page_count: int = 0
    file_size_bytes: int = 0

    # Storage references (paths/URIs to stage artifacts)
    raw_storage_uri: str = ""
    preprocessed_uri: str = ""
    ocr_result_uri: str = ""
    normalized_uri: str = ""
    extracted_uri: str = ""
    validated_uri: str = ""
    delivery_uri: str = ""

    # Semantic RAG Chunking configuration & result
    chunking_requested: str | None = None  # "semantic" or None
    chunk_size_target: int = 1000
    semantic_chunking: SemanticChunkingResult | None = None

    # Pipeline results (denormalized for quick access)
    profile: DocumentProfile | None = None
    extraction_result: ExtractionResult | None = None
    normalized_output: NormalizedOutput | None = None
    extraction_output: ExtractionOutput | None = None
    trust_score: TrustScore | None = None
    decision: DecisionResult | None = None

    # Tracking
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    error_message: str | None = None
    retry_count: int = 0
    state_history: list[dict[str, Any]] = Field(default_factory=list)

    def transition_to(self, new_state: JobState, reason: str = "") -> None:
        """Transition to a new state, recording history."""
        from .job_states import validate_transition

        validate_transition(self.state, new_state)
        self.state_history.append(
            {
                "from": self.state.value,
                "to": new_state.value,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.state = new_state
        self.updated_at = datetime.now(timezone.utc)
        if new_state == JobState.COMPLETED:
            self.completed_at = self.updated_at


# ═══════════════════════════════════════════════════════════════════════════════
# Tenant Configuration
# ═══════════════════════════════════════════════════════════════════════════════


class TenantLimits(BaseModel):
    """Per-tenant resource limits."""
    max_pages_per_document: int = 500
    max_concurrent_jobs: int = 50
    max_file_size_mb: int = 100
    max_documents_per_day: int = 10000
    gpu_priority: str = "normal"  # low, normal, high


class TenantFeatures(BaseModel):
    """Feature flags per tenant."""
    ocr_engine: OCREngine = OCREngine.UNLIMITED_OCR
    llm_escalation_enabled: bool = True
    human_review_enabled: bool = True
    fraud_detection_enabled: bool = True
    pii_redaction_enabled: bool = False
    custom_templates: list[str] = Field(default_factory=list)


class TenantStorage(BaseModel):
    """Storage configuration per tenant."""
    bucket: str = ""
    region: str = "us-east-1"
    encryption_key_id: str = ""
    retention_days: int = 365


class TenantConfig(BaseModel):
    """Complete tenant configuration."""
    tenant_id: str
    name: str
    is_active: bool = True
    limits: TenantLimits = Field(default_factory=TenantLimits)
    features: TenantFeatures = Field(default_factory=TenantFeatures)
    storage: TenantStorage = Field(default_factory=TenantStorage)
    auto_approve_threshold: float = Field(ge=0.0, le=1.0, default=0.95)
    ml_approve_threshold: float = Field(ge=0.0, le=1.0, default=0.85)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Model Registry Entry
# ═══════════════════════════════════════════════════════════════════════════════


class ModelRegistryEntry(BaseModel):
    """Registry entry for an OCR/ML model or LLM."""
    model_id: str
    engine: OCREngine
    version: str
    architecture: str = ""
    deployment_backend: str = ""  # "sglang", "vllm", "transformers", "api"
    capabilities: list[str] = Field(default_factory=list)
    cost_model: str = "gpu_time"  # "gpu_time", "per_call", "per_token"
    gpu_requirements: dict[str, Any] = Field(default_factory=dict)
    inference_config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    is_canary: bool = False
    traffic_percentage: float = Field(ge=0.0, le=1.0, default=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)
