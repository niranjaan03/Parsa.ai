"""
Comprehensive JSON Conversion Benchmark Suite for IDP Platform.

Tests 36 distinct data types (20 schemas, 6 MIME file formats, 10 document domain types)
with 20 test files/instances per data type (720 total tests).
Measures win rate, pass/fail counts, success rates, and reports root causes for failures.
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from libs.common.job_states import JobState
from libs.common.schemas import (
    BoundingBox,
    ContentType,
    DecisionOutcome,
    DecisionResult,
    DeliveryPayload,
    DocumentJob,
    DocumentProfile,
    ExtractedField,
    ExtractionLayer,
    ExtractionOutput,
    ExtractionResult,
    ModelRegistryEntry,
    NormalizedField,
    NormalizedOutput,
    OCREngine,
    PageExtractionResult,
    PageProfile,
    Region,
    SecurityStatus,
    TenantConfig,
    TenantFeatures,
    TenantLimits,
    TenantStorage,
    TrustScore,
    ValidationFlag,
)
from services.ingestion.service import IngestionService, SecurityCheckResult
from services.normalizer.service import NormalizationService
from services.extractor.service import ExtractionService, RulesEngine, DocumentTemplate


# Helper to generate mock image bytes for various formats
def create_mock_file_bytes(mime_type: str, file_index: int) -> bytes:
    """Create valid binary stream matching magic headers for given mime type."""
    if mime_type == "application/pdf":
        return f"%PDF-1.5\n%{file_index}\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 1\n0000000000 65535 f\ntrailer\n<< /Root 1 0 R >>\nstartxref\n9\n%%EOF".encode("utf-8")
    elif mime_type == "image/png":
        # PNG signature + simple chunk data
        return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4" + bytes([file_index])
    elif mime_type == "image/jpeg":
        # JPEG SOI marker + APP0 marker
        return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + bytes([file_index])
    elif mime_type == "image/tiff":
        # TIFF little endian magic header
        return b"II*\x00\x08\x00\x00\x00" + bytes([file_index]) * 10
    elif mime_type == "image/bmp":
        # BMP magic header 'BM'
        return b"BM\x36\x00\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00" + bytes([file_index]) * 10
    elif mime_type == "image/webp":
        # RIFF ... WEBP header
        return b"RIFF\x1a\x00\x00\x00WEBPVP8 " + bytes([file_index]) * 10
    else:
        return f"generic_data_{file_index}".encode("utf-8")


class DatatypeJSONTester:
    def __init__(self, num_samples: int = 20) -> None:
        self.num_samples = num_samples
        self.results: Dict[str, Dict[str, Any]] = {}
        self.ingestion_service = IngestionService()
        self.normalizer_service = NormalizationService()
        self.extraction_service = ExtractionService()
        self.tenant_config = TenantConfig(tenant_id="test_tenant", name="Test Tenant")

    def record_result(self, datatype_category: str, datatype_name: str, passed: bool, error_msg: str | None = None) -> None:
        key = f"[{datatype_category}] {datatype_name}"
        if key not in self.results:
            self.results[key] = {"category": datatype_category, "name": datatype_name, "total": 0, "passed": 0, "failed": 0, "errors": []}
        self.results[key]["total"] += 1
        if passed:
            self.results[key]["passed"] += 1
        else:
            self.results[key]["failed"] += 1
            if error_msg:
                self.results[key]["errors"].append(error_msg)

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORY A: 20 Core Pydantic Data Models (JSON Serialization & Round-Trip)
    # ══════════════════════════════════════════════════════════════════════════

    def test_pydantic_schemas(self) -> None:
        print("Testing Category A: Pydantic Data Schemas (JSON round-trip)...")

        # 1. BoundingBox
        for i in range(self.num_samples):
            try:
                obj = BoundingBox(x=10.0 * i, y=5.0 * i, width=100.0 + i, height=50.0 + i)
                json_str = obj.model_dump_json()
                parsed = json.loads(json_str)
                restored = BoundingBox.model_validate_json(json_str)
                assert restored.x == obj.x and restored.width == obj.width and "x2" in parsed
                self.record_result("Pydantic Schema", "BoundingBox", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "BoundingBox", False, str(e))

        # 2. Region
        for i in range(self.num_samples):
            try:
                obj = Region(
                    region_id=f"reg_{i}",
                    content_type=ContentType.PRINTED_TEXT if i % 2 == 0 else ContentType.TABLE,
                    bbox=BoundingBox(x=1.0, y=2.0, width=30.0 + i, height=40.0 + i),
                    content=f"Sample text content region {i}",
                    confidence=min(1.0, 0.80 + (i * 0.008)),
                    reading_order=i,
                    metadata={"index": i, "tag": f"tag_{i}"},
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = Region.model_validate_json(json_str)
                assert restored.content == obj.content and restored.content_type == obj.content_type
                self.record_result("Pydantic Schema", "Region", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "Region", False, str(e))

        # 3. PageProfile
        for i in range(self.num_samples):
            try:
                obj = PageProfile(
                    page_num=i + 1,
                    width_px=800 + i * 10,
                    height_px=1100 + i * 10,
                    is_native_text=bool(i % 2 == 0),
                    quality_score=0.9,
                    detected_languages=["en", "es"],
                    regions=[Region(content_type=ContentType.PRINTED_TEXT, content=f"Page {i+1} text")],
                    preprocessing_strategy="default",
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = PageProfile.model_validate_json(json_str)
                assert restored.page_num == obj.page_num and len(restored.regions) == 1
                self.record_result("Pydantic Schema", "PageProfile", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "PageProfile", False, str(e))

        # 4. DocumentProfile
        for i in range(self.num_samples):
            try:
                obj = DocumentProfile(
                    doc_id=f"doc_prof_{i}",
                    tenant_id=f"tenant_{i}",
                    is_native_text=True,
                    primary_language="en",
                    detected_languages=["en"],
                    overall_quality_score=0.95,
                    page_count=i + 1,
                    doc_type_prediction="invoice",
                    doc_type_confidence=0.92,
                    pages=[PageProfile(page_num=p + 1) for p in range(i + 1)],
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = DocumentProfile.model_validate_json(json_str)
                assert restored.doc_id == obj.doc_id and restored.page_count == len(restored.pages)
                self.record_result("Pydantic Schema", "DocumentProfile", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "DocumentProfile", False, str(e))

        # 5. PageExtractionResult
        for i in range(self.num_samples):
            try:
                obj = PageExtractionResult(
                    page_num=i + 1,
                    raw_text=f"Raw text for page {i+1}",
                    regions=[Region(content_type=ContentType.PRINTED_TEXT, content=f"region {i}")],
                    confidence=0.88,
                    engine=OCREngine.UNLIMITED_OCR,
                    latency_ms=120 + i * 5,
                    token_count=50 + i,
                    raw_engine_output=f"<|det|>text<|/det|>Raw text for page {i+1}",
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = PageExtractionResult.model_validate_json(json_str)
                assert restored.page_num == obj.page_num and restored.engine == OCREngine.UNLIMITED_OCR
                self.record_result("Pydantic Schema", "PageExtractionResult", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "PageExtractionResult", False, str(e))

        # 6. ExtractionResult
        for i in range(self.num_samples):
            try:
                pages = [PageExtractionResult(page_num=1, raw_text=f"Text page {i}")]
                obj = ExtractionResult(
                    doc_id=f"ext_res_{i}",
                    tenant_id="tenant_1",
                    pages=pages,
                    overall_confidence=0.91,
                    primary_engine=OCREngine.UNLIMITED_OCR,
                    total_latency_ms=250,
                    total_tokens=100,
                )
                json_str = obj.model_dump_json()
                parsed = json.loads(json_str)
                restored = ExtractionResult.model_validate_json(json_str)
                assert restored.doc_id == obj.doc_id and "full_text" in parsed
                self.record_result("Pydantic Schema", "ExtractionResult", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "ExtractionResult", False, str(e))

        # 7. NormalizedField
        for i in range(self.num_samples):
            try:
                obj = NormalizedField(
                    key=f"field_key_{i}",
                    raw_value=f"$10{i}.00",
                    normalized_value=f"10{i}.00 USD",
                    field_type="currency",
                    confidence=0.9,
                    source_region_id=f"reg_{i}",
                    source_page=1,
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = NormalizedField.model_validate_json(json_str)
                assert restored.key == obj.key and restored.field_type == "currency"
                self.record_result("Pydantic Schema", "NormalizedField", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "NormalizedField", False, str(e))

        # 8. NormalizedOutput
        for i in range(self.num_samples):
            try:
                fields = [NormalizedField(key="total", raw_value="$100", normalized_value="100.00 USD")]
                obj = NormalizedOutput(
                    doc_id=f"norm_out_{i}",
                    tenant_id="tenant_1",
                    fields=fields,
                    normalized_text=f"Invoice total $100 sample {i}",
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = NormalizedOutput.model_validate_json(json_str)
                assert restored.doc_id == obj.doc_id and len(restored.fields) == 1
                self.record_result("Pydantic Schema", "NormalizedOutput", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "NormalizedOutput", False, str(e))

        # 9. ExtractedField
        for i in range(self.num_samples):
            try:
                obj = ExtractedField(
                    field_name=f"inv_no_{i}",
                    value=f"INV-2026-00{i}",
                    confidence=0.95,
                    extraction_layer=ExtractionLayer.RULES_TEMPLATES,
                    source_span=f"Invoice No: INV-2026-00{i}",
                    source_page=1,
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = ExtractedField.model_validate_json(json_str)
                assert restored.field_name == obj.field_name and restored.extraction_layer == ExtractionLayer.RULES_TEMPLATES
                self.record_result("Pydantic Schema", "ExtractedField", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "ExtractedField", False, str(e))

        # 10. ExtractionOutput
        for i in range(self.num_samples):
            try:
                fields = [ExtractedField(field_name="total", value="100.00", confidence=0.99)]
                obj = ExtractionOutput(
                    doc_id=f"extr_out_{i}",
                    tenant_id="tenant_1",
                    doc_type="invoice",
                    fields=fields,
                    extraction_layer_used=ExtractionLayer.RULES_TEMPLATES,
                    overall_confidence=0.99,
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = ExtractionOutput.model_validate_json(json_str)
                assert restored.doc_id == obj.doc_id and restored.doc_type == "invoice"
                self.record_result("Pydantic Schema", "ExtractionOutput", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "ExtractionOutput", False, str(e))

        # 11. ValidationFlag
        for i in range(self.num_samples):
            try:
                obj = ValidationFlag(
                    flag_type="missing_field" if i % 2 == 0 else "arithmetic_error",
                    severity="warning" if i % 2 == 0 else "error",
                    field_name=f"field_{i}",
                    message=f"Validation issue on field {i}",
                    details={"val": i},
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = ValidationFlag.model_validate_json(json_str)
                assert restored.flag_type == obj.flag_type and restored.severity == obj.severity
                self.record_result("Pydantic Schema", "ValidationFlag", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "ValidationFlag", False, str(e))

        # 12. TrustScore
        for i in range(self.num_samples):
            try:
                obj = TrustScore(
                    doc_id=f"trust_{i}",
                    tenant_id="tenant_1",
                    composite_confidence=min(1.0, 0.80 + (i * 0.008)),
                    field_scores={"inv_no": 0.9, "total": 0.8},
                    validation_flags=[ValidationFlag(flag_type="missing_field", severity="warning")],
                    fraud_risk="low",
                    anomaly_score=0.05,
                    business_impact="medium",
                    compliance_risk="none",
                )
                json_str = obj.model_dump_json()
                parsed = json.loads(json_str)
                restored = TrustScore.model_validate_json(json_str)
                assert restored.doc_id == obj.doc_id and "has_critical_flags" in parsed
                self.record_result("Pydantic Schema", "TrustScore", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "TrustScore", False, str(e))

        # 13. DecisionResult
        for i in range(self.num_samples):
            try:
                obj = DecisionResult(
                    doc_id=f"dec_{i}",
                    tenant_id="tenant_1",
                    outcome=DecisionOutcome.AUTO_APPROVED if i % 2 == 0 else DecisionOutcome.HUMAN_REVIEW,
                    review_priority=min(1.0, (i % 10) * 0.1),
                    reason=f"Decision rule {i} triggered",
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = DecisionResult.model_validate_json(json_str)
                assert restored.doc_id == obj.doc_id and restored.outcome == obj.outcome
                self.record_result("Pydantic Schema", "DecisionResult", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "DecisionResult", False, str(e))

        # 14. DeliveryPayload
        for i in range(self.num_samples):
            try:
                trust = TrustScore(doc_id=f"del_trust_{i}", tenant_id="tenant_1", composite_confidence=0.9)
                obj = DeliveryPayload(
                    doc_id=f"del_{i}",
                    tenant_id="tenant_1",
                    schema_version="1.0.0",
                    extracted_data={"invoice_no": f"INV-{i}", "total": 100 + i},
                    trust_score=trust,
                    decision=DecisionOutcome.AUTO_APPROVED,
                )
                obj.signature = obj.compute_signature("secret_key_123")
                json_str = obj.model_dump_json()
                parsed = json.loads(json_str)
                restored = DeliveryPayload.model_validate_json(json_str)
                assert restored.doc_id == obj.doc_id and restored.signature == obj.signature
                self.record_result("Pydantic Schema", "DeliveryPayload", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "DeliveryPayload", False, str(e))

        # 15. DocumentJob
        for i in range(self.num_samples):
            try:
                obj = DocumentJob(
                    job_id=f"job_{i}",
                    doc_id=f"doc_job_{i}",
                    tenant_id="tenant_1",
                    state=JobState.UPLOADED,
                    original_filename=f"file_{i}.pdf",
                    file_size_bytes=1024 * (i + 1),
                )
                obj.transition_to(JobState.SECURITY_CHECK, "Started")
                obj.transition_to(JobState.PROFILING, "Passed security")
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = DocumentJob.model_validate_json(json_str)
                assert restored.job_id == obj.job_id and len(restored.state_history) == 2
                self.record_result("Pydantic Schema", "DocumentJob", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "DocumentJob", False, str(e))

        # 16. TenantLimits
        for i in range(self.num_samples):
            try:
                obj = TenantLimits(
                    max_pages_per_document=100 + i * 10,
                    max_concurrent_jobs=10 + i,
                    max_file_size_mb=50 + i * 5,
                    max_documents_per_day=1000 + i * 100,
                    gpu_priority="high" if i % 2 == 0 else "normal",
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = TenantLimits.model_validate_json(json_str)
                assert restored.max_pages_per_document == obj.max_pages_per_document
                self.record_result("Pydantic Schema", "TenantLimits", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "TenantLimits", False, str(e))

        # 17. TenantFeatures
        for i in range(self.num_samples):
            try:
                obj = TenantFeatures(
                    ocr_engine=OCREngine.UNLIMITED_OCR,
                    llm_escalation_enabled=bool(i % 2 == 0),
                    human_review_enabled=True,
                    fraud_detection_enabled=True,
                    pii_redaction_enabled=bool(i % 3 == 0),
                    custom_templates=[f"template_{i}"],
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = TenantFeatures.model_validate_json(json_str)
                assert restored.ocr_engine == OCREngine.UNLIMITED_OCR and len(restored.custom_templates) == 1
                self.record_result("Pydantic Schema", "TenantFeatures", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "TenantFeatures", False, str(e))

        # 18. TenantStorage
        for i in range(self.num_samples):
            try:
                obj = TenantStorage(
                    bucket=f"tenant-bucket-{i}",
                    region="us-west-2",
                    encryption_key_id=f"key_{i}",
                    retention_days=30 + i * 10,
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = TenantStorage.model_validate_json(json_str)
                assert restored.bucket == obj.bucket and restored.retention_days == obj.retention_days
                self.record_result("Pydantic Schema", "TenantStorage", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "TenantStorage", False, str(e))

        # 19. TenantConfig
        for i in range(self.num_samples):
            try:
                obj = TenantConfig(
                    tenant_id=f"tenant_cfg_{i}",
                    name=f"Tenant Enterprise {i}",
                    is_active=True,
                    limits=TenantLimits(max_file_size_mb=100),
                    features=TenantFeatures(llm_escalation_enabled=True),
                    storage=TenantStorage(bucket=f"bucket-{i}"),
                    auto_approve_threshold=0.90 + (i * 0.005),
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = TenantConfig.model_validate_json(json_str)
                assert restored.tenant_id == obj.tenant_id and restored.limits.max_file_size_mb == 100
                self.record_result("Pydantic Schema", "TenantConfig", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "TenantConfig", False, str(e))

        # 20. ModelRegistryEntry
        for i in range(self.num_samples):
            try:
                obj = ModelRegistryEntry(
                    model_id=f"unlimited_ocr_v{i}",
                    engine=OCREngine.UNLIMITED_OCR,
                    version=f"3.{i}.0",
                    architecture="3B-MoE",
                    deployment_backend="sglang",
                    capabilities=["ocr", "tables", "layout"],
                    traffic_percentage=1.0,
                )
                json_str = obj.model_dump_json()
                json.loads(json_str)
                restored = ModelRegistryEntry.model_validate_json(json_str)
                assert restored.model_id == obj.model_id and restored.version == obj.version
                self.record_result("Pydantic Schema", "ModelRegistryEntry", True)
            except Exception as e:
                self.record_result("Pydantic Schema", "ModelRegistryEntry", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORY B: 6 Ingestion File MIME Formats (PDF, PNG, JPEG, TIFF, BMP, WebP)
    # ══════════════════════════════════════════════════════════════════════════

    async def test_file_formats(self) -> None:
        print("Testing Category B: Input File Formats (Ingestion & JSON Conversion)...")
        mime_types = [
            ("PDF", "application/pdf", "sample.pdf"),
            ("PNG", "image/png", "sample.png"),
            ("JPEG", "image/jpeg", "sample.jpg"),
            ("TIFF", "image/tiff", "sample.tif"),
            ("BMP", "image/bmp", "sample.bmp"),
            ("WebP", "image/webp", "sample.webp"),
        ]

        for format_label, mime_type, filename_ext in mime_types:
            for i in range(self.num_samples):
                try:
                    filename = f"test_{i}_{filename_ext}"
                    file_bytes = create_mock_file_bytes(mime_type, i)
                    job, sec_result = await self.ingestion_service.ingest(
                        data=file_bytes,
                        filename=filename,
                        declared_mime=mime_type,
                        tenant=self.tenant_config,
                    )
                    assert sec_result == SecurityCheckResult.PASSED
                    assert job.content_type == mime_type
                    # Convert job state to JSON
                    json_str = job.model_dump_json()
                    parsed = json.loads(json_str)
                    assert parsed["content_type"] == mime_type and parsed["state"] == "profiling"
                    self.record_result("File Format MIME", format_label, True)
                except Exception as e:
                    self.record_result("File Format MIME", format_label, False, f"{type(e).__name__}: {str(e)}")

    # ══════════════════════════════════════════════════════════════════════════
    # CATEGORY C: 10 Document Domain Types (Rules, Normalization, Extraction to JSON)
    # ══════════════════════════════════════════════════════════════════════════

    async def test_document_types(self) -> None:
        print("Testing Category C: Document Domain Types (Extraction to JSON)...")

        N = self.num_samples
        doc_type_samples: Dict[str, List[str]] = {
            "Invoice": [
                f"INVOICE #{100+i}\nDate: 01/{(i%28)+1:02d}/2026\nBill To: Acme Corp {i}\nSubtotal: ${500+i*10}.00\nTax: ${45+i}.00\nTotal: ${545+i*10+i}.00" for i in range(N)
            ],
            "Receipt": [
                f"Store #{i+1} Supermarket\nDate: 0{(i%12)+1:02d}/15/2026\nPaid with Credit Card\nTOTAL: ${12+i}.99\nThank you for shopping!" for i in range(N)
            ],
            "ID Card": [
                f"DRIVERS LICENSE\nID No: DL-8890{i}\nName: John Doe {i}\nDOB: 05/12/198{(i%10)}\nAddress: 12{i} Main St, Cityville" for i in range(N)
            ],
            "Bank Statement": [
                f"BANK STATEMENT\nAccount Number: ACCT-901{i}\nStatement Date: 01/31/2026\nOpening Balance: $1,000.00\nClosing Balance: ${2500+i*100}.00" for i in range(N)
            ],
            "Utility Bill": [
                f"ELECTRIC UTILITY BILL\nAccount No: ELEC-55{i}\nBilling Date: 01/15/2026\nUsage: {300+i*20} kWh\nTotal Amount: ${75+i*5}.50" for i in range(N)
            ],
            "Tax Form": [
                f"FORM W-2 Wage and Tax Statement 2026\nSSN: XXX-XX-440{i}\nEmployer ID: EIN-998{i}\nWages: ${75000+i*1000}.00\nFederal Tax: ${12000+i*200}.00" for i in range(N)
            ],
            "Contract": [
                f"SERVICE AGREEMENT #{i+1}\nDate: 01/01/2026\nParty A: Tech Solutions LLC\nParty B: Enterprise Inc {i}\nContract Value: ${50000+i*5000}.00" for i in range(N)
            ],
            "Purchase Order": [
                f"PURCHASE ORDER PO-{202600+i}\nPO Date: 01/20/2026\nVendor: Supply Chain Co\nQuantity: {10+i} Units\nTotal Amount: ${1500+i*150}.00" for i in range(N)
            ],
            "Medical Claim": [
                f"HEALTH INSURANCE CLAIM\nClaim ID: CLM-77{i}\nPatient: Jane Smith {i}\nService Date: 01/10/2026\nTotal Charge: ${350+i*25}.00" for i in range(N)
            ],
            "Custom Form": [
                f"CUSTOM REGISTRATION FORM\nReference ID: REF-{4400+i}\nSubmission Date: 01/25/2026\nApplicant: Bob Miller {i}\nStatus: Approved" for i in range(N)
            ],
        }

        for doc_type_name, samples in doc_type_samples.items():
            for i, raw_text in enumerate(samples):
                try:
                    # 1. Normalize
                    ext_res = ExtractionResult(
                        doc_id=f"doc_{doc_type_name}_{i}",
                        tenant_id="tenant_1",
                        pages=[PageExtractionResult(page_num=1, raw_text=raw_text)],
                    )
                    norm_out = await self.normalizer_service.normalize(ext_res)
                    norm_json = norm_out.model_dump_json()
                    json.loads(norm_json)

                    # 2. Extract
                    extracted_out = await self.extraction_service.extract(norm_out, doc_type=doc_type_name.lower())
                    extr_json = extracted_out.model_dump_json()
                    parsed_extr = json.loads(extr_json)

                    assert "fields" in parsed_extr and "doc_id" in parsed_extr
                    self.record_result("Document Domain Type", doc_type_name, True)
                except Exception as e:
                    self.record_result("Document Domain Type", doc_type_name, False, f"{type(e).__name__}: {str(e)}")

    def run_all_tests(self) -> Tuple[int, int, float]:
        print("\n============================================================")
        print("Starting Comprehensive JSON Conversion Benchmark (36 Datatypes)")
        print("============================================================\n")

        self.test_pydantic_schemas()
        asyncio.run(self.test_file_formats())
        asyncio.run(self.test_document_types())

        total_tests = sum(r["total"] for r in self.results.values())
        total_passed = sum(r["passed"] for r in self.results.values())
        total_failed = sum(r["failed"] for r in self.results.values())
        overall_success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0.0

        return total_tests, total_passed, overall_success_rate


def test_datatype_json_conversions_benchmark() -> None:
    tester = DatatypeJSONTester()
    total, passed, win_rate = tester.run_all_tests()
    assert total == 720
    assert passed == 720
    assert win_rate == 100.0


if __name__ == "__main__":
    tester = DatatypeJSONTester()
    total, passed, win_rate = tester.run_all_tests()

    print("\n" + "=" * 80)
    print(f"{'DATATYPE NAME':<35} | {'CATEGORY':<20} | {'TESTS':<6} | {'PASS':<6} | {'WIN RATE':<10}")
    print("=" * 80)

    all_100_percent = True
    failures_summary = []

    for key, data in sorted(tester.results.items()):
        name = data["name"]
        cat = data["category"]
        t = data["total"]
        p = data["passed"]
        rate = (p / t) * 100 if t > 0 else 0.0
        print(f"{name:<35} | {cat:<20} | {t:<6} | {p:<6} | {rate:6.1f}%")
        if p < t:
            all_100_percent = False
            failures_summary.append((name, cat, data['errors']))

    print("=" * 80)
    print(f"TOTAL TESTED: {total} | TOTAL PASSED: {passed} | OVERALL SUCCESS RATE: {win_rate:.2f}%")
    print("=" * 80)

    if all_100_percent:
        print("\n🎉 100% WIN RATE ACHIEVED ACROSS ALL DATA TYPES!")
    else:
        print("\n⚠️ 100% WIN RATE WAS NOT ACHIEVED. DETAILED FAILURE ANALYSIS:")
        for name, cat, errors in failures_summary:
            print(f"- Datatype: {name} ({cat})")
            for err in set(errors):
                print(f"  Reason: {err}")

