"""
Extraction Router — Dispatches pages to the optimal OCR engine.

The router uses the Document Profile (from Phase 2) to decide which
extraction adapter handles each page:

  1. Native-text PDFs → NativePDFExtractor (fast path, no GPU)
  2. Everything else → UnlimitedOCRAdapter (single model handles all)
  3. Future: fallback chains, A/B testing, parallel extraction

Since Unlimited-OCR is a unified model that handles printed text, handwriting,
tables, and layout in a single pass, the routing is simpler than traditional
multi-engine setups. The router still exists for:
  - The native PDF fast path (saves GPU for image-based pages)
  - Future engine additions (Tesseract fallback, Textract comparison)
  - A/B testing new model versions (canary rollout)
  - Per-tenant engine overrides
"""

from __future__ import annotations

import logging
import time
from typing import Any

from libs.common.schemas import (
    DocumentProfile,
    ExtractionResult,
    OCREngine,
    PageExtractionResult,
    PageProfile,
    TenantConfig,
)

from .adapters.base import ExtractionAdapter, ExtractionConfig
from .adapters.unlimited_ocr import UnlimitedOCRAdapter
from .adapters.native_pdf import NativePDFExtractor

logger = logging.getLogger(__name__)


class ExtractionRouter:
    """
    Routes documents to the optimal extraction engine based on their profile.

    Supports:
      - Engine selection per page (native PDF vs. OCR)
      - Multi-page batching for Unlimited-OCR
      - Per-tenant engine overrides
      - Fallback chains on failure
      - Cost and latency tracking
    """

    def __init__(
        self,
        unlimited_ocr_url: str = "http://localhost:10000",
        unlimited_ocr_model: str = "Unlimited-OCR",
        custom_logit_processor: str | None = None,
    ) -> None:
        # Initialize available adapters
        self._adapters: dict[OCREngine, ExtractionAdapter] = {}

        # Primary engine: Unlimited-OCR
        self._unlimited_ocr = UnlimitedOCRAdapter(
            server_url=unlimited_ocr_url,
            model_name=unlimited_ocr_model,
            custom_logit_processor=custom_logit_processor,
        )
        self._adapters[OCREngine.UNLIMITED_OCR] = self._unlimited_ocr

        # Fast path: Native PDF extractor
        self._native_pdf = NativePDFExtractor()
        self._adapters[OCREngine.NATIVE_PDF] = self._native_pdf

    def register_adapter(self, engine: OCREngine, adapter: ExtractionAdapter) -> None:
        """Register an additional extraction adapter (e.g., Tesseract fallback)."""
        self._adapters[engine] = adapter
        logger.info("Registered extraction adapter: %s", engine.value)

    async def extract_document(
        self,
        doc_profile: DocumentProfile,
        page_images: list[bytes],
        pdf_bytes: bytes | None = None,
        tenant_config: TenantConfig | None = None,
        config: ExtractionConfig | None = None,
    ) -> ExtractionResult:
        """
        Extract text and structure from an entire document.

        Decision flow:
          1. If native-text PDF → use NativePDFExtractor (no GPU)
          2. If all pages are image/scanned → use Unlimited-OCR multi-page
          3. If mixed (some native, some scanned) → route per page

        Args:
            doc_profile: Document analysis from the Profiler (Phase 2)
            page_images: List of page images as bytes (for OCR engines)
            pdf_bytes: Original PDF bytes (for native text extraction)
            tenant_config: Tenant-specific settings (engine overrides, etc.)
            config: Extraction configuration overrides

        Returns:
            ExtractionResult with all pages merged
        """
        start_time = time.monotonic()
        cfg = config or ExtractionConfig()

        # Determine which engine to use
        engine = self._select_engine(doc_profile, tenant_config)
        logger.info(
            "Document %s: routing to %s (native_text=%s, pages=%d)",
            doc_profile.doc_id,
            engine.value,
            doc_profile.is_native_text,
            doc_profile.page_count,
        )

        page_results: list[PageExtractionResult] = []

        if engine == OCREngine.NATIVE_PDF and pdf_bytes:
            # ── Fast path: native text extraction ──
            page_results = await self._native_pdf.extract_from_pdf(
                pdf_bytes, doc_profile
            )

            # Check if extraction actually got text (some "digital" PDFs
            # have empty text layers). Fall back to OCR if empty.
            has_text = any(p.raw_text.strip() for p in page_results)
            if not has_text:
                logger.warning(
                    "Document %s: native PDF extraction returned empty text, "
                    "falling back to Unlimited-OCR",
                    doc_profile.doc_id,
                )
                engine = OCREngine.UNLIMITED_OCR
                page_results = []  # Reset to trigger OCR below

        if engine == OCREngine.UNLIMITED_OCR and page_images:
            # ── OCR path: Unlimited-OCR ──
            if len(page_images) == 1:
                # Single-page: use gundam mode for higher quality
                single_cfg = ExtractionConfig(
                    image_mode="gundam",
                    image_size=640,
                    ngram_window=128,
                    max_length=cfg.max_length,
                    temperature=cfg.temperature,
                    timeout_seconds=cfg.timeout_seconds,
                )
                page_profile = (
                    doc_profile.pages[0]
                    if doc_profile.pages
                    else PageProfile(page_num=1)
                )
                result = await self._unlimited_ocr.extract_page(
                    page_images[0], page_profile, single_cfg
                )
                page_results = [result]
            else:
                # Multi-page: use base mode with larger ngram window
                multi_cfg = ExtractionConfig(
                    image_mode="base",
                    image_size=1024,
                    ngram_window=1024,
                    max_length=cfg.max_length,
                    temperature=cfg.temperature,
                    timeout_seconds=cfg.timeout_seconds,
                )
                page_results = await self._unlimited_ocr.extract_multi_page(
                    page_images, doc_profile, multi_cfg
                )

        elif engine == OCREngine.UNLIMITED_OCR and not page_images:
            logger.error(
                "Document %s: OCR engine selected but no page images provided",
                doc_profile.doc_id,
            )

        # ── Mixed document handling ──
        # If some pages are native text and others are scanned, handle them
        # separately (optimization for mixed documents)
        if self._is_mixed_document(doc_profile) and pdf_bytes and page_images:
            page_results = await self._extract_mixed(
                doc_profile, page_images, pdf_bytes, cfg
            )

        # Build combined result
        total_ms = int((time.monotonic() - start_time) * 1000)
        total_tokens = sum(p.token_count for p in page_results)
        overall_confidence = (
            sum(p.confidence for p in page_results) / len(page_results)
            if page_results
            else 0.0
        )

        return ExtractionResult(
            doc_id=doc_profile.doc_id,
            tenant_id=doc_profile.tenant_id,
            pages=page_results,
            overall_confidence=overall_confidence,
            primary_engine=engine,
            total_latency_ms=total_ms,
            total_tokens=total_tokens,
            metadata={
                "engine_used": engine.value,
                "page_count": len(page_results),
                "config": {
                    "image_mode": cfg.image_mode,
                    "ngram_window": cfg.ngram_window,
                },
            },
        )

    async def health_check_all(self) -> dict[str, bool]:
        """Check health of all registered adapters."""
        results = {}
        for engine, adapter in self._adapters.items():
            results[engine.value] = await adapter.health_check()
        return results

    # ── Private helpers ──────────────────────────────────────────

    def _select_engine(
        self,
        doc_profile: DocumentProfile,
        tenant_config: TenantConfig | None = None,
    ) -> OCREngine:
        """
        Select the optimal engine for a document.

        Priority:
          1. Tenant override (if configured)
          2. Native PDF path (if document has embedded text)
          3. Default: Unlimited-OCR
        """
        # Check tenant override
        if tenant_config and tenant_config.features.ocr_engine != OCREngine.UNLIMITED_OCR:
            override = tenant_config.features.ocr_engine
            if override in self._adapters:
                return override
            logger.warning(
                "Tenant %s requested engine %s but it's not available, "
                "falling back to Unlimited-OCR",
                tenant_config.tenant_id,
                override.value,
            )

        # Fast path for digital PDFs
        if doc_profile.is_native_text:
            return OCREngine.NATIVE_PDF

        # Default: Unlimited-OCR handles everything
        return OCREngine.UNLIMITED_OCR

    def _is_mixed_document(self, doc_profile: DocumentProfile) -> bool:
        """Check if a document has both native-text and image pages."""
        if not doc_profile.pages:
            return False
        has_native = any(p.is_native_text for p in doc_profile.pages)
        has_image = any(not p.is_native_text for p in doc_profile.pages)
        return has_native and has_image

    async def _extract_mixed(
        self,
        doc_profile: DocumentProfile,
        page_images: list[bytes],
        pdf_bytes: bytes,
        config: ExtractionConfig,
    ) -> list[PageExtractionResult]:
        """
        Handle mixed documents (some pages native text, some scanned).

        Routes each page to the appropriate engine individually.
        """
        import fitz

        results: list[PageExtractionResult] = []
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        for i, page_profile in enumerate(doc_profile.pages):
            if page_profile.is_native_text:
                # Native text extraction for this page
                page = doc[i]
                text = page.get_text("text")
                results.append(
                    PageExtractionResult(
                        page_num=page_profile.page_num,
                        raw_text=text.strip(),
                        regions=[],
                        confidence=0.99,
                        engine=OCREngine.NATIVE_PDF,
                        latency_ms=1,
                        token_count=len(text.split()),
                    )
                )
            else:
                # OCR for this page
                if i < len(page_images):
                    single_cfg = ExtractionConfig(
                        image_mode="gundam",
                        image_size=640,
                        ngram_window=128,
                        max_length=config.max_length,
                        temperature=config.temperature,
                        timeout_seconds=config.timeout_seconds,
                    )
                    result = await self._unlimited_ocr.extract_page(
                        page_images[i], page_profile, single_cfg
                    )
                    results.append(result)
                else:
                    results.append(
                        PageExtractionResult(
                            page_num=page_profile.page_num,
                            raw_text="",
                            confidence=0.0,
                            engine=OCREngine.UNLIMITED_OCR,
                        )
                    )

        doc.close()
        return results

    async def close(self) -> None:
        """Clean up all adapters."""
        for adapter in self._adapters.values():
            if hasattr(adapter, "close"):
                await adapter.close()
