"""
Document Profiler Service — Phase 2.

Analyzes a document before any OCR to determine:
  - Is it a digital PDF (native text) or scanned/image?
  - What language(s) does it contain?
  - What is the image quality?
  - What type of document is it (invoice, contract, form, etc.)?
  - What regions exist on each page (text, tables, images, etc.)?
  - What pre-processing strategy should be applied?

This profile drives routing decisions in the Extraction Router (Phase 3)
and pre-processing pipeline (Phase 2b).
"""

from __future__ import annotations

import io
import logging
import time
from typing import Any

from libs.common.schemas import (
    BoundingBox,
    ContentType,
    DocumentProfile,
    PageProfile,
    Region,
)

logger = logging.getLogger(__name__)


class DocumentProfiler:
    """
    Produces a structured DocumentProfile for any input document.

    The profile determines:
      1. Whether to use native text extraction (fast) or OCR (GPU)
      2. What pre-processing to apply (denoise, deskew, etc.)
      3. What document type template to try for extraction
    """

    async def profile_pdf(
        self,
        pdf_bytes: bytes,
        tenant_id: str,
        doc_id: str,
    ) -> DocumentProfile:
        """Profile a PDF document."""
        import fitz

        start_time = time.monotonic()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        pages: list[PageProfile] = []
        total_text_chars = 0
        total_image_area = 0

        for page_num, page in enumerate(doc, start=1):
            # Check for native text
            text = page.get_text("text")
            has_text = bool(text.strip())
            text_chars = len(text.strip())
            total_text_chars += text_chars

            # Check for images
            image_list = page.get_images(full=True)
            page_rect = page.rect
            page_area = page_rect.width * page_rect.height

            image_area = 0
            for img in image_list:
                xref = img[0]
                try:
                    img_rect = page.get_image_rects(xref)
                    for rect in img_rect:
                        image_area += rect.width * rect.height
                except Exception:
                    pass

            total_image_area += image_area

            # Determine if page is native text or scanned
            # Heuristic: if text is substantial and images are large, it's likely scanned
            # with an invisible text layer. If text is present and images are small, it's digital.
            is_native = has_text and (image_area / max(page_area, 1) < 0.5)

            # Quality score heuristic
            quality = 1.0 if is_native else 0.7
            if image_list:
                # Check image resolution
                for img_info in image_list:
                    xref = img_info[0]
                    try:
                        pix = fitz.Pixmap(doc, xref)
                        if pix.width < 150 or pix.height < 150:
                            quality = min(quality, 0.4)  # Low resolution
                        elif pix.width < 300 or pix.height < 300:
                            quality = min(quality, 0.6)
                        pix = None  # Free memory
                        break  # Check first image only for speed
                    except Exception:
                        pass

            # Simple region detection from text blocks
            regions: list[Region] = []
            blocks = page.get_text("dict", flags=0)
            for block in blocks.get("blocks", []):
                if block.get("type") == 0:  # text block
                    bbox_raw = block.get("bbox", (0, 0, 0, 0))
                    block_text = ""
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            block_text += span.get("text", "")

                    if block_text.strip():
                        regions.append(
                            Region(
                                content_type=ContentType.PRINTED_TEXT,
                                bbox=BoundingBox(
                                    x=bbox_raw[0],
                                    y=bbox_raw[1],
                                    width=max(1, bbox_raw[2] - bbox_raw[0]),
                                    height=max(1, bbox_raw[3] - bbox_raw[1]),
                                ),
                                content=block_text.strip()[:100],  # Preview only
                            )
                        )

            pages.append(
                PageProfile(
                    page_num=page_num,
                    width_px=int(page_rect.width),
                    height_px=int(page_rect.height),
                    is_native_text=is_native,
                    quality_score=quality,
                    detected_languages=[],  # TODO: language detection
                    regions=regions,
                    preprocessing_strategy="none" if is_native else self._select_strategy(quality),
                )
            )

        doc.close()

        # Overall document profile
        all_native = all(p.is_native_text for p in pages) if pages else False
        avg_quality = sum(p.quality_score for p in pages) / len(pages) if pages else 0.5

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            "Profiled document %s: %d pages, native=%s, quality=%.2f in %dms",
            doc_id,
            len(pages),
            all_native,
            avg_quality,
            elapsed_ms,
        )

        return DocumentProfile(
            doc_id=doc_id,
            tenant_id=tenant_id,
            is_native_text=all_native,
            overall_quality_score=avg_quality,
            page_count=len(pages),
            pages=pages,
            preprocessing_strategy="none" if all_native else self._select_strategy(avg_quality),
            metadata={"profiling_time_ms": elapsed_ms},
        )

    async def profile_image(
        self,
        image_bytes: bytes,
        tenant_id: str,
        doc_id: str,
    ) -> DocumentProfile:
        """Profile a single image document."""
        from PIL import Image

        start_time = time.monotonic()
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size

        # Quality score based on resolution
        min_dim = min(width, height)
        if min_dim >= 2000:
            quality = 0.9
        elif min_dim >= 1000:
            quality = 0.7
        elif min_dim >= 500:
            quality = 0.5
        else:
            quality = 0.3

        page = PageProfile(
            page_num=1,
            width_px=width,
            height_px=height,
            is_native_text=False,
            quality_score=quality,
            preprocessing_strategy=self._select_strategy(quality),
        )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        return DocumentProfile(
            doc_id=doc_id,
            tenant_id=tenant_id,
            is_native_text=False,
            overall_quality_score=quality,
            page_count=1,
            pages=[page],
            preprocessing_strategy=self._select_strategy(quality),
            metadata={"profiling_time_ms": elapsed_ms, "image_size": f"{width}x{height}"},
        )

    def _select_strategy(self, quality_score: float) -> str:
        """Select pre-processing strategy based on quality score."""
        if quality_score >= 0.8:
            return "light"       # Minimal processing — just deskew
        elif quality_score >= 0.5:
            return "standard"    # Deskew + light denoise
        elif quality_score >= 0.3:
            return "aggressive"  # Deskew + denoise + contrast enhancement
        else:
            return "maximum"     # Full enhancement pipeline
