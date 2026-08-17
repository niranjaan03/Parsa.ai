"""
Unit & Integration Tests for Office Ingestion (.docx, .pptx) and Semantic RAG Chunking.
"""

import io
import os
import sys
import zipfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from libs.common.chunker import SemanticChunker
from libs.common.job_states import JobState
from libs.common.schemas import (
    BoundingBox,
    ContentType,
    DocumentJob,
    InputSource,
    Region,
    TenantConfig,
)
from services.ingestion.service import (
    IngestionService,
    OfficeDocumentConverter,
    SecurityCheckResult,
    detect_mime,
    validate_mime,
)
from services.orchestrator.pipeline import PipelineOrchestrator


def _create_dummy_docx_bytes(title: str = "Test Agreement", body: str = "This is a sample contract text.") -> bytes:
    """Create a minimal valid OpenXML .docx in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # [Content_Types].xml
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>'
        )
        zf.writestr("[Content_Types].xml", content_types)

        # word/document.xml
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body>'
            f'<w:p><w:r><w:t>{title}</w:t></w:r></w:p>'
            f'<w:p><w:r><w:t>{body}</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>Clause 1: Confidentiality and Non-Disclosure.</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>Total Amount Due: $15,000.00 USD payable upon delivery.</w:t></w:r></w:p>'
            '</w:body>'
            '</w:document>'
        )
        zf.writestr("word/document.xml", doc_xml)
    return buf.getvalue()


def _create_dummy_pptx_bytes() -> bytes:
    """Create a minimal valid OpenXML .pptx in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Override PartName="/ppt/presentation.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            '</Types>',
        )
        zf.writestr(
            "ppt/presentation.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>',
        )
        slide1_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:cSld><p:spTree><p:sp><p:txBody>'
            '<a:p><a:r><a:t>Executive Q3 Business Review</a:t></a:r></a:p>'
            '<a:p><a:r><a:t>Total Revenue: $4,500,000 ARR</a:t></a:r></a:p>'
            '</p:txBody></p:sp></p:spTree></p:cSld>'
            '</p:sld>'
        )
        zf.writestr("ppt/slides/slide1.xml", slide1_xml)
    return buf.getvalue()


def test_office_mime_detection():
    """Test detection of .docx and .pptx packages."""
    docx_bytes = _create_dummy_docx_bytes()
    mime_docx = detect_mime(docx_bytes, "agreement.docx")
    assert "wordprocessingml" in mime_docx

    pptx_bytes = _create_dummy_pptx_bytes()
    mime_pptx = detect_mime(pptx_bytes, "presentation.pptx")
    assert "presentationml" in mime_pptx

    is_valid_docx, _ = validate_mime(docx_bytes, filename="agreement.docx")
    assert is_valid_docx is True

    is_valid_pptx, _ = validate_mime(pptx_bytes, filename="deck.pptx")
    assert is_valid_pptx is True


def test_office_document_conversion():
    """Test conversion of DOCX and PPTX to valid PDF bytes."""
    docx_bytes = _create_dummy_docx_bytes()
    pdf_bytes, engine = OfficeDocumentConverter.convert_to_pdf(docx_bytes, "agreement.docx")
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 200

    pptx_bytes = _create_dummy_pptx_bytes()
    pdf_pptx, engine_pptx = OfficeDocumentConverter.convert_to_pdf(pptx_bytes, "q3_deck.pptx")
    assert pdf_pptx.startswith(b"%PDF")
    assert len(pdf_pptx) > 200


@pytest.mark.asyncio
async def test_stage1_office_ingestion():
    """Test full Stage 1 ingestion of an office document."""
    service = IngestionService()
    tenant = TenantConfig(tenant_id="demo-tenant", name="Demo")
    docx_bytes = _create_dummy_docx_bytes()

    job, result = await service.ingest(
        data=docx_bytes,
        filename="contract.docx",
        declared_mime=None,
        tenant=tenant,
        source=InputSource.API,
    )

    assert result == SecurityCheckResult.PASSED
    assert job.state == JobState.PROFILING
    assert job.content_type == "application/pdf"


def test_semantic_chunker_from_text():
    """Test SemanticChunker splitting text at semantic boundaries."""
    chunker = SemanticChunker(default_chunk_size=300)
    sample_text = (
        "# Section 1: Executive Overview\n\n"
        "The Intelligent Document Processing platform automates parsing for enterprise workloads. "
        "It supports PDF, DOCX, and image pipelines seamlessly with high accuracy.\n\n"
        "# Section 2: Financial Terms\n\n"
        "| Invoice No | Subtotal | Tax | Total Due |\n"
        "| INV-1001   | $1,000   | $80 | $1,080    |\n\n"
        "Payment is due within 30 calendar days from receipt of invoice."
    )

    result = chunker.chunk_document(full_text=sample_text, chunk_size=200)
    assert result.total_segments >= 2
    for seg in result.segments:
        assert seg.char_count > 0
        assert len(seg.pages) > 0
        assert seg.segment_id is not None


def test_semantic_chunker_with_parent_bboxes():
    """Test SemanticChunker retaining parent bounding boxes and page provenance."""
    regions = [
        Region(
            content_type=ContentType.HEADER,
            bbox=BoundingBox(x=54.0, y=72.0, width=500.0, height=24.0),
            content="# INVOICE BILLING STATEMENT",
            metadata={"page_num": 1},
        ),
        Region(
            content_type=ContentType.PRINTED_TEXT,
            bbox=BoundingBox(x=54.0, y=110.0, width=400.0, height=18.0),
            content="Customer Name: Acme Global Logistics Inc.",
            metadata={"page_num": 1},
        ),
        Region(
            content_type=ContentType.TABLE,
            bbox=BoundingBox(x=54.0, y=140.0, width=500.0, height=120.0),
            content="| Line Item | Qty | Rate | Amount |\n| Freight Shipping | 1 | $3,500.00 | $3,500.00 |",
            metadata={"page_num": 1},
        ),
        Region(
            content_type=ContentType.PRINTED_TEXT,
            bbox=BoundingBox(x=54.0, y=280.0, width=300.0, height=18.0),
            content="Total Due: $3,500.00 USD",
            metadata={"page_num": 1},
        ),
    ]

    chunker = SemanticChunker(default_chunk_size=150)
    result = chunker.chunk_document(regions=regions, chunk_size=150)

    assert result.total_segments >= 1
    for seg in result.segments:
        assert len(seg.bounding_boxes) > 0
        assert len(seg.members) > 0
        # Verify member provenance
        member = seg.members[0]
        assert member.page_no == 1
        assert len(member.bbox) == 4
