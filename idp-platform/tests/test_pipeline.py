"""
Integration tests for the IDP pipeline.

Tests the core pipeline flow from ingestion through decision, verifying:
  - Job state machine transitions
  - Unlimited-OCR output parsing (<|det|> tags)
  - Normalization (dates, currencies, KV pairs)
  - 3-layer extraction (rules & templates)
  - Validation & trust scoring
  - Decision engine routing

These tests run without a GPU — they test the pipeline logic, schema parsing,
and state machine, not the actual OCR model inference.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from libs.common.job_states import (
    JobState,
    InvalidTransitionError,
    TERMINAL_STATES,
    validate_transition,
)
from libs.common.schemas import (
    ContentType,
    DecisionOutcome,
    DocumentJob,
    DocumentProfile,
    ExtractionLayer,
    ExtractionOutput,
    ExtractionResult,
    ExtractedField,
    NormalizedOutput,
    OCREngine,
    PageExtractionResult,
    PageProfile,
    Region,
    TenantConfig,
    TrustScore,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Test: Job State Machine
# ═══════════════════════════════════════════════════════════════════════════════


def test_state_machine_happy_path():
    """Test the full happy-path state machine sequence."""
    job = DocumentJob(tenant_id="test-tenant")
    assert job.state == JobState.UPLOADED

    job.transition_to(JobState.SECURITY_CHECK, "Starting checks")
    assert job.state == JobState.SECURITY_CHECK

    job.transition_to(JobState.PROFILING, "Security passed")
    assert job.state == JobState.PROFILING

    job.transition_to(JobState.PREPROCESSING, "Profile done")
    assert job.state == JobState.PREPROCESSING

    job.transition_to(JobState.OCR_EXTRACTION, "Preprocessed")
    assert job.state == JobState.OCR_EXTRACTION

    job.transition_to(JobState.NORMALIZING, "OCR done")
    assert job.state == JobState.NORMALIZING

    job.transition_to(JobState.VALIDATING, "Normalized")
    assert job.state == JobState.VALIDATING

    job.transition_to(JobState.DECISION, "Validated")
    assert job.state == JobState.DECISION

    job.transition_to(JobState.DELIVERY_PENDING, "Auto-approved")
    assert job.state == JobState.DELIVERY_PENDING

    job.transition_to(JobState.COMPLETED, "Delivered")
    assert job.state == JobState.COMPLETED
    assert job.completed_at is not None

    # Verify history
    assert len(job.state_history) == 9
    print("✅ State machine happy path: PASSED")


def test_state_machine_security_rejection():
    """Test security rejection path."""
    job = DocumentJob(tenant_id="test-tenant")
    job.transition_to(JobState.SECURITY_CHECK)
    job.transition_to(JobState.SECURITY_REJECTED, "Malware detected")
    assert job.state == JobState.SECURITY_REJECTED
    assert job.state in TERMINAL_STATES
    print("✅ Security rejection path: PASSED")


def test_state_machine_invalid_transition():
    """Test that invalid transitions raise errors."""
    job = DocumentJob(tenant_id="test-tenant")
    try:
        job.transition_to(JobState.COMPLETED)  # Can't go directly to COMPLETED
        assert False, "Should have raised InvalidTransitionError"
    except InvalidTransitionError as e:
        assert e.current == JobState.UPLOADED
        assert e.target == JobState.COMPLETED
    print("✅ Invalid transition detection: PASSED")


def test_state_machine_review_path():
    """Test the human review path."""
    job = DocumentJob(tenant_id="test-tenant")
    job.transition_to(JobState.SECURITY_CHECK)
    job.transition_to(JobState.PROFILING)
    job.transition_to(JobState.PREPROCESSING)
    job.transition_to(JobState.OCR_EXTRACTION)
    job.transition_to(JobState.NORMALIZING)
    job.transition_to(JobState.VALIDATING)
    job.transition_to(JobState.DECISION)
    job.transition_to(JobState.REVIEW_REQUIRED, "Low confidence")
    job.transition_to(JobState.REVIEW_PENDING)
    job.transition_to(JobState.DELIVERY_PENDING, "Reviewer approved")
    job.transition_to(JobState.COMPLETED)
    assert job.state == JobState.COMPLETED
    print("✅ Human review path: PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Unlimited-OCR Output Parsing
# ═══════════════════════════════════════════════════════════════════════════════


def test_det_tag_parsing():
    """Test parsing of Unlimited-OCR's <|det|> annotated output."""
    from services.ocr_engine.adapters.unlimited_ocr import parse_det_output, extract_plain_text

    raw_output = """<|det|>title [10,20,300,50]<|/det|>Invoice #INV-2024-001
<|det|>text [10,60,300,100]<|/det|>Date: January 15, 2024
<|det|>text [10,110,300,150]<|/det|>From: Acme Corporation
<|det|>table [10,160,600,400]<|/det|>| Item | Qty | Price |
| Widget A | 10 | $50.00 |
| Widget B | 5 | $30.00 |
<|det|>text [10,410,300,440]<|/det|>Subtotal: $650.00
<|det|>text [10,450,300,480]<|/det|>Tax: $58.50
<|det|>text [10,490,300,520]<|/det|>Total: $708.50
<|det|>image [400,10,600,200]<|/det|>company logo
<|det|>signature [10,540,200,600]<|/det|>John Doe"""

    regions = parse_det_output(raw_output)
    assert len(regions) == 8  # 9 det tags minus 1 image = 8
    assert regions[0].content_type == ContentType.HEADER  # title -> header
    assert regions[0].content == "Invoice #INV-2024-001"
    assert regions[0].bbox is not None
    assert regions[0].bbox.x == 10
    assert regions[3].content_type == ContentType.TABLE

    # Check plain text extraction
    plain = extract_plain_text(raw_output)
    assert "Invoice #INV-2024-001" in plain
    assert "Total: $708.50" in plain
    assert "company logo" not in plain  # Image regions stripped

    print("✅ <|det|> tag parsing: PASSED")


