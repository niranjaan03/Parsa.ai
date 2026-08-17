"""
Unlimited-OCR Adapter — Primary OCR engine integration.

Wraps Unlimited-OCR (3B-MoE vision-language model) running as a
persistent SGLang or vLLM server behind an OpenAI-compatible API.

Key design decisions:
  - Single model handles ALL content types (printed, handwriting, tables,
    layout) — no need to route to separate sub-APIs.
  - Output is Markdown with <|det|>category [bbox]<|/det|> region annotations.
  - The adapter parses these annotations into the pipeline's normalized
    Region schema with bounding boxes and confidence scores.
  - Multi-page support uses the "base" image_mode and larger ngram_window.
  - Confidence is estimated from response completeness / token patterns
    since the model doesn't emit per-token log-probs directly in all backends.

Reference: baidu/Unlimited-OCR README and infer.py
"""

from __future__ import annotations

import base64
import json
import logging
import re
import time
from pathlib import Path
from typing import Any

import httpx

from libs.common.schemas import (
    BoundingBox,
    ContentType,
    OCREngine,
    PageExtractionResult,
    PageProfile,
    DocumentProfile,
    Region,
)

from .base import ExtractionAdapter, ExtractionConfig

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# <|det|> Tag Parser
# ═══════════════════════════════════════════════════════════════════════════════

# Matches: <|det|>category [x1,y1,x2,y2]<|/det|>content
DET_TAG_RE = re.compile(
    r"<\|det\|>"
    r"(?P<category>[^<\s\[]+)"           # category name (e.g., "text", "table")
    r"(?:\s*\[(?P<bbox>[^\]]*)\])?"      # optional bounding box [x1,y1,x2,y2]
    r"\s*<\|/det\|>"
    r"(?P<content>.*)",                   # content after the tag
    re.DOTALL,
)

# Map Unlimited-OCR category names to our ContentType enum
CATEGORY_MAP: dict[str, ContentType] = {
    "text": ContentType.PRINTED_TEXT,
    "paragraph": ContentType.PARAGRAPH,
    "title": ContentType.HEADER,
    "header": ContentType.HEADER,
    "footer": ContentType.FOOTER,
    "table": ContentType.TABLE,
    "figure": ContentType.IMAGE,
    "image": ContentType.IMAGE,
    "formula": ContentType.PRINTED_TEXT,
    "caption": ContentType.PRINTED_TEXT,
    "list": ContentType.PRINTED_TEXT,
    "code": ContentType.PRINTED_TEXT,
    "handwriting": ContentType.HANDWRITING,
    "stamp": ContentType.STAMP,
    "signature": ContentType.SIGNATURE,
    "checkbox": ContentType.CHECKBOX,
    "barcode": ContentType.BARCODE,
}


def parse_bbox(bbox_str: str) -> BoundingBox | None:
    """Parse a '[x1,y1,x2,y2]' string into a BoundingBox."""
    try:
        coords = [float(c.strip()) for c in bbox_str.split(",")]
        if len(coords) >= 4:
            x1, y1, x2, y2 = coords[:4]
            return BoundingBox(
                x=min(x1, x2),
                y=min(y1, y2),
                width=abs(x2 - x1),
                height=abs(y2 - y1),
            )
    except (ValueError, TypeError):
        pass
    return None


def parse_det_output(raw_output: str) -> list[Region]:
    """
    Parse Unlimited-OCR's <|det|> annotated Markdown output into Region objects.

    Based on the remove_det() function from the Unlimited-OCR README,
    but extended to preserve bounding boxes and map to our schema.
    """
    regions: list[Region] = []
    current_category: str | None = None
    current_bbox: BoundingBox | None = None
    current_lines: list[str] = []
    reading_order = 0

    for line in raw_output.splitlines():
        line = line.rstrip()
        if not line:
            continue

        match = DET_TAG_RE.match(line)
        if match:
            # Flush previous region
            if current_category is not None and current_lines:
                content_type = CATEGORY_MAP.get(current_category, ContentType.PRINTED_TEXT)
                if content_type != ContentType.IMAGE:  # skip image regions
                    regions.append(
                        Region(
                            content_type=content_type,
                            bbox=current_bbox,
                            content="\n".join(current_lines),
                            confidence=0.0,  # will be set by confidence estimator
                            reading_order=reading_order,
                        )
                    )
                    reading_order += 1

            # Start new region
            current_category = match.group("category").strip().lower()
            bbox_str = match.group("bbox")
            current_bbox = parse_bbox(bbox_str) if bbox_str else None
            content = match.group("content").strip()
            current_lines = [content] if content else []
        else:
            # Continuation line for current region
            current_lines.append(line)

    # Flush last region
    if current_category is not None and current_lines:
        content_type = CATEGORY_MAP.get(current_category, ContentType.PRINTED_TEXT)
        if content_type != ContentType.IMAGE:
            regions.append(
                Region(
                    content_type=content_type,
                    bbox=current_bbox,
                    content="\n".join(current_lines),
                    confidence=0.0,
                    reading_order=reading_order,
                )
            )

    return regions


