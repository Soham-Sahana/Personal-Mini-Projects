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

"""Customer Support Agent — ADK 2.0 graph-workflow with intelligent routing.

Classifies incoming customer queries and routes them to the appropriate
specialist agent (shipping FAQ, order status, refund) or politely declines
unrelated requests.
"""

import os

import google.auth
from google.adk import Context, Event, Workflow
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.auth.exceptions import DefaultCredentialsError
from google.genai import types

from app.config import get_return_policy, get_shipping_rates
from app.tools.order_lookup import lookup_order
from app.tools.refund import request_refund
from app.tools.tracking import track_shipment

# ---------------------------------------------------------------------------
# Environment setup — prefer Vertex AI, fall back to AI Studio
# ---------------------------------------------------------------------------
try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id or "dummy-project"
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
except DefaultCredentialsError:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"


# ═══════════════════════════════════════════════════════════════════════════
# Node 1 — Query classifier (keyword rules + LLM fallback)
# ═══════════════════════════════════════════════════════════════════════════


def classify_query(ctx: Context, node_input: str) -> Event:
    """Classify a customer query into a support category.

    Uses fast keyword matching first; falls back to LLM classification
    when keywords are inconclusive and API credentials are available.

    Routes:
        shipping_faq  — general shipping questions
        order_status  — tracking / delivery inquiries
        refund        — return & refund requests
        unrelated     — anything else
    """
    query = node_input.lower().strip()

    # --- Fast keyword rules ------------------------------------------------
    order_status_keywords = {
        "order", "status", "where", "track", "tracking",
        "shipment", "package", "delivery", "when", "arrive", "arriving",
    }
    refund_keywords = {
        "refund", "return", "money back", "exchange", "cancel",
        "cancellation", "damaged", "broken", "wrong item",
    }
    shipping_faq_keywords = {
        "rates", "costs", "how long", "methods", "free shipping",
    }

    words = set(query.split())

    if words & order_status_keywords or any(kw in query for kw in order_status_keywords):
        return Event(route="order_status", output=node_input)

    if words & refund_keywords or any(kw in query for kw in refund_keywords):
        return Event(route="refund", output=node_input)

    if words & shipping_faq_keywords or any(kw in query for kw in shipping_faq_keywords):
        return Event(route="shipping_faq", output=node_input)

    # --- LLM fallback ------------------------------------------------------
    has_api_key = bool(os.environ.get("GEMINI_API_KEY"))
    has_gcp_creds = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI") == "True"

    if has_api_key or has_gcp_creds:
        try:
            from google import genai

            client = genai.Client()
            prompt = (
                "Classify the following customer query into one of these four "
                "categories: 'shipping_faq', 'order_status', 'refund', or "
                "'unrelated'.\n\n"
                "- 'shipping_faq': general shipping questions (rates, costs, "
                "delivery times, methods, free shipping).\n"
                "- 'order_status': checking order status, tracking, shipments, "
                "package delivery, arrival times.\n"
                "- 'refund': refunds, returns, money back, exchanges, "
                "cancellations, damaged/broken/wrong items.\n"
                "- 'unrelated': everything else.\n\n"
                f"Query: {node_input}\n\nClassification:"
            )
            response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
            )
            classification = response.text.strip().lower()
            for route in ("shipping_faq", "order_status", "refund", "unrelated"):
                if route in classification:
                    return Event(route=route, output=node_input)
        except Exception:
            pass  # fall through to default

    return Event(route="unrelated", output=node_input)


# ═══════════════════════════════════════════════════════════════════════════
# Node 2 — Polite decline for out-of-scope queries
# ═══════════════════════════════════════════════════════════════════════════


def polite_decline(node_input: str) -> str:
    """Politely decline queries outside our support scope."""
    return (
        "I'm sorry, but I can only assist you with shipping information, "
        "order tracking, or refund processing. Please let me know "
        "if you need help with any of those!"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Specialist agents
# ═══════════════════════════════════════════════════════════════════════════

_RETRY = types.HttpRetryOptions(attempts=3)

shipping_faq_agent = Agent(
    name="shipping_faq_agent",
    model=Gemini(model="gemini-flash-latest", retry_options=_RETRY),
    instruction=(
        "You are an enthusiastic and friendly customer support representative "
        "for a shipping company! 📦✨\n\n"
        "Your personality is warm, upbeat, and helpful — you LOVE shipping! "
        "Use emojis naturally in your responses to keep things fun.\n\n"
        "Key info you know:\n"
        f"- Shipping Rates: {get_shipping_rates()}\n"
        f"- Return Policy: {get_return_policy()}\n\n"
        "Keep your responses concise but enthusiastic. "
        "Always end with an offer to help further! 😊"
    ),
)

order_status_agent = Agent(
    name="order_status_agent",
    model=Gemini(model="gemini-flash-latest", retry_options=_RETRY),
    tools=[lookup_order, track_shipment],
    instruction=(
        "You help customers check order status and track shipments. "
        "Ask for the order ID or tracking number if not provided. "
        "Present tracking events in a clear timeline format."
    ),
)

refund_agent = Agent(
    name="refund_agent",
    model=Gemini(model="gemini-flash-latest", retry_options=_RETRY),
    tools=[lookup_order, request_refund],
    instruction=(
        "You help process refund requests. Ask for the order ID and reason "
        "if not provided. Check eligibility before processing. "
        "Be empathetic and clear about timelines."
    ),
)

# ═══════════════════════════════════════════════════════════════════════════
# Workflow — deterministic graph routing
# ═══════════════════════════════════════════════════════════════════════════

workflow = Workflow(
    name="customer_support_workflow",
    edges=[
        ("START", classify_query),
        (
            classify_query,
            {
                "shipping_faq": shipping_faq_agent,
                "order_status": order_status_agent,
                "refund": refund_agent,
                "unrelated": polite_decline,
            },
        ),
    ],
)

root_agent = workflow

app = App(
    root_agent=root_agent,
    name="app",
)
