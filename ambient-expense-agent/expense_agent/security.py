"""PII scrubbing and prompt-injection detection utilities.

These run *before* any data reaches the LLM or appears in logs/HITL payloads.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════════════════
# PII scrubbing
# ═══════════════════════════════════════════════════════════════════════════

_PII_RULES: list[tuple[re.Pattern[str], str, str]] = [
    # SSN  (123-45-6789)
    (
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "[SSN REDACTED]",
        "ssn",
    ),
    # Credit card — groups of 4 separated by spaces or dashes
    (
        re.compile(r"\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b"),
        "[CC REDACTED]",
        "credit_card",
    ),
    # Credit card — Amex format  (3712-345678-90123)
    (
        re.compile(r"\b3[47]\d{2}[-\s]\d{6}[-\s]\d{5}\b"),
        "[CC REDACTED]",
        "credit_card",
    ),
    # Credit card — continuous 15-16 digits starting with known BINs
    (
        re.compile(
            r"\b(?:4\d{15}|5[1-5]\d{14}|3[47]\d{13}|6(?:011|5\d{2})\d{12})\b"
        ),
        "[CC REDACTED]",
        "credit_card",
    ),
]


@dataclass
class ScrubResult:
    """Outcome of a PII scrub pass."""

    clean_text: str
    redacted_categories: list[str] = field(default_factory=list)
    redaction_count: int = 0


def scrub_pii(text: str) -> ScrubResult:
    """Remove SSNs and credit-card numbers, returning the cleaned text
    and a summary of what was redacted."""
    clean = text
    categories: set[str] = set()
    count = 0

    for pattern, replacement, category in _PII_RULES:
        hits = pattern.findall(clean)
        if hits:
            count += len(hits)
            categories.add(category)
            clean = pattern.sub(replacement, clean)

    return ScrubResult(
        clean_text=clean,
        redacted_categories=sorted(categories),
        redaction_count=count,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Prompt-injection detection
# ═══════════════════════════════════════════════════════════════════════════

_INJECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(p, re.IGNORECASE), label)
    for p, label in [
        # ── Instruction override ──
        (r"ignore\s+(?:all\s+)?(?:previous\s+)?instructions", "instruction_override"),
        (r"disregard\s+(?:the\s+|all\s+|your\s+)?(?:rules|guidelines|policy)", "instruction_override"),
        (r"forget\s+(?:all\s+)?(?:your\s+)?(?:previous\s+)?(?:rules|instructions)", "instruction_override"),
        # ── Role hijacking ──
        (r"you\s+are\s+now\b", "role_hijack"),
        (r"pretend\s+(?:you\s+are|to\s+be)", "role_hijack"),
        (r"act\s+as\s+(?:if|an?)\b", "role_hijack"),
        # ── Direct manipulation of outcome ──
        (r"override\s+(?:the\s+)?approv", "outcome_manipulation"),
        (r"auto[\-\s]?approve", "outcome_manipulation"),
        (r"mark\s+(?:this\s+)?(?:as\s+)?approved", "outcome_manipulation"),
        (r"(?:always|must|should)\s+approve", "outcome_manipulation"),
        (r"approve\s+(?:this|immediately|now)", "outcome_manipulation"),
        # ── Review bypass ──
        (r"bypass\s+(?:the\s+)?(?:review|policy|rules|check)", "review_bypass"),
        (r"skip\s+(?:the\s+)?(?:review|check|approval)", "review_bypass"),
        (r"do\s+not\s+(?:flag|review|reject)", "review_bypass"),
        (r"no\s+risk\s+factors?", "review_bypass"),
        # ── Prompt framing / delimiters ──
        (r"system\s*prompt", "prompt_framing"),
        (r"<\s*/?system\s*>", "prompt_framing"),
        (r"\[\s*INST\s*\]", "prompt_framing"),
        (r"```\s*(?:system|instruction)", "prompt_framing"),
        (r"IMPORTANT\s*:\s*(?:always\s+)?approve", "prompt_framing"),
    ]
]


@dataclass
class InjectionResult:
    """Outcome of a prompt-injection scan."""

    is_injected: bool
    matched_signals: list[str] = field(default_factory=list)
    matched_categories: list[str] = field(default_factory=list)


def detect_injection(text: str) -> InjectionResult:
    """Scan text for prompt-injection signals.

    Returns an InjectionResult; callers check `.is_injected`.
    """
    signals: list[str] = []
    categories: set[str] = set()

    for pattern, category in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            signals.append(match.group())
            categories.add(category)

    return InjectionResult(
        is_injected=bool(signals),
        matched_signals=signals,
        matched_categories=sorted(categories),
    )
