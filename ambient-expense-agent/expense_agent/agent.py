"""
Ambient Expense Approval Agent — ADK 2.0 Workflow graph.

Graph topology
==============

  START
    │
    ▼
  parse_expense              ← extract Expense from JSON / base64
    │
    ▼
  route_expense              ← pure-Python threshold check
    │
    ├─ "auto_approve" ────────► auto_approve ──────────────────┐
    │                                                          │
    └─ "needs_review" ──► prepare_for_review                   │
                              │                                │
                              ▼                                │
                        security_checkpoint  ← PII scrub +     │
                              │                injection scan  │
                              │                                │
                     ┌────────┴────────┐                       │
                 "clean"          "injection"                   │
                     │                 │                        │
                     ▼                 │                        │
               risk_reviewer (LLM)    │                        │
                     │                 │                        │
                     ▼                 │                        │
               human_approval (HITL) ◄─┘                       │
                     │                                         │
                     ▼                         ▼               │
                 record_decision ◄──────────────────────────────┘
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.workflow import Workflow, node
from google.genai import types

from .config import APPROVAL_THRESHOLD, MODEL_NAME
from .schemas import ApprovalDecision, Expense, RiskAssessment
from .security import detect_injection, scrub_pii

# ── Load .env (API key lives here) ──────────────────────────────────────────
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


# ═══════════════════════════════════════════════════════════════════════════
# Node 1 — parse_expense
# ═══════════════════════════════════════════════════════════════════════════
def parse_expense(node_input: types.Content) -> Expense:
    """Extract an Expense from the incoming JSON event.

    Handles two shapes:
      • Plain JSON:  {"data": {"amount": ..., ...}}
      • Pub/Sub:     {"data": "<base64-encoded JSON>"}
    If there is no "data" wrapper the top-level object is used directly.
    """
    raw_text = node_input.parts[0].text
    payload = json.loads(raw_text)

    data = payload.get("data", payload)

    # Real Pub/Sub wraps the body as a base64 string.
    if isinstance(data, str):
        data = json.loads(base64.b64decode(data).decode())

    return Expense(**data)


# ═══════════════════════════════════════════════════════════════════════════
# Node 2 — route_expense   (pure Python, no LLM)
# ═══════════════════════════════════════════════════════════════════════════
def route_expense(node_input: Expense) -> Event:
    """Conditional edge: auto_approve or needs_review."""
    if node_input.amount < APPROVAL_THRESHOLD:
        return Event(output=node_input.model_dump(), route="auto_approve")
    return Event(output=node_input.model_dump(), route="needs_review")


# ═══════════════════════════════════════════════════════════════════════════
# Node 3a — auto_approve   (fast path — no LLM, no human)
# ═══════════════════════════════════════════════════════════════════════════
def auto_approve(node_input: Expense):
    """Instant approval for expenses under the threshold."""
    decision = ApprovalDecision(
        expense=node_input,
        decision="approved",
        decided_by="auto",
        reason=(
            f"Amount ${node_input.amount:.2f} is under "
            f"${APPROVAL_THRESHOLD:.2f} threshold"
        ),
    )
    yield Event(output=decision.model_dump())


# ═══════════════════════════════════════════════════════════════════════════
# Node 3b — prepare_for_review
# ═══════════════════════════════════════════════════════════════════════════
def prepare_for_review(node_input: Expense) -> Event:
    """Stash the expense in workflow state and pass it onward."""
    return Event(
        output=node_input.model_dump(),
        state={"expense": node_input.model_dump()},
    )


# ═══════════════════════════════════════════════════════════════════════════
# Node 3c — security_checkpoint   (PII scrub + injection scan)
# ═══════════════════════════════════════════════════════════════════════════
def security_checkpoint(ctx: Context, node_input: Expense) -> Event:
    """Gate between the business-logic routing and the LLM.

    1. Scrub PII (SSNs, credit-card numbers) from the description so
       neither the model nor the HITL payload ever sees raw PII.
    2. Scan the original description for prompt-injection patterns.
       - Clean  → route to the LLM risk reviewer.
       - Dirty  → skip the LLM entirely, fabricate a critical-severity
                   RiskAssessment, and route straight to a human.
    """
    # ── 1. PII scrub ──
    scrub = scrub_pii(node_input.description)
    scrubbed_expense = node_input.model_copy(
        update={"description": scrub.clean_text},
    )

    # Persist the *clean* expense in state (used later by human_approval)
    state_delta: dict = {"expense": scrubbed_expense.model_dump()}
    if scrub.redacted_categories:
        state_delta["pii_redacted"] = scrub.redacted_categories
        state_delta["pii_redaction_count"] = scrub.redaction_count

    # ── 2. Injection scan (runs on the ORIGINAL text, before scrubbing) ──
    injection = detect_injection(node_input.description)

    if injection.is_injected:
        # Build a synthetic RiskAssessment — the LLM must never see this input
        synthetic_risk = RiskAssessment(
            risk_level="critical",
            risk_factors=[
                "⚠️  PROMPT INJECTION DETECTED",
                f"Matched signals: {', '.join(injection.matched_signals)}",
                f"Categories: {', '.join(injection.matched_categories)}",
            ],
            recommendation=(
                "REJECT — the expense description contains embedded "
                "instructions attempting to manipulate the approval process. "
                "This input was blocked from reaching the LLM."
            ),
        )
        state_delta["security_flag"] = "prompt_injection"
        state_delta["injection_signals"] = injection.matched_signals
        return Event(
            output=synthetic_risk.model_dump(),
            route="injection_detected",
            state=state_delta,
        )

    # ── 3. Clean — format the scrubbed expense for the LLM ──
    expense_text = (
        "Review this expense report for risk factors:\n"
        f"  Amount:      ${scrubbed_expense.amount:.2f}\n"
        f"  Submitter:   {scrubbed_expense.submitter}\n"
        f"  Category:    {scrubbed_expense.category}\n"
        f"  Description: {scrubbed_expense.description}\n"
        f"  Date:        {scrubbed_expense.date}"
    )
    return Event(
        output=expense_text,
        route="clean",
        state=state_delta,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Node 4 — risk_reviewer   (LLM)
# ═══════════════════════════════════════════════════════════════════════════
risk_reviewer = LlmAgent(
    name="risk_reviewer",
    model=MODEL_NAME,
    instruction=(
        "You are a financial risk reviewer for corporate expense reports. "
        "Analyse the expense and identify concrete risk factors.\n"
        "Consider: unusually high amounts for the category, vague or missing "
        "descriptions, uncommon categories, weekend or holiday submissions, "
        "and round-number amounts that may indicate estimates.\n"
        "Be concise and specific — do not invent risks that the data does "
        "not support."
    ),
    output_schema=RiskAssessment,
    output_key="risk_assessment",
)


# ═══════════════════════════════════════════════════════════════════════════
# Node 5 — human_approval   (HITL — pauses the workflow)
# ═══════════════════════════════════════════════════════════════════════════
@node(rerun_on_resume=True)
async def human_approval(ctx: Context, node_input: dict):
    """Present the risk report and wait for a human approve / reject."""
    risk = RiskAssessment(**node_input)
    expense = Expense(**ctx.state["expense"])

    # ── First run: yield a RequestInput to pause the workflow ──
    if not ctx.resume_inputs:
        summary = (
            "🔍  EXPENSE REVIEW REQUIRED\n"
            "─────────────────────────────\n"
            f"  Submitter:   {expense.submitter}\n"
            f"  Amount:      ${expense.amount:.2f}\n"
            f"  Category:    {expense.category}\n"
            f"  Description: {expense.description}\n"
            f"  Date:        {expense.date}\n"
            "\n"
            f"  Risk level:    {risk.risk_level.upper()}\n"
            f"  Risk factors:  {', '.join(risk.risk_factors)}\n"
            f"  Recommendation:{risk.recommendation}\n"
            "─────────────────────────────\n"
            "Reply **approve** or **reject** (with optional reason)."
        )
        yield RequestInput(interrupt_id="manager_decision", message=summary)
        return  # workflow pauses here

    # ── Resumed: the manager has responded ──
    raw_response = str(ctx.resume_inputs["manager_decision"]).strip()
    is_approved = raw_response.lower().startswith("approve")
    decision_word = "approved" if is_approved else "rejected"

    decision = ApprovalDecision(
        expense=expense,
        decision=decision_word,
        decided_by="human",
        reason=raw_response,
        risk_assessment=risk,
    )
    yield Event(output=decision.model_dump())


# ═══════════════════════════════════════════════════════════════════════════
# Node 6 — record_decision   (both paths converge here)
# ═══════════════════════════════════════════════════════════════════════════
def record_decision(node_input: dict):
    """Emit a user-visible summary and pass the decision downstream."""
    d = ApprovalDecision(**node_input)
    emoji = "✅" if d.decision == "approved" else "❌"

    lines = [
        f"{emoji}  DECISION: {d.decision.upper()}",
        f"   Expense:    ${d.expense.amount:.2f} — {d.expense.submitter}",
        f"   Category:   {d.expense.category}",
        f"   Decided by: {d.decided_by}",
    ]
    if d.reason:
        lines.append(f"   Reason:     {d.reason}")
    if d.risk_assessment:
        lines.append(f"   Risk level: {d.risk_assessment.risk_level}")

    yield Event(
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text="\n".join(lines))],
        ),
    )
    yield Event(output=node_input)


# ═══════════════════════════════════════════════════════════════════════════
# Wiring — the graph
# ═══════════════════════════════════════════════════════════════════════════
root_agent = Workflow(
    name="expense_approval",
    edges=[
        # ── linear spine ──
        ("START", parse_expense),
        (parse_expense, route_expense),
        # ── conditional fork (dict maps route → target) ──
        (route_expense, {
            "auto_approve": auto_approve,
            "needs_review": prepare_for_review,
        }),
        # ── security gate ──
        (prepare_for_review, security_checkpoint),
        (security_checkpoint, {
            "clean": risk_reviewer,
            "injection_detected": human_approval,
        }),
        # ── review branch ──
        (risk_reviewer, human_approval),
        # ── both branches converge ──
        (auto_approve, record_decision),
        (human_approval, record_decision),
    ],
)

app = App(
    name="expense_agent",
    root_agent=root_agent,
)
