# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Integration tests — run the full workflow end-to-end.

These tests require a Gemini API key (GEMINI_API_KEY env var) or GCP
Application Default Credentials because the specialist LLM agents make
real model calls.

Run with:
    uv run pytest tests/integration/ -v
"""

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


def test_unrelated_query_is_declined() -> None:
    """An unrelated query should be politely declined."""
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(
        user_id="test_user", app_name="test"
    )
    runner = Runner(
        agent=root_agent, session_service=session_service, app_name="test"
    )

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="What is the capital of France?")],
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
        )
    )

    outputs = [e.output for e in events if e.output is not None]
    assert any("shipping" in str(o).lower() for o in outputs), (
        f"Expected a decline mentioning shipping, got: {outputs}"
    )


def test_shipping_query_is_routed() -> None:
    """A shipping-related query should be routed to the FAQ agent."""
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(
        user_id="test_user", app_name="test"
    )
    runner = Runner(
        agent=root_agent, session_service=session_service, app_name="test"
    )

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="What are your shipping rates?")],
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
        )
    )

    outputs = [e.output for e in events if e.output is not None]
    assert any("shipping rates" in str(o).lower() for o in outputs), (
        f"Expected shipping rates query forwarded, got: {outputs}"
    )
