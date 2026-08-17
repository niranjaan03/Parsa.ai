"""
Native PDF Text Extractor — Fast path for digital PDFs.

When the Document Profiler (Phase 2) detects a PDF with embedded text layers
(native/digital PDF), this extractor uses PyMuPDF to pull text directly
without invoking any OCR model — saving GPU compute and latency.

This is the "Digital PDF? → Native text path" decision branch from the
architecture diagram.
"""

from __future__ import annotations

import io
import logging
import time

from libs.common.schemas import (
    ContentType,
    OCREngine,
    PageExtractionResult,
    PageProfile,
    DocumentProfile,
    Region,
)

from .base import ExtractionAdapter, ExtractionConfig

logger = logging.getLogger(__name__)


class NativePDFExtractor(ExtractionAdapter):
    """
    Extract text from digital PDFs using PyMuPDF (no OCR needed).

    This is the fastest and cheapest extraction path. It only works
    for PDFs with embedded text layers — scanned/image PDFs will
    produce empty output and should be routed to an OCR engine instead.
    """

    engine = OCREngine.NATIVE_PDF

    async def extract_page(
        self,
        image_data: bytes,
        page_profile: PageProfile,
        config: ExtractionConfig | None = None,
    ) -> PageExtractionResult:
        """
        Extract text from a single page of a digital PDF.

        Note: For native PDF extraction, 'image_data' is actually the
        full PDF bytes. Use extract_from_pdf() for the standard workflow.
        """
        # This adapter is primarily used via extract_from_pdf()
        # Single page extraction from raw image bytes doesn't apply here
        return PageExtractionResult(
            page_num=page_profile.page_num,
            raw_text="",
            regions=[],
            confidence=0.0,
            engine=OCREngine.NATIVE_PDF,
            latency_ms=0,
            token_count=0,
        )

    async def extract_from_pdf(
        self,
        pdf_bytes: bytes,
        doc_profile: DocumentProfile,
    ) -> list[PageExtractionResult]:
        """
        Extract text from all pages of a digital PDF using PyMuPDF.

        Returns one PageExtractionResult per page with high confidence
        (native text extraction is reliable for digital PDFs).
        """
        import fitz  # PyMuPDF

        start_time = time.monotonic()
        results: list[PageExtractionResult] = []

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            for page_num, page in enumerate(doc, start=1):
                page_start = time.monotonic()

                # Extract text blocks with position info
                blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                regions: list[Region] = []
                full_text_parts: list[str] = []
                reading_order = 0

                for block in blocks.get("blocks", []):
                    if block.get("type") == 0:  # Text block
                        block_text = ""
                        for line in block.get("lines", []):
                            line_text = ""
                            for span in line.get("spans", []):
                                line_text += span.get("text", "")
                            block_text += line_text + "\n"

                        block_text = block_text.strip()
                        if block_text:
                            bbox = block.get("bbox", (0, 0, 0, 0))
                            from libs.common.schemas import BoundingBox

                            regions.append(
                                Region(
                                    content_type=ContentType.PRINTED_TEXT,
                                    bbox=BoundingBox(
                                        x=bbox[0],
                                        y=bbox[1],
                                        width=max(1, bbox[2] - bbox[0]),
                                        height=max(1, bbox[3] - bbox[1]),
                                    ),
                                    content=block_text,
                                    confidence=0.99,  # Native text is highly reliable
                                    reading_order=reading_order,
                                )
                            )
                            full_text_parts.append(block_text)
                            reading_order += 1

                    elif block.get("type") == 1:  # Image block
                        bbox = block.get("bbox", (0, 0, 0, 0))
                        from libs.common.schemas import BoundingBox

                        regions.append(
                            Region(
                                content_type=ContentType.IMAGE,
                                bbox=BoundingBox(
                                    x=bbox[0],
                                    y=bbox[1],
                                    width=max(1, bbox[2] - bbox[0]),
                                    height=max(1, bbox[3] - bbox[1]),
                                ),
                                content="[image]",
                                confidence=1.0,
                                reading_order=reading_order,
                            )
                        )
                        reading_order += 1

                full_text = "\n\n".join(full_text_parts)
                page_ms = int((time.monotonic() - page_start) * 1000)

                results.append(
                    PageExtractionResult(
                        page_num=page_num,
                        raw_text=full_text,
                        regions=regions,
                        confidence=0.99 if full_text else 0.0,
                        engine=OCREngine.NATIVE_PDF,
                        latency_ms=page_ms,
                        token_count=len(full_text.split()),
                    )
                )

            doc.close()

        except Exception as e:
            logger.error("Native PDF extraction failed: %s", e)
            # Return empty results — the router should fallback to OCR
            for i in range(doc_profile.page_count):
                results.append(
                    PageExtractionResult(
                        page_num=i + 1,
                        raw_text="",
                        regions=[],
                        confidence=0.0,
                        engine=OCREngine.NATIVE_PDF,
                        latency_ms=0,
                    )
                )

        total_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "Native PDF extraction: %d pages in %dms",
            len(results),
            total_ms,
        )

        return results

    async def health_check(self) -> bool:
        """Always healthy — no external dependency."""
        try:
            import fitz  # noqa: F401
            return True
        except ImportError:
            return False

    def get_capabilities(self) -> list[ContentType]:
        return [ContentType.PRINTED_TEXT, ContentType.IMAGE]
