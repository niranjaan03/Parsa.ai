"""
Base Extraction Adapter — Abstract interface that all OCR engines implement.

Every extraction engine (Unlimited-OCR, Tesseract, Textract, Azure Doc
Intelligence, etc.) must implement this interface. This decouples the
pipeline from any specific OCR vendor and enables:
  - Hot-swapping engines per tenant / doc type
  - A/B testing / canary rollout of new engines
  - Fallback chains (primary fails → try secondary)
  - Parallel extraction with consensus voting
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from libs.common.schemas import (
    BoundingBox,
    ContentType,
    DocumentProfile,
    OCREngine,
    PageExtractionResult,
    PageProfile,
    Region,
)


@dataclass
class ExtractionConfig:
    """Configuration passed to the extraction adapter per request."""

    # Image processing
    image_mode: str = "gundam"  # "gundam" (single-page) or "base" (multi-page)
    image_size: int = 640       # 640 for gundam, 1024 for base
    dpi: int = 300

    # Model parameters
    max_length: int = 32768
    no_repeat_ngram_size: int = 35
    ngram_window: int = 128     # 128 for single-page, 1024 for multi-page
    temperature: float = 0.0

    # Timeout and retry
    timeout_seconds: int = 1200
    max_retries: int = 3

    # Extra engine-specific config
    extra: dict[str, Any] = field(default_factory=dict)


class ExtractionAdapter(ABC):
    """
    Abstract base class for OCR extraction engines.

    Subclasses must implement:
      - extract_page(): Extract from a single page image
      - health_check(): Verify the engine is operational

    Optionally override:
      - extract_multi_page(): Optimized multi-page extraction
      - get_capabilities(): Report what content types the engine handles
    """

    engine: OCREngine

    @abstractmethod
    async def extract_page(
        self,
        image_data: bytes,
        page_profile: PageProfile,
        config: ExtractionConfig | None = None,
    ) -> PageExtractionResult:
        """
        Extract text and regions from a single page image.

        Args:
            image_data: Raw image bytes (PNG, JPEG, etc.)
            page_profile: Analysis of this page from the profiler
            config: Engine-specific configuration overrides

        Returns:
            PageExtractionResult with text, regions, confidence, and timing
        """
        ...

    async def extract_multi_page(
        self,
        images: list[bytes],
        doc_profile: DocumentProfile,
        config: ExtractionConfig | None = None,
    ) -> list[PageExtractionResult]:
        """
        Extract from multiple pages. Default: sequential single-page calls.

        Override for engines that support native multi-page batching
        (e.g., Unlimited-OCR's infer_multi).
        """
        results = []
        for i, img_data in enumerate(images):
            page_profile = (
                doc_profile.pages[i]
                if i < len(doc_profile.pages)
                else PageProfile(page_num=i + 1)
            )
            result = await self.extract_page(img_data, page_profile, config)
            results.append(result)
        return results

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the engine is operational and ready."""
        ...

    def get_capabilities(self) -> list[ContentType]:
        """Content types this engine can handle. Override per engine."""
        return [ContentType.PRINTED_TEXT]

    def get_engine_name(self) -> str:
        return self.engine.value
