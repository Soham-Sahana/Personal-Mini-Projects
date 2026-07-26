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

"""Unit tests for the query classifier and business tools.

These tests run without any API keys or network access — they exercise
only the deterministic keyword-matching path of classify_query and the
mock-data–backed tools.
"""

from __future__ import annotations

import pytest

from app.agent import classify_query
from app.config import MOCK_ORDERS, MOCK_TRACKING
from app.tools.order_lookup import lookup_order
from app.tools.refund import request_refund
from app.tools.tracking import track_shipment


# ═══════════════════════════════════════════════════════════════════════════
# classify_query — keyword routing
# ═══════════════════════════════════════════════════════════════════════════


class _FakeContext:
    """Minimal stand-in for google.adk.Context used in unit tests."""


@pytest.mark.parametrize(
    "query, expected_route",
    [
        # Shipping FAQ
        ("What are your shipping rates?", "shipping_faq"),
        ("How much does shipping cost?", "shipping_faq"),
        ("Do you offer free shipping?", "shipping_faq"),
        ("How long does delivery take?", "shipping_faq"),
        # Order status
        ("Where is my order?", "order_status"),
        ("Can I track my package?", "order_status"),
        ("When will my delivery arrive?", "order_status"),
        ("Check order status", "order_status"),
        # Refund
        ("I want a refund", "refund"),
        ("How do I return an item?", "refund"),
        ("I received a damaged product", "refund"),
        ("Can I cancel my order?", "refund"),
        # Unrelated
        ("What is the capital of France?", "unrelated"),
        ("Tell me a joke", "unrelated"),
        ("What's the weather like?", "unrelated"),
    ],
)
def test_classify_query_keyword_routing(query: str, expected_route: str) -> None:
    """Keyword classifier should route common queries deterministically."""
    ctx = _FakeContext()
    event = classify_query(ctx, query)
    assert event.route == expected_route, (
        f"Query '{query}' routed to '{event.route}', expected '{expected_route}'"
    )


# ═══════════════════════════════════════════════════════════════════════════
# lookup_order
# ═══════════════════════════════════════════════════════════════════════════


def test_lookup_order_found() -> None:
    """Known order IDs should return full details."""
    result = lookup_order("ORD-1001")
    assert result["order_id"] == "ORD-1001"
    assert result["status"] == "shipped"
    assert "Wireless Mouse" in result["items"]


def test_lookup_order_case_insensitive() -> None:
    """Order lookup should be case-insensitive."""
    result = lookup_order("ord-1002")
    assert result["order_id"] == "ORD-1002"


def test_lookup_order_not_found() -> None:
    """Unknown order IDs should return an error dict."""
    result = lookup_order("ORD-9999")
    assert "error" in result


# ═══════════════════════════════════════════════════════════════════════════
# track_shipment
# ═══════════════════════════════════════════════════════════════════════════


def test_track_shipment_found() -> None:
    """Known tracking numbers should return event history."""
    result = track_shipment("TRK-9876543210")
    assert result["tracking_number"] == "TRK-9876543210"
    assert result["current_status"] == "Out for delivery"
    assert len(result["events"]) == 4


def test_track_shipment_not_found() -> None:
    """Unknown tracking numbers should return an error dict."""
    result = track_shipment("TRK-0000000000")
    assert "error" in result


# ═══════════════════════════════════════════════════════════════════════════
# request_refund
# ═══════════════════════════════════════════════════════════════════════════


def test_refund_delivered_order() -> None:
    """Refund should succeed for a delivered order within the return window."""
    result = request_refund("ORD-1002", "Changed my mind")
    assert result["status"] == "approved"
    assert result["order_id"] == "ORD-1002"
    assert "refund_id" in result


def test_refund_undelivered_order() -> None:
    """Refund should fail for an order that hasn't been delivered yet."""
    result = request_refund("ORD-1001", "Don't want it")
    assert "error" in result
    assert "shipped" in result["error"]


def test_refund_processing_order() -> None:
    """Refund should fail for an order still being processed, with a cancel suggestion."""
    result = request_refund("ORD-1003", "Changed my mind")
    assert "error" in result
    assert "suggestion" in result


def test_refund_order_not_found() -> None:
    """Refund for unknown order should return an error."""
    result = request_refund("ORD-9999", "Test")
    assert "error" in result
