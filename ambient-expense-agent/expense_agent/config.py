"""Ambient Expense Approval Agent – configuration constants."""

# ── Approval threshold (USD) ──
# Expenses below this amount are auto-approved with no LLM call.
APPROVAL_THRESHOLD: float = 100.00

# ── LLM model for risk review ──
MODEL_NAME: str = "gemini-3.1-flash-lite"
