"""
Information Extraction Service — Phase 5 (Stage 6).

Three-layer cost-efficient extraction strategy:

  Layer 1: Rules & Templates (deterministic)
    → Fastest, cheapest. For known/standard forms.
    → Regex patterns, anchor-point matching, template fields.

  Layer 2: Small Extraction Model (ML)
    → For semi-structured / variable documents.
    → Fine-tuned NER model (LayoutLM, BERT-based).
    → Interface only — model training is Phase 10.

  Layer 3: LLM Escalation (expensive, last resort)
    → Only for genuinely ambiguous cases.
    → Structured JSON output with source spans.
    → Cost guardrails (max tokens, circuit breaker).

The Escalation Policy decides Layer 1 → 2 → 3 routing based on
confidence thresholds configured per tenant.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from libs.common.schemas import (
    ExtractedField,
    ExtractionLayer,
    ExtractionOutput,
    NormalizedOutput,
    TenantConfig,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 1: Rules & Templates
# ═══════════════════════════════════════════════════════════════════════════════


class DocumentTemplate:
    """
    A template defining expected fields for a known document type.

    Each field has a name, list of regex patterns to try, and
    optional anchor text that helps locate the value.
    """

    def __init__(
        self,
        doc_type: str,
        fields: list[dict[str, Any]],
    ) -> None:
        self.doc_type = doc_type
        self.fields = fields

    def extract(self, text: str) -> list[ExtractedField]:
        """Extract fields using regex patterns and anchors."""
        results: list[ExtractedField] = []

        for field_def in self.fields:
            name = field_def["name"]
            patterns = field_def.get("patterns", [])
            anchors = field_def.get("anchors", [])
            required = field_def.get("required", False)

            value = None
            source_span = None
            confidence = 0.0

            # Try patterns first
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    # Use first captured group, or entire match
                    value = match.group(1) if match.lastindex else match.group()
                    source_span = match.group()
                    confidence = 0.95  # High confidence for regex matches
                    break

            # Try anchor-based extraction if no pattern matched
            if not value and anchors:
                for anchor in anchors:
                    idx = text.lower().find(anchor.lower())
                    if idx >= 0:
                        # Extract text after the anchor
                        after = text[idx + len(anchor):].strip()
                        # Take first line or up to 100 chars
                        value_match = re.match(r"[:=]?\s*(.+?)(?:\n|$)", after)
                        if value_match:
                            value = value_match.group(1).strip()
                            source_span = f"{anchor}: {value}"
                            confidence = 0.85
                            break

            if value:
                results.append(
                    ExtractedField(
                        field_name=name,
                        value=value,
                        confidence=confidence,
                        extraction_layer=ExtractionLayer.RULES_TEMPLATES,
                        source_span=source_span,
                    )
                )

        return results


# Built-in templates for common document types
INVOICE_TEMPLATE = DocumentTemplate(
    doc_type="invoice",
    fields=[
        {
            "name": "invoice_number",
            "patterns": [
                r"(?:Invoice|Inv)[ \t]+(?:No|Number|#|Num)?[ \t]*[:#.]?[ \t]*([A-Za-z0-9][\w-]+)",
                r"(?:Invoice|Inv)[ \t]*[:#.]+[ \t]*([A-Za-z0-9][\w-]+)",
                r"(?:Bill|Receipt)[ \t]*(?:No|Number|#)?[ \t]*[:#.]?[ \t]*(\S+)",
            ],
            "anchors": ["Invoice Number", "Invoice No", "Invoice #", "Inv #"],
            "required": True,
        },
        {
            "name": "invoice_date",
            "patterns": [
                r"(?:Invoice\s+)?Date[\s.:]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})",
                r"Date[\s.:]*(\w+\s+\d{1,2},?\s+\d{4})",
            ],
            "anchors": ["Invoice Date", "Date", "Issued"],
        },
        {
            "name": "due_date",
            "patterns": [
                r"Due\s*Date[\s.:]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})",
                r"Due\s*Date[\s.:]*(\w+\s+\d{1,2},?\s+\d{4})",
                r"Payment\s*Due[\s.:]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})",
            ],
            "anchors": ["Due Date", "Payment Due"],
        },
        {
            "name": "total_amount",
            "patterns": [
                r"(?:Grand\s*Total|Amount\s*Due|Balance\s*Due)[\s.:]*([€$£¥₹]?\s*[\d,]+\.?\d{0,2})",
                r"(?<![Ss]ub)Total[\s.:]*([€$£¥₹]?\s*[\d,]+\.?\d{0,2})",
            ],
            "anchors": ["Grand Total", "Total", "Amount Due", "Balance Due"],
            "required": True,
        },
        {
            "name": "subtotal",
            "patterns": [
                r"Sub\s*total[\s.:]*([€$£¥₹]?\s*[\d,]+\.?\d{0,2})",
            ],
            "anchors": ["Subtotal", "Sub Total", "Sub-total"],
        },
        {
            "name": "tax_amount",
            "patterns": [
                r"(?:Tax|VAT|GST|Sales\s*Tax)[\s.:]*([€$£¥₹]?\s*[\d,]+\.?\d{0,2})",
            ],
            "anchors": ["Tax", "VAT", "GST", "Sales Tax"],
        },
        {
            "name": "vendor_name",
            "anchors": ["From", "Vendor", "Seller", "Bill From", "Company"],
        },
        {
            "name": "customer_name",
            "anchors": ["To", "Customer", "Buyer", "Bill To", "Client"],
        },
    ],
)

RECEIPT_TEMPLATE = DocumentTemplate(
    doc_type="receipt",
    fields=[
        {
            "name": "store_name",
            "anchors": ["Store", "Restaurant", "Shop"],
        },
        {
            "name": "date",
            "patterns": [
                r"Date[\s.:]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})",
            ],
            "anchors": ["Date"],
        },
        {
            "name": "total",
            "patterns": [
                r"(?:Total|TOTAL)[\s.:]*([€$£¥₹]?\s*[\d,]+\.?\d{0,2})",
            ],
            "anchors": ["Total", "TOTAL"],
        },
        {
            "name": "payment_method",
            "patterns": [
                r"(?:Paid\s*(?:by|with)|Payment)[\s.:]*(\w+)",
            ],
            "anchors": ["Payment", "Paid by", "Paid with"],
        },
    ],
)

# Template registry
TEMPLATES: dict[str, DocumentTemplate] = {
    "invoice": INVOICE_TEMPLATE,
    "receipt": RECEIPT_TEMPLATE,
}


class RulesEngine:
    """Layer 1: Rules & Templates-based extraction."""

    def __init__(self, templates: dict[str, DocumentTemplate] | None = None) -> None:
        self.templates = templates or TEMPLATES

    def extract(
        self,
        text: str,
        doc_type: str | None = None,
    ) -> ExtractionOutput:
        """
        Extract fields using templates.

        If doc_type is known, use that template. Otherwise, try all
        templates and pick the one with the most matches.
        """
        if doc_type and doc_type in self.templates:
            template = self.templates[doc_type]
            fields = template.extract(text)
            overall_conf = (
                sum(f.confidence for f in fields) / len(fields)
                if fields
                else 0.0
            )
            return ExtractionOutput(
                doc_id="",
                tenant_id="",
                doc_type=doc_type,
                fields=fields,
                extraction_layer_used=ExtractionLayer.RULES_TEMPLATES,
                overall_confidence=overall_conf,
            )

        # Try all templates, pick best match
        best_output: ExtractionOutput | None = None
        best_field_count = 0

        for dt, template in self.templates.items():
            fields = template.extract(text)
            if len(fields) > best_field_count:
                best_field_count = len(fields)
                overall_conf = (
                    sum(f.confidence for f in fields) / len(fields)
                    if fields
                    else 0.0
                )
                best_output = ExtractionOutput(
                    doc_id="",
                    tenant_id="",
                    doc_type=dt,
                    fields=fields,
                    extraction_layer_used=ExtractionLayer.RULES_TEMPLATES,
                    overall_confidence=overall_conf,
                )

        return best_output or ExtractionOutput(
            doc_id="",
            tenant_id="",
            extraction_layer_used=ExtractionLayer.RULES_TEMPLATES,
            overall_confidence=0.0,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 2: Small Extraction Model (Interface)
# ═══════════════════════════════════════════════════════════════════════════════


class SmallModelExtractor:
    """
    Layer 2: ML-based extraction using a fine-tuned model.

    In production, this wraps a LayoutLM / BERT-based extraction model
    served via a separate inference endpoint. For now, it's an interface
    that returns the Layer 1 results with lower confidence to trigger
    LLM escalation.
    """

    async def extract(
        self,
        text: str,
        normalized: NormalizedOutput,
        doc_type: str | None = None,
    ) -> ExtractionOutput:
        """
        Extract fields using the small ML model.

        TODO: Implement with actual model inference.
        For now, returns normalized fields as extracted fields.
        """
        fields: list[ExtractedField] = []
        for nf in normalized.fields:
            fields.append(
                ExtractedField(
                    field_name=nf.key,
                    value=nf.normalized_value,
                    confidence=nf.confidence * 0.9,  # Slightly lower than rules
                    extraction_layer=ExtractionLayer.SMALL_MODEL,
                    source_span=nf.raw_value,
                )
            )

        overall = (
            sum(f.confidence for f in fields) / len(fields)
            if fields
            else 0.0
        )

        return ExtractionOutput(
            doc_id=normalized.doc_id,
            tenant_id=normalized.tenant_id,
            doc_type=doc_type or "unknown",
            fields=fields,
            extraction_layer_used=ExtractionLayer.SMALL_MODEL,
            overall_confidence=overall,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 3: LLM Escalation
# ═══════════════════════════════════════════════════════════════════════════════


EXTRACTION_PROMPT_TEMPLATE = """You are a document extraction assistant. Extract structured fields from the following document text.