def extract_plain_text(raw_output: str) -> str:
    """
    Strip all <|det|> markers and return clean text.

    Groups lines belonging to the same block with \\n,
    separates different blocks with \\n\\n.
    Mirrors the remove_det() logic from the Unlimited-OCR README.
    """
    blocks: list[list[str]] = []
    current_block: list[str] | None = None

    for line in raw_output.splitlines():
        line = line.rstrip()
        if not line:
            continue

        match = DET_TAG_RE.match(line)
        if match:
            category = match.group("category").strip().lower()
            content = match.group("content").strip()
            if category == "image":
                continue
            if current_block is not None:
                blocks.append(current_block)
            current_block = [content] if content else []
        else:
            if current_block is None:
                current_block = []
            current_block.append(line)

    if current_block is not None:
        blocks.append(current_block)

    return "\n\n".join("\n".join(b) for b in blocks).strip()


def estimate_confidence(raw_output: str, token_count: int) -> float:
    """
    Heuristic confidence estimation for Unlimited-OCR output.

    Since log-probs may not always be available, we estimate confidence
    based on output characteristics:
      - Length of output relative to expected
      - Presence of structured regions
      - Absence of repetition artifacts (the ngram processor should prevent these)
      - Presence of recognizable patterns (dates, numbers, etc.)
    """
    if not raw_output or token_count == 0:
        return 0.0

    score = 0.7  # Base confidence for any non-empty output

    # Bonus for structured output (detected regions)
    det_count = raw_output.count("<|det|>")
    if det_count > 0:
        score += 0.1

    # Bonus for reasonable length (not truncated or overly short)
    if 50 < token_count < 30000:
        score += 0.05

    # Penalty for repetition (indicates ngram processor failure)
    lines = raw_output.splitlines()
    if len(lines) > 5:
        unique_ratio = len(set(lines)) / len(lines)
        if unique_ratio < 0.5:
            score -= 0.3  # Heavy repetition
        elif unique_ratio > 0.8:
            score += 0.05

    # Penalty for very short output on expected-complex pages
    if token_count < 10:
        score -= 0.2

    return max(0.0, min(1.0, score))


# ═══════════════════════════════════════════════════════════════════════════════
# Unlimited-OCR Adapter
# ═══════════════════════════════════════════════════════════════════════════════


