"""
Pipeline Orchestrator — Phase 9.

Wires all pipeline stages together and manages the document lifecycle:

  Ingestion → Profiling → Pre-processing → OCR/Extraction →
  Normalization → Information Extraction → Validation → Decision → Delivery

Features:
  - Stage-level execution with artifact persistence
  - Job State Machine transitions with validation
  - Stage-level reprocessing (not full re-ingestion)
  - Error handling with retry support
  - Metrics tracking (latency, token usage, cost)

In production, each stage is a message-queue consumer; this orchestrator
shows the synchronous pipeline for development/testing.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from libs.common.schemas import (
    DecisionOutcome,
    DocumentJob,
    DocumentProfile,
    ExtractionOutput,
    ExtractionResult,
    NormalizedOutput,
    SemanticChunkingResult,
    TenantConfig,
    TrustScore,
)
from libs.common.job_states import JobState, TERMINAL_STATES
from libs.common.chunker import SemanticChunker
from services.ingestion.service import OfficeDocumentConverter

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates the full document processing pipeline.

    This is the synchronous/development orchestrator. In production,
    replace with async message-queue orchestration (Kafka/SQS consumers)
    or a workflow engine (Temporal, Step Functions).
    """

    def __init__(
        self,
        ingestion_service: Any = None,
        profiler_service: Any = None,
        ocr_router: Any = None,
        normalizer_service: Any = None,
        extractor_service: Any = None,
        validator_service: Any = None,
        decision_engine: Any = None,
        delivery_service: Any = None,
    ) -> None:
        self.ingestion = ingestion_service
        self.profiler = profiler_service
        self.ocr_router = ocr_router
        self.normalizer = normalizer_service
        self.extractor = extractor_service
        self.validator = validator_service
        self.decision = decision_engine
        self.delivery = delivery_service

        # Metrics
        self._stage_metrics: list[dict[str, Any]] = []

    async def process_document(
        self,
        job: DocumentJob,
        file_bytes: bytes,
        tenant_config: TenantConfig,
        start_from: JobState | None = None,
    ) -> DocumentJob:
        """
        Run the full pipeline on a document job.

        If start_from is specified, skip to that stage (for reprocessing).
        """
        pipeline_start = time.monotonic()

        # Handle Office conversion (.docx, .pptx, etc.) seamlessly before stage pipeline
        if OfficeDocumentConverter.is_office_document(job.content_type, job.original_filename):
            try:
                converted_pdf, engine = OfficeDocumentConverter.convert_to_pdf(file_bytes, job.original_filename)
                file_bytes = converted_pdf
                job.content_type = "application/pdf"
                logger.info("Office document '%s' converted to PDF via %s (%d bytes)", job.original_filename, engine, len(file_bytes))
            except Exception as e:
                logger.warning("Office conversion failed: %s; proceeding with original bytes", e)

        try:
            # Determine starting stage
            stages = self._build_stage_sequence(start_from or job.state)

            for stage_func, target_state in stages:
                if job.state in TERMINAL_STATES:
                    break

                stage_start = time.monotonic()

                try:
                    await stage_func(job, file_bytes, tenant_config)
                except Exception as e:
                    logger.error(
                        "Stage %s failed for job %s: %s",
                        target_state.value,
                        job.job_id,
                        e,
                    )
                    job.error_message = f"Stage {target_state.value} failed: {e}"
                    job.transition_to(JobState.ERROR, str(e))
                    break

                stage_ms = int((time.monotonic() - stage_start) * 1000)
                self._stage_metrics.append(
                    {
                        "job_id": job.job_id,
                        "stage": target_state.value,
                        "latency_ms": stage_ms,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

        except Exception as e:
            logger.error("Pipeline failed for job %s: %s", job.job_id, e)
            job.error_message = str(e)
            if job.state not in TERMINAL_STATES:
                job.transition_to(JobState.ERROR, str(e))

        total_ms = int((time.monotonic() - pipeline_start) * 1000)
        logger.info(
            "Pipeline complete for job %s: state=%s in %dms",
            job.job_id,
            job.state.value,
            total_ms,
        )

        return job

    def _build_stage_sequence(
        self, start: JobState
    ) -> list[tuple[Any, JobState]]:
        """Build the ordered list of stages to execute."""
        all_stages = [
            (self._stage_profile, JobState.PROFILING),
            (self._stage_preprocess, JobState.PREPROCESSING),
            (self._stage_ocr, JobState.OCR_EXTRACTION),
            (self._stage_normalize, JobState.NORMALIZING),
            (self._stage_extract, JobState.VALIDATING),
            (self._stage_validate, JobState.DECISION),
            (self._stage_decide, JobState.DELIVERY_PENDING),
            (self._stage_deliver, JobState.COMPLETED),
        ]

        # Find the starting index
        start_map = {
            JobState.PROFILING: 0,
            JobState.PREPROCESSING: 1,
            JobState.OCR_EXTRACTION: 2,
            JobState.NORMALIZING: 3,
            JobState.VALIDATING: 4,
            JobState.DECISION: 5,
            JobState.DELIVERY_PENDING: 6,
        }

        start_idx = start_map.get(start, 0)
        return all_stages[start_idx:]

    # ── Stage Implementations ────────────────────────────────────────

    async def _stage_profile(
        self, job: DocumentJob, file_bytes: bytes, tenant: TenantConfig
    ) -> None:
        """Stage 2: Document Profiling."""
        if not self.profiler:
            logger.warning("Profiler not configured, skipping")
            job.transition_to(JobState.PREPROCESSING, "Profiler skipped")
            return

        if job.content_type == "application/pdf":
            profile = await self.profiler.profile_pdf(
                file_bytes, tenant.tenant_id, job.doc_id
            )
        else:
            profile = await self.profiler.profile_image(
                file_bytes, tenant.tenant_id, job.doc_id
            )

        job.profile = profile
        job.page_count = profile.page_count
        job.transition_to(JobState.PREPROCESSING, "Profiling complete")

    async def _stage_preprocess(
        self, job: DocumentJob, file_bytes: bytes, tenant: TenantConfig
    ) -> None:
        """Stage 3: Pre-processing & Layout."""
        # Pre-processing: convert PDF pages to images for OCR
        # For native-text PDFs, this is skipped by the OCR router
        job.transition_to(JobState.OCR_EXTRACTION, "Pre-processing complete")

    async def _stage_ocr(
        self, job: DocumentJob, file_bytes: bytes, tenant: TenantConfig
    ) -> None:
        """Stage 4: OCR / Extraction via Unlimited-OCR."""
        if not self.ocr_router:
            logger.warning("OCR router not configured, skipping")
            job.transition_to(JobState.NORMALIZING, "OCR skipped")
            return

        profile = job.profile or DocumentProfile(
            doc_id=job.doc_id,
            tenant_id=tenant.tenant_id,
            page_count=1,
        )

        # Convert PDF to page images for OCR
        page_images: list[bytes] = []
        pdf_bytes: bytes | None = None

        if job.content_type == "application/pdf":
            pdf_bytes = file_bytes
            page_images = self._pdf_to_images(file_bytes)
        else:
            page_images = [file_bytes]

        result = await self.ocr_router.extract_document(
            doc_profile=profile,
            page_images=page_images,
            pdf_bytes=pdf_bytes,
            tenant_config=tenant,
        )

        job.extraction_result = result
        job.transition_to(JobState.NORMALIZING, "OCR extraction complete")

    async def _stage_normalize(
        self, job: DocumentJob, file_bytes: bytes, tenant: TenantConfig
    ) -> None:
        """Stage 5: Normalization."""
        if not self.normalizer or not job.extraction_result:
            job.transition_to(JobState.VALIDATING, "Normalization skipped")
            return

        normalized = await self.normalizer.normalize(job.extraction_result)
        job.normalized_output = normalized
        job.transition_to(JobState.VALIDATING, "Normalization complete")

    async def _stage_extract(
        self, job: DocumentJob, file_bytes: bytes, tenant: TenantConfig
    ) -> None:
        """Stage 6: Information Extraction (3-layer) & Optional Semantic Chunking."""
        if not self.extractor or not job.normalized_output:
            job.transition_to(JobState.DECISION, "Extraction skipped")
            return

        doc_type = (
            job.profile.doc_type_prediction
            if job.profile
            else None
        )

        extraction_output = await self.extractor.extract(
            normalized=job.normalized_output,
            doc_type=doc_type,
            tenant_config=tenant,
        )

        # Compute semantic chunking if requested
        if job.chunking_requested == "semantic":
            all_regions = []
            full_text = ""
            if job.extraction_result:
                full_text = job.extraction_result.full_text
                for p in job.extraction_result.pages:
                    for r in p.regions:
                        r.metadata["page_num"] = p.page_num
                        all_regions.append(r)
            elif job.normalized_output:
                full_text = job.normalized_output.normalized_text

            chunker = SemanticChunker(default_chunk_size=job.chunk_size_target or 1000)
            chunk_res = chunker.chunk_document(
                full_text=full_text,
                regions=all_regions,
                chunk_size=job.chunk_size_target,
            )
            job.semantic_chunking = chunk_res
            extraction_output.semantic_chunking = chunk_res

        job.extraction_output = extraction_output
        job.transition_to(JobState.DECISION, "Information extraction complete")

    async def _stage_validate(
        self, job: DocumentJob, file_bytes: bytes, tenant: TenantConfig
    ) -> None:
        """Stage 7: Validation & Trust Scoring."""
        if not self.validator or not job.extraction_output:
            job.transition_to(JobState.DELIVERY_PENDING, "Validation skipped")
            return

        trust_score = await self.validator.validate(job.extraction_output)
        job.trust_score = trust_score
        # Don't transition here — the decision engine handles the transition

    async def _stage_decide(
        self, job: DocumentJob, file_bytes: bytes, tenant: TenantConfig
    ) -> None:
        """Stage 8: Decision Engine."""
        if not self.decision or not job.extraction_output or not job.trust_score:
            job.transition_to(JobState.DELIVERY_PENDING, "Decision skipped")
            return

        decision = await self.decision.decide(
            extraction=job.extraction_output,
            trust_score=job.trust_score,
            tenant_config=tenant,
        )
        job.decision = decision

        if decision.outcome == DecisionOutcome.AUTO_APPROVED:
            job.transition_to(JobState.DELIVERY_PENDING, "Auto-approved")
        elif decision.outcome == DecisionOutcome.HUMAN_REVIEW:
            job.transition_to(JobState.REVIEW_REQUIRED, decision.reason)
        elif decision.outcome == DecisionOutcome.REPROCESS:
            target = decision.reprocess_target_stage or JobState.OCR_EXTRACTION
            job.transition_to(target, f"Reprocessing from {target.value}")
            job.retry_count += 1
        elif decision.outcome in (DecisionOutcome.REJECTED, DecisionOutcome.QUARANTINED):
            job.transition_to(JobState.SECURITY_REJECTED, decision.reason)

    async def _stage_deliver(
        self, job: DocumentJob, file_bytes: bytes, tenant: TenantConfig
    ) -> None:
        """Stage 9: Output Delivery."""
        if not self.delivery or not job.extraction_output or not job.trust_score or not job.decision:
            job.transition_to(JobState.COMPLETED, "Delivery skipped")
            return

        events = await self.delivery.deliver(
            extraction=job.extraction_output,
            trust_score=job.trust_score,
            decision=job.decision,
        )

        all_success = all(e.success for e in events) if events else True
        if all_success:
            job.transition_to(JobState.COMPLETED, "Delivery complete")
        else:
            job.transition_to(JobState.DELIVERY_FAILED, "One or more deliveries failed")

    # ── Helpers ──────────────────────────────────────────────────────

    def _pdf_to_images(self, pdf_bytes: bytes) -> list[bytes]:
        """Convert PDF pages to PNG images for OCR."""
        import fitz
        import io

        images: list[bytes] = []
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        mat = fitz.Matrix(300 / 72, 300 / 72)  # 300 DPI

        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            images.append(img_bytes)

        doc.close()
        return images

    def get_metrics(self) -> list[dict[str, Any]]:
        """Return collected stage metrics."""
        return self._stage_metrics
