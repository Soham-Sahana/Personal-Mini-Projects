"""Quick smoke test — sends a $150 expense through the workflow."""

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

# Load .env FIRST, before any ADK module is imported
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from expense_agent.agent import app  # noqa: E402


async def main():
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="expense_agent", user_id="test"
    )

    payload = json.dumps(
        {
            "data": {
                "amount": 150.0,
                "submitter": "alice@company.com",
                "category": "software",
                "description": "IDE License",
                "date": "2026-06-06",
            }
        }
    )
    msg = types.Content(role="user", parts=[types.Part.from_text(text=payload)])

    print()
    print("=" * 55)
    print("  Sending expense: $150 (above threshold -> review)")
    print("=" * 55)
    print()

    paused = False
    async for event in runner.run_async(
        user_id="test", session_id=session.id, new_message=msg
    ):
        etype = type(event).__name__
        if hasattr(event, "content") and event.content and event.content.parts:
            for p in event.content.parts:
                if hasattr(p, "text") and p.text:
                    print(f"[{etype}/content] {p.text[:200]}")

        if hasattr(event, "actions") and event.actions:
            acts = event.actions
            if hasattr(acts, "request_input") and acts.request_input:
                ri = acts.request_input
                print(f"\n[HITL] Request for input detected!")
                print(f"[HITL] interrupt_id = {getattr(ri, 'interrupt_id', 'N/A')}")
                print(f"[HITL] message:\n{getattr(ri, 'message', str(ri))}")
                paused = True

        if hasattr(event, "interrupts") and event.interrupts:
            for intr in event.interrupts:
                print(f"\n[HITL] interrupt_id = {intr.interrupt_id}")
                print(f"[HITL] message:\n{intr.message}")
                paused = True

    if paused:
        print("\n>>> Workflow PAUSED — waiting for human decision <<<")
    else:
        print("\n[info] Workflow completed without HITL pause.")

    # Show final session state
    updated = await runner.session_service.get_session(
        app_name="expense_agent", user_id="test", session_id=session.id
    )
    if updated and updated.state:
        print(f"\n[session state] {json.dumps(dict(updated.state), indent=2, default=str)}")

    print("\n=== Run complete ===")


if __name__ == "__main__":
    asyncio.run(main())
