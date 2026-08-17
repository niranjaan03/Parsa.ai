"""
Normalization Service — Phase 4 (Stage 5).

Transforms raw OCR output into clean, standardized data:
  - Spell correction
  - Key-value pair recovery
  - Date normalization (locale-aware → ISO 8601)
  - Currency/unit normalization
  - Entity normalization (company names, addresses)
  - Language-aware transformations (CJK full-width → half-width, etc.)
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from libs.common.schemas import (
    ExtractionResult,
    NormalizedField,
    NormalizedOutput,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Date Normalization
# ═══════════════════════════════════════════════════════════════════════════════

# Common date patterns (ordered by specificity)
DATE_PATTERNS: list[tuple[str, str]] = [
    # ISO formats
    (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "%Y-%m-%dT%H:%M:%S"),
    (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
    # US formats
    (r"\d{2}/\d{2}/\d{4}", "%m/%d/%Y"),
    (r"\d{1,2}/\d{1,2}/\d{4}", "%m/%d/%Y"),
    # EU formats
    (r"\d{2}\.\d{2}\.\d{4}", "%d.%m.%Y"),
    (r"\d{2}-\d{2}-\d{4}", "%d-%m-%Y"),
    # Written formats
    (r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}", None),
    (r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}", None),
    # Chinese date format
    (r"\d{4}年\d{1,2}月\d{1,2}日", None),
]


def normalize_date(raw: str) -> str | None:
    """
    Attempt to normalize a date string to ISO 8601 (YYYY-MM-DD).

    Returns normalized date string or None if no date pattern matched.
    """
    raw = raw.strip()

    # Try specific format patterns
    for pattern, fmt in DATE_PATTERNS:
        match = re.search(pattern, raw)
        if match:
            date_str = match.group()
            if fmt:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue

    # Chinese dates
    cn_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", raw)
    if cn_match:
        y, m, d = cn_match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # Written English dates
    for month_name in [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]:
        en_match = re.search(
            rf"({month_name})\s+(\d{{1,2}}),?\s+(\d{{4}})", raw, re.IGNORECASE
        )
        if en_match:
            try:
                # Try both full and abbreviated month names
                for fmt_str in ["%B %d %Y", "%b %d %Y"]:
                    try:
                        dt = datetime.strptime(
                            f"{en_match.group(1)} {en_match.group(2)} {en_match.group(3)}",
                            fmt_str,
                        )
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            except ValueError:
                continue

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Currency / Amount Normalization
# ═══════════════════════════════════════════════════════════════════════════════

CURRENCY_SYMBOLS: dict[str, str] = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "CNY",
    "₹": "INR",
    "₩": "KRW",
    "฿": "THB",
    "₫": "VND",
    "R$": "BRL",
    "A$": "AUD",
    "C$": "CAD",
}

AMOUNT_RE = re.compile(
    r"(?P<currency>[€$£¥₹₩฿₫]|R\$|A\$|C\$)\s*"
    r"(?P<amount>[\d,]+(?:\.\d{1,2})?)"
    r"\s*(?P<unit>USD|EUR|GBP|CNY|JPY|INR|KRW)?"
)

# Fallback: amount with explicit currency code but no symbol
AMOUNT_WITH_CODE_RE = re.compile(
    r"(?P<amount>[\d,]+\.\d{2})"
    r"\s*(?P<unit>USD|EUR|GBP|CNY|JPY|INR|KRW)"
)


def normalize_currency(raw: str) -> dict[str, Any] | None:
    """
    Normalize currency amounts.

    Returns {"amount": float, "currency": "USD", "raw": "..."} or None.
    """
    match = AMOUNT_RE.search(raw)
    if not match:
        return None

    amount_str = match.group("amount").replace(",", "")
    try:
        amount = float(amount_str)
    except ValueError:
        return None

    currency = match.group("unit") or ""
    symbol = match.group("currency") or ""
    if not currency and symbol:
        currency = CURRENCY_SYMBOLS.get(symbol, "")

    if amount > 0:
        return {
            "amount": amount,
            "currency": currency,
            "raw": match.group(),
        }
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Key-Value Pair Recovery
# ═══════════════════════════════════════════════════════════════════════════════

KV_PATTERNS = [
    re.compile(r"(?P<key>[A-Za-z][A-Za-z\s]{1,30}):\s*(?P<value>.+)"),       # Key: Value
    re.compile(r"(?P<key>[A-Za-z][A-Za-z\s]{1,30})=\s*(?P<value>.+)"),       # Key = Value
    re.compile(r"(?P<key>[A-Za-z][A-Za-z\s]{1,30})\t+(?P<value>.+)"),        # Key\tValue
]


def extract_key_value_pairs(text: str) -> list[NormalizedField]:
    """
    Extract key-value pairs from text using pattern matching.

    Handles patterns like:
      - "Invoice Number: INV-2024-001"
      - "Date: January 15, 2024"
      - "Total Amount: $1,234.56"
    """
    fields: list[NormalizedField] = []
    seen_keys: set[str] = set()

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        for pattern in KV_PATTERNS:
            match = pattern.match(line)
            if match:
                key = match.group("key").strip()
                value = match.group("value").strip()

                # Deduplicate by normalized key
                norm_key = key.lower().replace(" ", "_")
                if norm_key in seen_keys:
                    continue
                seen_keys.add(norm_key)

                # Determine field type and normalize
                field_type = "string"
                normalized = value

                # Try date normalization
                date_norm = normalize_date(value)
                if date_norm:
                    field_type = "date"
                    normalized = date_norm

                # Try currency normalization
                curr_norm = normalize_currency(value)
                if curr_norm:
                    field_type = "currency"
                    normalized = f"{curr_norm['amount']:.2f} {curr_norm['currency']}".strip()

                fields.append(
                    NormalizedField(
                        key=norm_key,
                        raw_value=value,
                        normalized_value=normalized,
                        field_type=field_type,
                        confidence=0.8,
                    )
                )
                break

    return fields


# ═══════════════════════════════════════════════════════════════════════════════
# Language-Aware Normalization
# ═══════════════════════════════════════════════════════════════════════════════


def normalize_fullwidth(text: str) -> str:
    """Convert CJK full-width characters to ASCII half-width."""
    result = []
    for char in text:
        code = ord(char)
        # Full-width ASCII variants (FF01-FF5E) → ASCII (0021-007E)
        if 0xFF01 <= code <= 0xFF5E:
            result.append(chr(code - 0xFEE0))
        # Full-width space → ASCII space
        elif code == 0x3000:
            result.append(" ")
        else:
            result.append(char)
    return "".join(result)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace: collapse runs, trim lines."""
    lines = []
    for line in text.splitlines():
        # Collapse multiple spaces to single
        cleaned = re.sub(r"[ \t]+", " ", line.strip())
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Main Normalization Service
# ═══════════════════════════════════════════════════════════════════════════════


class NormalizationService:
    """
    Runs the full normalization pipeline on OCR extraction results.

    Produces a NormalizedOutput with:
      - Detected key-value pairs (dates, currencies normalized)
      - Cleaned text (whitespace, full-width chars normalized)
      - Field-level confidence scores
    """

    async def normalize(
        self,
        extraction: ExtractionResult,
        locale: str = "en_US",
    ) -> NormalizedOutput:
        """Run normalization on an extraction result."""
        # Gather all text
        full_text = extraction.full_text

        # 1. Language-aware normalization
        normalized_text = normalize_fullwidth(full_text)
        normalized_text = normalize_whitespace(normalized_text)

        # 2. Extract key-value pairs
        fields = extract_key_value_pairs(normalized_text)

        logger.info(
            "Normalized document %s: %d fields extracted",
            extraction.doc_id,
            len(fields),
        )

        return NormalizedOutput(
            doc_id=extraction.doc_id,
            tenant_id=extraction.tenant_id,
            fields=fields,
            normalized_text=normalized_text,
            metadata={
                "locale": locale,
                "original_length": len(full_text),
                "normalized_length": len(normalized_text),
                "field_count": len(fields),
            },
        )