def test_det_tag_no_bbox():
    """Test parsing when bounding boxes are absent."""
    from services.ocr_engine.adapters.unlimited_ocr import parse_det_output

    raw_output = """<|det|>text<|/det|>Hello world
<|det|>table<|/det|>| A | B |"""

    regions = parse_det_output(raw_output)
    assert len(regions) == 2
    assert regions[0].bbox is None
    assert regions[0].content == "Hello world"
    print("✅ <|det|> parsing without bbox: PASSED")


def test_confidence_estimation():
    """Test confidence estimation heuristics."""
    from services.ocr_engine.adapters.unlimited_ocr import estimate_confidence

    # Good output (varied content with det tags)
    lines = [f"<|det|>text<|/det|>Line {i} with unique content about topic {i*7}" for i in range(20)]
    good = "\n".join(lines)
    conf = estimate_confidence(good, 200)
    assert conf > 0.5, f"Expected >0.5, got {conf}"

    # Empty output
    assert estimate_confidence("", 0) == 0.0

    # Very short output
    conf_short = estimate_confidence("x", 1)
    assert conf_short < 0.7, f"Expected <0.7 for short output, got {conf_short}"

    print("✅ Confidence estimation: PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Normalization
# ═══════════════════════════════════════════════════════════════════════════════


def test_date_normalization():
    """Test date parsing across multiple formats."""
    from services.normalizer.service import normalize_date

    assert normalize_date("01/15/2024") == "2024-01-15"
    assert normalize_date("15.01.2024") == "2024-01-15"
    assert normalize_date("2024-01-15") == "2024-01-15"
    assert normalize_date("2024年1月15日") == "2024-01-15"
    assert normalize_date("January 15, 2024") == "2024-01-15"
    assert normalize_date("Jan 15 2024") == "2024-01-15"
    assert normalize_date("no date here") is None
    print("✅ Date normalization: PASSED")


def test_currency_normalization():
    """Test currency amount parsing."""
    from services.normalizer.service import normalize_currency

    result = normalize_currency("$1,234.56")
    assert result is not None
    assert result["amount"] == 1234.56
    assert result["currency"] == "USD"

    result = normalize_currency("€99.99")
    assert result is not None
    assert result["amount"] == 99.99
    assert result["currency"] == "EUR"

    result = normalize_currency("¥10000")
    assert result is not None
    assert result["amount"] == 10000.0

    assert normalize_currency("no amount") is None
    print("✅ Currency normalization: PASSED")


def test_kv_extraction():
    """Test key-value pair extraction from text."""
    from services.normalizer.service import extract_key_value_pairs

    text = """Invoice Number: INV-2024-001
Date: 01/15/2024
Total Amount: $1,234.56
Customer: Acme Corp"""

    fields = extract_key_value_pairs(text)
    assert len(fields) >= 3
    names = {f.key for f in fields}
    assert "invoice_number" in names
    assert "total_amount" in names

    # Check that date was normalized
    date_field = next(f for f in fields if f.key == "date")
    assert date_field.field_type == "date"
    assert date_field.normalized_value == "2024-01-15"

    print("✅ Key-value extraction: PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Information Extraction (Rules Engine)
# ═══════════════════════════════════════════════════════════════════════════════


def test_invoice_rules_extraction():
    """Test Layer 1 (rules & templates) on invoice text."""
    from services.extractor.service import RulesEngine

    engine = RulesEngine()
    text = """INVOICE

Invoice Number: INV-2024-001
Invoice Date: 01/15/2024
Due Date: 02/15/2024

Bill From: Acme Corporation
Bill To: Wayne Enterprises

Item          Qty    Price
Widget A       10    $500.00
Widget B        5    $150.00

Subtotal: $650.00
Tax: $58.50
Total: $708.50"""

    result = engine.extract(text, doc_type="invoice")
    assert result.doc_type == "invoice"
    assert len(result.fields) >= 3  # At minimum: invoice_number, total
    assert result.overall_confidence > 0.5

    field_names = {f.field_name for f in result.fields}
    assert "invoice_number" in field_names
    assert "total_amount" in field_names

    # Check invoice number value
    inv_field = next(f for f in result.fields if f.field_name == "invoice_number")
    assert "INV-2024-001" in str(inv_field.value)

    print("✅ Invoice rules extraction: PASSED")


def test_extraction_escalation():
    """Test that unknown templates trigger escalation."""
    from services.extractor.service import RulesEngine

    engine = RulesEngine()
    result = engine.extract("Random text with no recognizable fields")
    assert result.overall_confidence == 0.0 or len(result.fields) == 0
    print("✅ Extraction escalation trigger: PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Validation & Trust Scoring
# ═══════════════════════════════════════════════════════════════════════════════


def test_validation_required_fields():
    """Test required field validation for invoices."""
    from services.validator.service import RequiredFieldsRule

    rule = RequiredFieldsRule()

    # Missing required field
    extraction = ExtractionOutput(
        doc_id="test",
        tenant_id="test",
        doc_type="invoice",
        fields=[
            ExtractedField(field_name="vendor_name", value="Acme", confidence=0.9),
        ],
    )
    flags = rule.validate(extraction)
    missing = [f for f in flags if f.flag_type == "missing_field"]
    assert len(missing) >= 1  # invoice_number and total_amount missing
    print("✅ Required field validation: PASSED")


def test_arithmetic_check():
    """Test arithmetic validation (subtotal + tax = total)."""
    from services.validator.service import ArithmeticCheckRule

    rule = ArithmeticCheckRule()

    # Correct arithmetic
    extraction = ExtractionOutput(
        doc_id="test",
        tenant_id="test",
        doc_type="invoice",
        fields=[
            ExtractedField(field_name="subtotal", value="$650.00", confidence=0.9),
            ExtractedField(field_name="tax_amount", value="$58.50", confidence=0.9),
            ExtractedField(field_name="total_amount", value="$708.50", confidence=0.9),
        ],
    )
    flags = rule.validate(extraction)
    assert len(flags) == 0, f"Expected no flags, got {flags}"

    # Wrong arithmetic
    extraction_bad = ExtractionOutput(
        doc_id="test",
        tenant_id="test",
        doc_type="invoice",
        fields=[
            ExtractedField(field_name="subtotal", value="$650.00", confidence=0.9),
            ExtractedField(field_name="tax_amount", value="$58.50", confidence=0.9),
            ExtractedField(field_name="total_amount", value="$999.00", confidence=0.9),
        ],
    )
    flags_bad = rule.validate(extraction_bad)
    assert len(flags_bad) == 1
    assert flags_bad[0].flag_type == "arithmetic_error"

    print("✅ Arithmetic validation: PASSED")


def test_trust_score_computation():
    """Test composite trust score."""
    from services.validator.service import compute_trust_score, ValidationFlag

    extraction = ExtractionOutput(
        doc_id="test",
        tenant_id="test",
        doc_type="invoice",
        fields=[
            ExtractedField(field_name="total", value="$100", confidence=0.9),
        ],
        overall_confidence=0.9,
    )

    # No flags → high confidence
    score_clean = compute_trust_score(extraction, [])
    assert score_clean.composite_confidence == 0.9

    # With error flag → reduced confidence
    flags = [
        ValidationFlag(
            flag_type="arithmetic_error",
            severity="error",
            message="Math doesn't add up",
        )
    ]
    score_flagged = compute_trust_score(extraction, flags)
    assert score_flagged.composite_confidence < 0.9  # Penalized

    print("✅ Trust score computation: PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Decision Engine
# ═══════════════════════════════════════════════════════════════════════════════


def test_decision_auto_approve():
    """Test auto-approval for high-confidence documents."""
    import asyncio
    from services.decision_engine.service import DecisionEngine

    engine = DecisionEngine(default_auto_threshold=0.85)

    extraction = ExtractionOutput(
        doc_id="test",
        tenant_id="test",
        doc_type="invoice",
        overall_confidence=0.92,
    )
    trust = TrustScore(
        doc_id="test",
        tenant_id="test",
        composite_confidence=0.92,
        fraud_risk="low",
    )

    decision = asyncio.run(engine.decide(extraction, trust))
    assert decision.outcome == DecisionOutcome.AUTO_APPROVED
    print("✅ Decision auto-approve: PASSED")


def test_decision_human_review():
    """Test routing to human review for medium confidence."""
    import asyncio
    from services.decision_engine.service import DecisionEngine

    engine = DecisionEngine(default_auto_threshold=0.90, default_review_threshold=0.60)

    extraction = ExtractionOutput(
        doc_id="test",
        tenant_id="test",
        overall_confidence=0.75,
    )
    trust = TrustScore(
        doc_id="test",
        tenant_id="test",
        composite_confidence=0.75,
        fraud_risk="low",
    )

    decision = asyncio.run(engine.decide(extraction, trust))
    assert decision.outcome == DecisionOutcome.HUMAN_REVIEW
    print("✅ Decision human review: PASSED")


def test_decision_fraud_rejection():
    """Test quarantine for high fraud risk."""
    import asyncio
    from services.decision_engine.service import DecisionEngine

    engine = DecisionEngine()

    extraction = ExtractionOutput(doc_id="test", tenant_id="test")
    trust = TrustScore(
        doc_id="test",
        tenant_id="test",
        composite_confidence=0.95,
        fraud_risk="high",
    )

    decision = asyncio.run(engine.decide(extraction, trust))
    assert decision.outcome == DecisionOutcome.QUARANTINED
    print("✅ Decision fraud quarantine: PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Reconciler
# ═══════════════════════════════════════════════════════════════════════════════


def test_deduplication():
    """Test region deduplication."""
    from services.ocr_engine.reconciler import reconcile_document

    result = ExtractionResult(
        doc_id="test",
        tenant_id="test",
        pages=[
            PageExtractionResult(
                page_num=1,
                raw_text="Hello world",
                regions=[
                    Region(
                        content_type=ContentType.PRINTED_TEXT,
                        content="Hello world",
                        confidence=0.9,
                    ),
                    Region(
                        content_type=ContentType.PRINTED_TEXT,
                        content="Hello world",  # Exact duplicate
                        confidence=0.8,
                    ),
                ],
            )
        ],
    )

    reconciled = reconcile_document(result)
    assert len(reconciled.pages[0].regions) == 1
    assert reconciled.pages[0].regions[0].confidence == 0.9  # Kept higher confidence
    print("✅ Region deduplication: PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Ingestion Security
# ═══════════════════════════════════════════════════════════════════════════════


def test_mime_detection():
    """Test MIME type detection from magic bytes."""
    from services.ingestion.service import detect_mime

    assert detect_mime(b"%PDF-1.4") == "application/pdf"
    assert detect_mime(b"\x89PNG\r\n\x1a\n") == "image/png"
    assert detect_mime(b"\xff\xd8\xff\xe0") == "image/jpeg"
    assert detect_mime(b"random bytes") == "application/octet-stream"
    print("✅ MIME detection: PASSED")


def test_idempotency_key():
    """Test idempotency key generation."""
    from services.ingestion.service import generate_idempotency_key

    data = b"test document content"
    key1 = generate_idempotency_key("tenant-1", data)
    key2 = generate_idempotency_key("tenant-1", data)
    key3 = generate_idempotency_key("tenant-2", data)

    assert key1 == key2  # Same tenant + content = same key
    assert key1 != key3  # Different tenant = different key
    print("✅ Idempotency key generation: PASSED")


def test_zip_bomb_detection():
    """Test zip bomb protection."""
    from services.ingestion.service import check_zip_bomb

    safe, msg = check_zip_bomb(b"not a zip")
    assert safe
    print("✅ Zip bomb detection: PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Delivery
# ═══════════════════════════════════════════════════════════════════════════════


def test_webhook_signing():
    """Test HMAC signature generation and verification."""
    from services.delivery.service import sign_payload, verify_signature

    payload = '{"doc_id":"test","amount":100}'
    secret = "my-webhook-secret"

    signature = sign_payload(payload, secret)
    assert len(signature) == 64  # SHA-256 hex

    assert verify_signature(payload, signature, secret)
    assert not verify_signature(payload, signature, "wrong-secret")
    assert not verify_signature("tampered payload", signature, secret)
    print("✅ Webhook signing: PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Run All Tests
# ═══════════════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("IDP Platform — Integration Tests")
    print("=" * 60 + "\n")

    # State Machine
    test_state_machine_happy_path()
    test_state_machine_security_rejection()
    test_state_machine_invalid_transition()
    test_state_machine_review_path()

    # OCR Output Parsing
    test_det_tag_parsing()
    test_det_tag_no_bbox()
    test_confidence_estimation()

    # Normalization
    test_date_normalization()
    test_currency_normalization()
    test_kv_extraction()

    # Information Extraction
    test_invoice_rules_extraction()
    test_extraction_escalation()

    # Validation
    test_validation_required_fields()
    test_arithmetic_check()
    test_trust_score_computation()

    # Decision Engine
    test_decision_auto_approve()
    test_decision_human_review()
    test_decision_fraud_rejection()

    # Reconciler
    test_deduplication()

    # Ingestion Security
    test_mime_detection()
    test_idempotency_key()
    test_zip_bomb_detection()

    # Delivery
    test_webhook_signing()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60 + "\n")