class UnlimitedOCRAdapter(ExtractionAdapter):
    """
    Adapter for Unlimited-OCR running as a SGLang/vLLM server.

    Communicates via the OpenAI-compatible /v1/chat/completions endpoint.
    Supports both single-page (gundam mode) and multi-page (base mode)
    extraction.

    Configuration:
        server_url: URL of the SGLang/vLLM server (default: http://localhost:10000)
        model_name: Served model name (default: Unlimited-OCR)
    """

    engine = OCREngine.UNLIMITED_OCR

    def __init__(
        self,
        server_url: str = "http://localhost:10000",
        model_name: str = "Unlimited-OCR",
        custom_logit_processor: str | None = None,
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self.model_name = model_name
        self.custom_logit_processor = custom_logit_processor
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(1200.0, connect=30.0))

    async def extract_page(
        self,
        image_data: bytes,
        page_profile: PageProfile,
        config: ExtractionConfig | None = None,
    ) -> PageExtractionResult:
        """
        Extract text and regions from a single page image via Unlimited-OCR.

        Uses 'gundam' image_mode for single pages (higher quality, crop_mode).
        """
        cfg = config or ExtractionConfig()
        start_time = time.monotonic()

        # Encode image as base64 data URI
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        image_url = f"data:image/png;base64,{image_b64}"

        # Build OpenAI-compatible request
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "document parsing."},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                }
            ],
            "temperature": cfg.temperature,
            "skip_special_tokens": False,
            "stream": True,
            "images_config": {"image_mode": cfg.image_mode},
        }

        # Add custom logit processor for ngram dedup (SGLang-specific)
        if self.custom_logit_processor:
            payload["custom_logit_processor"] = self.custom_logit_processor
            payload["custom_params"] = {
                "ngram_size": cfg.no_repeat_ngram_size,
                "window_size": cfg.ngram_window,
            }

        # Stream the response
        raw_output, token_count = await self._stream_completion(payload, cfg.timeout_seconds)

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        # Parse the output
        regions = parse_det_output(raw_output)
        plain_text = extract_plain_text(raw_output)
        confidence = estimate_confidence(raw_output, token_count)

        # Set confidence on regions
        for region in regions:
            region.confidence = confidence

        return PageExtractionResult(
            page_num=page_profile.page_num,
            raw_text=plain_text,
            regions=regions,
            confidence=confidence,
            engine=OCREngine.UNLIMITED_OCR,
            latency_ms=elapsed_ms,
            token_count=token_count,
            raw_engine_output=raw_output,
        )

    async def extract_multi_page(
        self,
        images: list[bytes],
        doc_profile: DocumentProfile,
        config: ExtractionConfig | None = None,
    ) -> list[PageExtractionResult]:
        """
        Multi-page extraction using Unlimited-OCR's native multi-page support.

        Uses 'base' image_mode (image_size=1024) and larger ngram_window=1024
        for cross-page context, as specified in the Unlimited-OCR README.
        """
        cfg = config or ExtractionConfig(
            image_mode="base",
            image_size=1024,
            ngram_window=1024,
        )

        start_time = time.monotonic()

        # Encode all images
        image_contents: list[dict[str, Any]] = [
            {"type": "text", "text": "Multi page parsing."}
        ]
        for img_data in images:
            image_b64 = base64.b64encode(img_data).decode("utf-8")
            image_contents.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                }
            )

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": image_contents}],
            "temperature": cfg.temperature,
            "skip_special_tokens": False,
            "stream": True,
            "images_config": {"image_mode": "base"},
        }

        if self.custom_logit_processor:
            payload["custom_logit_processor"] = self.custom_logit_processor
            payload["custom_params"] = {
                "ngram_size": cfg.no_repeat_ngram_size,
                "window_size": 1024,  # Multi-page uses larger window
            }

        raw_output, total_tokens = await self._stream_completion(
            payload, cfg.timeout_seconds
        )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        # For multi-page, the output is one continuous stream.
        # Split into per-page results using page boundary heuristics.
        page_results = self._split_multi_page_output(
            raw_output, total_tokens, elapsed_ms, len(images), doc_profile
        )

        return page_results

    async def health_check(self) -> bool:
        """Check if the SGLang/vLLM server is healthy."""
        try:
            resp = await self._client.get(f"{self.server_url}/health", timeout=5.0)
            return resp.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    def get_capabilities(self) -> list[ContentType]:
        """Unlimited-OCR handles all content types in a single model."""
        return [
            ContentType.PRINTED_TEXT,
            ContentType.HANDWRITING,
            ContentType.TABLE,
            ContentType.FORM,
            ContentType.CHECKBOX,
            ContentType.BARCODE,
            ContentType.SIGNATURE,
            ContentType.STAMP,
            ContentType.HEADER,
            ContentType.FOOTER,
            ContentType.PARAGRAPH,
            ContentType.IMAGE,
        ]

    # ── Internal methods ──────────────────────────────────────────

    async def _stream_completion(
        self, payload: dict[str, Any], timeout: int
    ) -> tuple[str, int]:
        """
        Stream a chat completion request and collect the full response.

        Returns (full_text, token_count).
        """
        chunks: list[str] = []
        token_count = 0

        async with self._client.stream(
            "POST",
            f"{self.server_url}/v1/chat/completions",
            json=payload,
            timeout=timeout,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {}).get("content", "")
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                if delta:
                    token_count += 1
                    chunks.append(delta)

        return "".join(chunks), token_count

    def _split_multi_page_output(
        self,
        raw_output: str,
        total_tokens: int,
        total_ms: int,
        num_pages: int,
        doc_profile: DocumentProfile,
    ) -> list[PageExtractionResult]:
        """
        Split multi-page output into per-page results.

        Heuristic: look for page boundary markers in the output.
        If none found, divide proportionally.
        """
        # Try to split on common page separators
        page_separator_patterns = [
            r"---\s*page\s*\d+\s*---",   # --- Page N ---
            r"\[page\s*\d+\]",            # [Page N]
            r"<\|page_break\|>",          # Custom page break token
        ]

        page_texts: list[str] = []
        remaining = raw_output

        for pattern in page_separator_patterns:
            splits = re.split(pattern, remaining, flags=re.IGNORECASE)
            if len(splits) > 1:
                page_texts = [s.strip() for s in splits if s.strip()]
                break

        # Fallback: if no page markers, treat entire output as one block
        # and assign proportionally to pages
        if not page_texts:
            if num_pages == 1:
                page_texts = [raw_output]
            else:
                # Simple proportional split by lines
                lines = raw_output.splitlines()
                lines_per_page = max(1, len(lines) // num_pages)
                page_texts = []
                for i in range(num_pages):
                    start = i * lines_per_page
                    end = start + lines_per_page if i < num_pages - 1 else len(lines)
                    page_texts.append("\n".join(lines[start:end]))

        # Pad or trim to match expected page count
        while len(page_texts) < num_pages:
            page_texts.append("")
        page_texts = page_texts[:num_pages]

        # Build per-page results
        results = []
        tokens_per_page = max(1, total_tokens // num_pages)
        ms_per_page = max(1, total_ms // num_pages)

        for i, page_text in enumerate(page_texts):
            regions = parse_det_output(page_text)
            plain_text = extract_plain_text(page_text)
            confidence = estimate_confidence(page_text, tokens_per_page)

            for region in regions:
                region.confidence = confidence

            page_profile = (
                doc_profile.pages[i]
                if i < len(doc_profile.pages)
                else PageProfile(page_num=i + 1)
            )

            results.append(
                PageExtractionResult(
                    page_num=page_profile.page_num,
                    raw_text=plain_text,
                    regions=regions,
                    confidence=confidence,
                    engine=OCREngine.UNLIMITED_OCR,
                    latency_ms=ms_per_page,
                    token_count=tokens_per_page,
                    raw_engine_output=page_text,
                )
            )

        return results

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
