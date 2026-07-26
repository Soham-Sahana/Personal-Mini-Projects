"""Pydantic schemas shared across the workflow nodes."""

from __future__ import annotations

from pydantic import BaseModel


class Expense(BaseModel):
    """Raw expense fields extracted from the incoming event."""

    amount: float
    submitter: str
    category: str
    description: str
    date: str


class RiskAssessment(BaseModel):
    """Structured output returned by the LLM risk-review node."""

    risk_level: str  # "low" | "medium" | "high" | "critical"
    risk_factors: list[str]
    recommendation: str


class ApprovalDecision(BaseModel):
    """Final recorded outcome — emitted by both the auto and human paths."""

    expense: Expense
    decision: str  # "approved" | "rejected"
    decided_by: str  # "auto" | "human"
    reason: str | None = None
    risk_assessment: RiskAssessment | None = None
