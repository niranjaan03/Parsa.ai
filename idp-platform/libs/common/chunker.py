"""
Semantic RAG Chunker — Structural and Context-Aware Document Segmentation.

Splits document text and OCR regions into semantic units ready for RAG embedding:
  - Respects headings, paragraphs, and list boundaries
  - Keeps table structures coherent (splitting only on row boundaries)
  - Retains parent bounding boxes ([x0, y0, x1, y1]) and page numbers for visual grounding
  - Target chunk size with elastic ±25% boundary window
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from libs.common.schemas import (
    BoundingBox,
    Region,
    SemanticChunkingResult,
    SemanticSegment,
    SemanticSegmentMember,
)

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Splits OCR / document text into structured semantic segments for RAG pipelines.
    """

    def __init__(self, default_chunk_size: int = 1000) -> None:
        self.default_chunk_size = default_chunk_size

    def chunk_document(
        self,
        full_text: str = "",
        regions: list[Region] | None = None,
        chunk_size: int | None = None,
        page_dimensions: list[dict[str, Any]] | None = None,
    ) -> SemanticChunkingResult:
        """
        Produce semantic chunks from raw document text and/or extracted layout regions.
        """
        target_size = chunk_size or self.default_chunk_size
        min_size = int(target_size * 0.75)
        max_size = int(target_size * 1.25)

        segments: list[SemanticSegment] = []

        # If regions with bounding boxes are available, chunk by regions
        if regions and len(regions) > 0:
            segments = self._chunk_from_regions(regions, target_size, min_size, max_size)
        elif full_text:
            segments = self._chunk_from_text(full_text, target_size, min_size, max_size)

        # Fallback if empty
        if not segments and full_text:
            segments.append(
                SemanticSegment(
                    segment_id=uuid.uuid4().hex[:12],
                    content=full_text.strip(),
                    char_count=len(full_text.strip()),
                    pages=[1],
                    bounding_boxes=[],
                    members=[],
                    chunk_type="text",
                )
            )

        return SemanticChunkingResult(
            segments=segments,
            total_segments=len(segments),
            chunk_size_target=target_size,
            page_dimensions=page_dimensions or [{"page_no": 1, "width": 612, "height": 792}],
            metadata={"strategy": "semantic", "segments_count": len(segments)},
        )

    def _chunk_from_regions(
        self,
        regions: list[Region],
        target_size: int,
        min_size: int,
        max_size: int,
    ) -> list[SemanticSegment]:
        """Group OCR regions into semantic chunks while maintaining bounding box provenance."""
        segments: list[SemanticSegment] = []
        current_members: list[SemanticSegmentMember] = []
        current_texts: list[str] = []
        current_pages: set[int] = set()
        current_bboxes: list[dict[str, Any]] = []
        current_len = 0
        has_table = False

        for idx, region in enumerate(regions):
            text = (region.content or "").strip()
            if not text:
                continue

            page_num = region.metadata.get("page_num", 1) if region.metadata else 1
            bbox_coords = []
            if region.bbox:
                # [x0, y0, x1, y1] in points/pixels
                bbox_coords = [
                    round(region.bbox.x, 2),
                    round(region.bbox.y, 2),
                    round(region.bbox.x2, 2),
                    round(region.bbox.y2, 2),
                ]

            member = SemanticSegmentMember(
                page_no=page_num,
                bbox=bbox_coords,
                source_index=idx,
                text=text,
            )

            is_heading = text.startswith(("#", "##", "###")) or str(region.content_type) in ("header", "ContentType.HEADER")
            is_table = str(region.content_type) in ("table", "ContentType.TABLE") or ("|" in text and "\n|" in text)
            item_len = len(text)

            # Check if we should split before adding this item
            should_split = False
            if current_len > 0:
                if is_heading and current_len >= min_size:
                    should_split = True
                elif current_len + item_len > max_size:
                    should_split = True
                elif is_table and current_len >= min_size:
                    should_split = True

            if should_split and current_texts:
                combined_content = "\n\n".join(current_texts)
                chunk_type = "table" if (has_table and len(current_texts) == 1) else ("mixed" if has_table else "text")
                segments.append(
                    SemanticSegment(
                        segment_id=uuid.uuid4().hex[:12],
                        content=combined_content,
                        char_count=len(combined_content),
                        pages=sorted(list(current_pages)),
                        bounding_boxes=current_bboxes,
                        members=current_members,
                        chunk_type=chunk_type,
                    )
                )
                current_members = []
                current_texts = []
                current_pages = set()
                current_bboxes = []
                current_len = 0
                has_table = False

            # Add current item
            current_texts.append(text)
            current_members.append(member)
            current_pages.add(page_num)
            if bbox_coords:
                current_bboxes.append({"page_no": page_num, "bbox": bbox_coords})
            current_len += item_len
            if is_table:
                has_table = True

        # Flush any remainder
        if current_texts:
            combined_content = "\n\n".join(current_texts)
            chunk_type = "table" if (has_table and len(current_texts) == 1) else ("mixed" if has_table else "text")
            segments.append(
                SemanticSegment(
                    segment_id=uuid.uuid4().hex[:12],
                    content=combined_content,
                    char_count=len(combined_content),
                    pages=sorted(list(current_pages)),
                    bounding_boxes=current_bboxes,
                    members=current_members,
                    chunk_type=chunk_type,
                )
            )

        return segments

    def _chunk_from_text(
        self,
        full_text: str,
        target_size: int,
        min_size: int,
        max_size: int,
    ) -> list[SemanticSegment]:
        """Split raw text at paragraph/section boundaries."""
        # Split by double newline or headings
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", full_text) if p.strip()]
        segments: list[SemanticSegment] = []
        current_parts: list[str] = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p)
            is_heading = p.startswith(("#", "##", "###", "SECTION", "CHAPTER"))

            if current_parts and ((is_heading and current_len >= min_size) or (current_len + p_len > max_size)):
                combined = "\n\n".join(current_parts)
                segments.append(
                    SemanticSegment(
                        segment_id=uuid.uuid4().hex[:12],
                        content=combined,
                        char_count=len(combined),
                        pages=[1],
                        bounding_boxes=[{"page_no": 1, "bbox": [0.0, 0.0, 612.0, 792.0]}],
                        members=[
                            SemanticSegmentMember(
                                page_no=1,
                                bbox=[0.0, 0.0, 612.0, 792.0],
                                source_index=len(segments),
                                text=combined,
                            )
                        ],
                        chunk_type="table" if "|" in combined and "\n|" in combined else "text",
                    )
                )
                current_parts = []
                current_len = 0

            current_parts.append(p)
            current_len += p_len

        if current_parts:
            combined = "\n\n".join(current_parts)
            segments.append(
                SemanticSegment(
                    segment_id=uuid.uuid4().hex[:12],
                    content=combined,
                    char_count=len(combined),
                    pages=[1],
                    bounding_boxes=[{"page_no": 1, "bbox": [0.0, 0.0, 612.0, 792.0]}],
                    members=[
                        SemanticSegmentMember(
                            page_no=1,
                            bbox=[0.0, 0.0, 612.0, 792.0],
                            source_index=len(segments),
                            text=combined,
                        )
                    ],
                    chunk_type="table" if "|" in combined and "\n|" in combined else "text",
                )
            )

        return segments