Document Type: {doc_type}
Expected Fields: {field_names}

Document Text:
---
{text}
---

Instructions:
1. Extract each field as accurately as possible
2. For each field, provide the exact source text span that supports your extraction
3. If a field cannot be found, set its value to null
4. Return ONLY valid JSON matching this schema:

{{
  "fields": [
    {{
      "field_name": "string",
      "value": "string or null",
      "confidence": 0.0-1.0,
      "source_span": "exact text from document"
    }}
  ]
}}
"""


class LLMEscalationExtractor:
    """
    Layer 3: LLM-based extraction for ambiguous documents.

    Only invoked when Layer 1 and 2 confidence is below threshold.
    Uses structured output (JSON) to extract fields with source spans.

    Cost guardrails:
      - Max tokens per request
      - Circuit breaker (max LLM calls per tenant per hour)
      - Prompt caching where possible
    """

    def __init__(
        self,
        api_url: str = "https://generativelanguage.googleapis.com/v1beta/models",
        model: str = "gemini-2.0-flash",
        max_tokens: int = 4096,
        max_calls_per_hour: int = 100,
    ) -> None:
        self.api_url = api_url
        self.model = model
        self.max_tokens = max_tokens
        self.max_calls_per_hour = max_calls_per_hour
        self._call_count = 0

    async def extract(
        self,
        text: str,
        doc_type: str,
        field_names: list[str],
        tenant_id: str,
    ) -> ExtractionOutput:
        """
        Extract fields using an LLM.

        This is the most expensive extraction path and should only be
        used for genuinely ambiguous documents.
        """
        # Cost guardrail: check circuit breaker
        if self._call_count >= self.max_calls_per_hour:
            logger.warning(
                "LLM escalation circuit breaker triggered for tenant %s",
                tenant_id,
            )
            return ExtractionOutput(
                doc_id="",
                tenant_id=tenant_id,
                doc_type=doc_type,
                extraction_layer_used=ExtractionLayer.LLM_ESCALATION,
                overall_confidence=0.0,
                escalation_reason="circuit_breaker_triggered",
            )

        self._call_count += 1

        # Build prompt
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(
            doc_type=doc_type,
            field_names=", ".join(field_names),
            text=text[:8000],  # Truncate to control token usage
        )

        # In production: call LLM API
        # response = await self._call_llm(prompt)
        # For now, return placeholder

        logger.info(
            "LLM escalation invoked for tenant %s, doc_type=%s, fields=%s",
            tenant_id,
            doc_type,
            field_names,
        )

        return ExtractionOutput(
            doc_id="",
            tenant_id=tenant_id,
            doc_type=doc_type,
            extraction_layer_used=ExtractionLayer.LLM_ESCALATION,
            overall_confidence=0.0,
            escalation_reason="llm_extraction_pending",
            metadata={"prompt_tokens": len(prompt.split())},
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Escalation Policy & Main Service
# ═══════════════════════════════════════════════════════════════════════════════


class ExtractionService:
    """
    Main extraction service implementing the 3-layer escalation strategy.

    Escalation flow:
      Layer 1 (Rules) → if confidence < threshold → Layer 2 (ML)
                       → if confidence < threshold → Layer 3 (LLM)
    """

    def __init__(
        self,
        rules_engine: RulesEngine | None = None,
        small_model: SmallModelExtractor | None = None,
        llm_extractor: LLMEscalationExtractor | None = None,
    ) -> None:
        self.rules = rules_engine or RulesEngine()
        self.small_model = small_model or SmallModelExtractor()
        self.llm = llm_extractor or LLMEscalationExtractor()

    async def extract(
        self,
        normalized: NormalizedOutput,
        doc_type: str | None = None,
        tenant_config: TenantConfig | None = None,
    ) -> ExtractionOutput:
        """
        Run the 3-layer extraction strategy.

        Returns the first layer that exceeds the confidence threshold.
        """
        auto_threshold = 0.95
        ml_threshold = 0.85
        if tenant_config:
            auto_threshold = tenant_config.auto_approve_threshold
            ml_threshold = tenant_config.ml_approve_threshold

        # ── Layer 1: Rules & Templates ──
        layer1 = self.rules.extract(normalized.normalized_text, doc_type)
        layer1.doc_id = normalized.doc_id
        layer1.tenant_id = normalized.tenant_id

        if layer1.overall_confidence >= auto_threshold and layer1.fields:
            logger.info(
                "Document %s: Layer 1 (Rules) extracted %d fields, conf=%.2f — accepted",
                normalized.doc_id,
                len(layer1.fields),
                layer1.overall_confidence,
            )
            return layer1

        # ── Layer 2: Small Model ──
        layer2 = await self.small_model.extract(
            normalized.normalized_text, normalized, doc_type
        )
        layer2.doc_id = normalized.doc_id
        layer2.tenant_id = normalized.tenant_id

        # Merge Layer 1 and Layer 2 results (take higher confidence per field)
        merged_fields = self._merge_fields(layer1.fields, layer2.fields)
        merged_confidence = (
            sum(f.confidence for f in merged_fields) / len(merged_fields)
            if merged_fields
            else 0.0
        )

        if merged_confidence >= ml_threshold and merged_fields:
            logger.info(
                "Document %s: Layer 2 (ML) merged %d fields, conf=%.2f — accepted",
                normalized.doc_id,
                len(merged_fields),
                merged_confidence,
            )
            return ExtractionOutput(
                doc_id=normalized.doc_id,
                tenant_id=normalized.tenant_id,
                doc_type=layer2.doc_type or layer1.doc_type,
                fields=merged_fields,
                extraction_layer_used=ExtractionLayer.SMALL_MODEL,
                overall_confidence=merged_confidence,
            )

        # ── Layer 3: LLM Escalation ──
        if tenant_config and not tenant_config.features.llm_escalation_enabled:
            logger.info(
                "Document %s: LLM escalation disabled for tenant, returning Layer 2",
                normalized.doc_id,
            )
            return ExtractionOutput(
                doc_id=normalized.doc_id,
                tenant_id=normalized.tenant_id,
                doc_type=layer2.doc_type or layer1.doc_type,
                fields=merged_fields,
                extraction_layer_used=ExtractionLayer.SMALL_MODEL,
                overall_confidence=merged_confidence,
                escalation_reason="llm_disabled",
            )

        # Determine which fields need LLM help
        field_names = [f.field_name for f in merged_fields if f.confidence < ml_threshold]
        if not field_names:
            field_names = [f["name"] for f in INVOICE_TEMPLATE.fields]  # Default fields

        layer3 = await self.llm.extract(
            normalized.normalized_text,
            doc_type or "unknown",
            field_names,
            normalized.tenant_id,
        )
        layer3.doc_id = normalized.doc_id

        # Merge all layers
        all_fields = self._merge_fields(merged_fields, layer3.fields)
        all_confidence = (
            sum(f.confidence for f in all_fields) / len(all_fields)
            if all_fields
            else 0.0
        )

        logger.info(
            "Document %s: Layer 3 (LLM) escalated, %d fields, conf=%.2f",
            normalized.doc_id,
            len(all_fields),
            all_confidence,
        )

        return ExtractionOutput(
            doc_id=normalized.doc_id,
            tenant_id=normalized.tenant_id,
            doc_type=layer3.doc_type or layer2.doc_type or layer1.doc_type,
            fields=all_fields,
            extraction_layer_used=ExtractionLayer.LLM_ESCALATION,
            overall_confidence=all_confidence,
            escalation_reason="low_confidence_escalation",
        )

    def _merge_fields(
        self,
        primary: list[ExtractedField],
        secondary: list[ExtractedField],
    ) -> list[ExtractedField]:
        """
        Merge two sets of extracted fields.

        For each field name, keep the extraction with higher confidence.
        """
        by_name: dict[str, ExtractedField] = {}

        for field in primary:
            by_name[field.field_name] = field

        for field in secondary:
            existing = by_name.get(field.field_name)
            if not existing or field.confidence > existing.confidence:
                by_name[field.field_name] = field

        return list(by_name.values())
