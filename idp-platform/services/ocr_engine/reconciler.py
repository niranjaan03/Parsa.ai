"""
Reconcile & Reconstruct Module — Post-OCR assembly.

After the Extraction Router returns per-page results, this module:
  1. Merges regions in reading order across pages
  2. Reconciles bounding boxes (handles overlaps, near-duplicates)
  3. Detects cross-page continuity (tables/paragraphs spanning pages)
  4. Deduplicates regions (same content detected by overlapping regions)
  5. Aggregates confidence scores per region and overall
  6. Produces the final, coherent document-level extraction result
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from libs.common.schemas import (
    BoundingBox,
    ContentType,
    ExtractionResult,
    PageExtractionResult,
    Region,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Minimum similarity ratio to consider two regions as duplicates
DEDUP_SIMILARITY_THRESHOLD = 0.85

# Maximum vertical gap (in pixels) between consecutive regions to merge
MERGE_VERTICAL_GAP = 20

# Content types that can span across pages
CROSS_PAGE_TYPES = {ContentType.TABLE, ContentType.PARAGRAPH, ContentType.PRINTED_TEXT}


# ═══════════════════════════════════════════════════════════════════════════════
# Core Functions
# ═══════════════════════════════════════════════════════════════════════════════


def reconcile_document(extraction: ExtractionResult) -> ExtractionResult:
    """
    Full reconciliation pipeline for a document's extraction results.

    Steps:
      1. Deduplicate regions within each page
      2. Detect and merge cross-page continuity
      3. Recompute reading order
      4. Aggregate confidence scores
      5. Rebuild clean full text

    Returns a new ExtractionResult with cleaned, merged results.
    """
    if not extraction.pages:
        return extraction

    # Step 1: Per-page deduplication
    cleaned_pages = []
    for page in extraction.pages:
        deduped_regions = _deduplicate_regions(page.regions)
        cleaned_pages.append(
            page.model_copy(update={"regions": deduped_regions})
        )

    # Step 2: Cross-page continuity detection
    cleaned_pages = _merge_cross_page_regions(cleaned_pages)

    # Step 3: Recompute reading order within each page
    for page in cleaned_pages:
        page.regions = _sort_reading_order(page.regions)

    # Step 4: Rebuild clean text per page
    for page in cleaned_pages:
        if page.regions:
            page.raw_text = _build_page_text(page.regions)

    # Step 5: Aggregate confidence
    overall = _aggregate_confidence(cleaned_pages)

    return extraction.model_copy(
        update={
            "pages": cleaned_pages,
            "overall_confidence": overall,
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Deduplication
# ═══════════════════════════════════════════════════════════════════════════════


def _deduplicate_regions(regions: list[Region]) -> list[Region]:
    """
    Remove duplicate regions (same content from overlapping detection).

    Two regions are considered duplicates if:
      - Their content similarity exceeds DEDUP_SIMILARITY_THRESHOLD
      - Their bounding boxes overlap significantly (if boxes are present)

    When duplicates are found, keep the one with higher confidence.
    """
    if len(regions) <= 1:
        return regions

    keep: list[Region] = []
    skip_indices: set[int] = set()

    for i, region_a in enumerate(regions):
        if i in skip_indices:
            continue

        best = region_a
        for j in range(i + 1, len(regions)):
            if j in skip_indices:
                continue

            region_b = regions[j]

            # Check content similarity
            if region_a.content and region_b.content:
                similarity = SequenceMatcher(
                    None, region_a.content, region_b.content
                ).ratio()

                if similarity >= DEDUP_SIMILARITY_THRESHOLD:
                    # Check bbox overlap (if available)
                    if _bboxes_overlap(region_a.bbox, region_b.bbox):
                        # Keep the higher-confidence one
                        if region_b.confidence > best.confidence:
                            best = region_b
                        skip_indices.add(j)

        keep.append(best)

    return keep


def _bboxes_overlap(a: BoundingBox | None, b: BoundingBox | None) -> bool:
    """Check if two bounding boxes overlap (or if either is missing)."""
    if a is None or b is None:
        return True  # Without bbox, assume potential overlap

    # Check for no overlap
    if a.x2 < b.x or b.x2 < a.x:
        return False
    if a.y2 < b.y or b.y2 < a.y:
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-Page Continuity
# ═══════════════════════════════════════════════════════════════════════════════


def _merge_cross_page_regions(
    pages: list[PageExtractionResult],
) -> list[PageExtractionResult]:
    """
    Detect and merge content that spans page boundaries.

    Handles:
      - Tables that continue from one page to the next
      - Paragraphs split across pages
      - Sentences cut mid-word at page break
    """
    if len(pages) <= 1:
        return pages

    for i in range(len(pages) - 1):
        current_page = pages[i]
        next_page = pages[i + 1]

        if not current_page.regions or not next_page.regions:
            continue

        last_region = current_page.regions[-1]
        first_region = next_page.regions[0]

        # Check if these regions should be merged
        if _should_merge_across_pages(last_region, first_region):
            # Merge: append next page's first region content to current's last
            merged_content = last_region.content.rstrip() + "\n" + first_region.content.lstrip()

            # Update current page's last region
            updated_last = last_region.model_copy(
                update={
                    "content": merged_content,
                    "confidence": (last_region.confidence + first_region.confidence) / 2,
                    "metadata": {
                        **last_region.metadata,
                        "cross_page_merge": True,
                        "merged_from_page": next_page.page_num,
                    },
                }
            )
            current_page.regions[-1] = updated_last

            # Remove the first region from the next page
            next_page.regions = next_page.regions[1:]

    return pages


def _should_merge_across_pages(last: Region, first: Region) -> bool:
    """Determine if two regions at a page boundary should be merged."""
    # Only merge compatible content types
    if last.content_type not in CROSS_PAGE_TYPES:
        return False
    if first.content_type not in CROSS_PAGE_TYPES:
        return False

    # Tables should merge with tables
    if last.content_type == ContentType.TABLE and first.content_type == ContentType.TABLE:
        return True

    # Check if the last region's text is cut mid-sentence
    if last.content and first.content:
        last_text = last.content.rstrip()
        # Indicators of a broken sentence:
        # - Ends without terminal punctuation
        # - Ends with a hyphen (word break)
        # - First region starts with lowercase
        if last_text and last_text[-1] in "-–—":
            return True
        if last_text and last_text[-1] not in ".!?;:\"')]}。！？；：":
            if first.content and first.content[0].islower():
                return True

    return False


# ═══════════════════════════════════════════════════════════════════════════════
# Reading Order & Text Assembly
# ═══════════════════════════════════════════════════════════════════════════════


def _sort_reading_order(regions: list[Region]) -> list[Region]:
    """
    Sort regions in natural reading order.

    Strategy: top-to-bottom, then left-to-right within the same vertical band.
    Regions without bounding boxes are ordered by their original reading_order.
    """
    def sort_key(region: Region) -> tuple[float, float, int]:
        if region.bbox:
            # Group into vertical bands (quantize y to reduce noise)
            y_band = region.bbox.y // 50 * 50
            return (y_band, region.bbox.x, region.reading_order)
        return (float("inf"), 0, region.reading_order)

    sorted_regions = sorted(regions, key=sort_key)

    # Update reading_order to reflect new sort
    for i, region in enumerate(sorted_regions):
        region.reading_order = i

    return sorted_regions


def _build_page_text(regions: list[Region]) -> str:
    """Build clean page text from sorted regions."""
    parts: list[str] = []
    for region in regions:
        if region.content and region.content_type != ContentType.IMAGE:
            parts.append(region.content)
    return "\n\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# Confidence Aggregation
# ═══════════════════════════════════════════════════════════════════════════════


def _aggregate_confidence(pages: list[PageExtractionResult]) -> float:
    """
    Compute overall document confidence from page-level scores.

    Weighted by the amount of content on each page (more content = more weight).
    """
    if not pages:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for page in pages:
        # Weight by content length (proxy for information density)
        weight = max(1.0, len(page.raw_text))
        weighted_sum += page.confidence * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return weighted_sum / total_weight
