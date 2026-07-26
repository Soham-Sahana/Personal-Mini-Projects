"""
Ambient expense-approval server.

Accepts Pub/Sub push messages on POST /pubsub, feeds each one into the
ADK Workflow graph, and exposes POST /decide/{session_id} so a human can
approve or reject expenses that the workflow paused on.

Usage:
    uv run uvicorn server:fastapi_app --host 0.0.0.0 --port 8080 --reload
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from dotenv import load_dotenv

# Load .env BEFORE any ADK / genai imports
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

from fastapi import FastAPI, Request  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from expense_agent.agent import app as adk_app  # noqa: E402

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("expense_agent.server")

# ── ADK runner ──────────────────────────────────────────────────────────────
runner = InMemoryRunner(app=adk_app)

# ── FastAPI app ─────────────────────────────────────────────────────────────
fastapi_app = FastAPI(
    title="Ambient Expense Agent",
    description="Event-driven expense approval — accepts Pub/Sub push messages",
    version="0.1.0",
)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def normalize_subscription(subscription: str) -> str:
    """Normalize a Pub/Sub subscription path to a short name."""
    if "/" in subscription:
        return subscription.rsplit("/", 1)[-1]
    return subscription


async def _run_workflow(user_id: str, session_id: str, text: str) -> dict:
    """Feed a message into the workflow and collect results."""
    msg = types.Content(role="user", parts=[types.Part.from_text(text=text)])

    content_parts: list[str] = []
    paused = False
    pause_message: str | None = None

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=msg
    ):
        if hasattr(event, "content") and event.content and event.content.parts:
            for p in event.content.parts:
                if hasattr(p, "text") and p.text:
                    content_parts.append(p.text)

        if hasattr(event, "long_running_tool_ids") and event.long_running_tool_ids:
            paused = True

        if hasattr(event, "actions") and event.actions:
            acts = event.actions
            if hasattr(acts, "request_input") and acts.request_input:
                pause_message = getattr(acts.request_input, "message", None)

    return {
        "content": content_parts,
        "paused": paused,
        "pause_message": pause_message,
    }


# ═══════════════════════════════════════════════════════════════════════════
# POST /pubsub — Pub/Sub push endpoint
# ═══════════════════════════════════════════════════════════════════════════

@fastapi_app.post("/pubsub")
async def handle_pubsub(request: Request):
    """Receive a Pub/Sub push message and feed it into the workflow.

    Expected envelope:
    {
      "message": {
        "data": "<base64-encoded expense JSON>",
        "messageId": "123456"
      },
      "subscription": "projects/my-project/subscriptions/expense-events"
    }

    Also accepts a flat JSON body for local testing:
    {"data": {"amount": 150, "submitter": "alice@co.com", ...}}
    """
    envelope = await request.json()

    if "message" in envelope:
        message = envelope["message"]
        raw_data = message.get("data", "")
        message_id = message.get("messageId", "unknown")
        subscription = envelope.get("subscription", "local")
    else:
        raw_data = envelope.get("data", envelope)
        if isinstance(raw_data, dict):
            raw_data = json.dumps(raw_data)
        message_id = "local"
        subscription = "local-test"

    short_sub = normalize_subscription(subscription)
    session_id = f"{short_sub}--{message_id}"
    user_id = short_sub

    log.info("Received expense event  sub=%-20s  msg_id=%s", short_sub, message_id)

    session = await runner.session_service.create_session(
        app_name="expense_agent", user_id=user_id, session_id=session_id
    )

    payload_text = json.dumps({"data": raw_data})
    result = await _run_workflow(user_id, session.id, payload_text)

    if result["paused"]:
        log.info("Expense PAUSED for human review  session=%s", session_id)
        return {
            "status": "pending_review",
            "session_id": session_id,
            "message": result.get("pause_message", "Awaiting human decision"),
            "content": result["content"],
        }

    log.info("Expense processed  session=%s", session_id)
    return {
        "status": "completed",
        "session_id": session_id,
        "content": result["content"],
    }


# ═══════════════════════════════════════════════════════════════════════════
# POST /decide/{session_id} — Human approval endpoint
# ═══════════════════════════════════════════════════════════════════════════

class DecisionRequest(BaseModel):
    """Body for the human approval endpoint."""
    decision: str  # "approve" or "reject", with optional reason


@fastapi_app.post("/decide/{session_id}")
async def decide(session_id: str, body: DecisionRequest):
    """Resume a paused workflow with the human's approve/reject decision."""
    user_id = session_id.split("--")[0] if "--" in session_id else "unknown"

    log.info(
        "Human decision received  session=%s  decision=%s",
        session_id,
        body.decision[:50],
    )

    result = await _run_workflow(user_id, session_id, body.decision)

    log.info("Expense finalized  session=%s", session_id)
    return {
        "status": "decided",
        "session_id": session_id,
        "content": result["content"],
    }


# ═══════════════════════════════════════════════════════════════════════════
# GET /health
# ═══════════════════════════════════════════════════════════════════════════

@fastapi_app.get("/health")
async def health():
    return {"status": "ok", "agent": "expense_agent"}


# ═══════════════════════════════════════════════════════════════════════════
# Entrypoint
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(fastapi_app, host="0.0.0.0", port=8080)
