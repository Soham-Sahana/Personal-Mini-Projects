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

"""Configuration and business data for the customer support agent."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Shipping rates
# ---------------------------------------------------------------------------

SHIPPING_RATES: dict[str, dict[str, str]] = {
    "standard": {
        "price": "$5.99",
        "delivery": "5–7 business days",
        "description": "Reliable ground shipping for non-urgent orders.",
    },
    "express": {
        "price": "$12.99",
        "delivery": "2–3 business days",
        "description": "Faster delivery for time-sensitive packages.",
    },
    "overnight": {
        "price": "$24.99",
        "delivery": "Next business day",
        "description": "Guaranteed next-day delivery (order by 2 PM).",
    },
}

FREE_SHIPPING_THRESHOLD: float = 50.00  # USD


def get_shipping_rates() -> str:
    """Return a human-readable summary of shipping rates."""
    lines = [f"Free shipping on orders over ${FREE_SHIPPING_THRESHOLD:.0f}!"]
    for tier, info in SHIPPING_RATES.items():
        lines.append(
            f"  • {tier.title()}: {info['price']} — {info['delivery']} ({info['description']})"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Return / refund policy
# ---------------------------------------------------------------------------

RETURN_WINDOW_DAYS: int = 30

RETURN_POLICY: dict[str, str] = {
    "window": f"{RETURN_WINDOW_DAYS} days from delivery date",
    "condition": "Items must be unused and in original packaging",
    "exceptions": "Final-sale items, perishable goods, and gift cards are non-refundable",
    "process": "Initiate a return via your order page or contact support",
    "refund_timeline": "Refunds are processed within 5–7 business days after we receive the item",
}


def get_return_policy() -> str:
    """Return a human-readable summary of the return policy."""
    lines = []
    for key, value in RETURN_POLICY.items():
        lines.append(f"  • {key.replace('_', ' ').title()}: {value}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mock order database  (used by tools for demo / testing)
# ---------------------------------------------------------------------------

MOCK_ORDERS: dict[str, dict] = {
    "ORD-1001": {
        "customer_email": "alice@example.com",
        "items": ["Wireless Mouse", "USB-C Hub"],
        "total": 67.98,
        "status": "shipped",
        "tracking_number": "TRK-9876543210",
        "shipping_method": "express",
        "ordered_at": "2026-07-20T14:30:00Z",
        "delivered_at": None,
    },
    "ORD-1002": {
        "customer_email": "bob@example.com",
        "items": ["Mechanical Keyboard"],
        "total": 129.99,
        "status": "delivered",
        "tracking_number": "TRK-1234567890",
        "shipping_method": "standard",
        "ordered_at": "2026-07-10T09:15:00Z",
        "delivered_at": "2026-07-17T11:00:00Z",
    },
    "ORD-1003": {
        "customer_email": "carol@example.com",
        "items": ["Monitor Stand", "Webcam", "Desk Lamp"],
        "total": 189.97,
        "status": "processing",
        "tracking_number": None,
        "shipping_method": "overnight",
        "ordered_at": "2026-07-25T16:45:00Z",
        "delivered_at": None,
    },
}

# ---------------------------------------------------------------------------
# Mock tracking events
# ---------------------------------------------------------------------------

MOCK_TRACKING: dict[str, list[dict[str, str]]] = {
    "TRK-9876543210": [
        {"timestamp": "2026-07-21T08:00:00Z", "status": "Package picked up", "location": "Warehouse, TX"},
        {"timestamp": "2026-07-21T18:00:00Z", "status": "In transit", "location": "Dallas, TX"},
        {"timestamp": "2026-07-22T12:00:00Z", "status": "In transit", "location": "Memphis, TN"},
        {"timestamp": "2026-07-23T09:00:00Z", "status": "Out for delivery", "location": "Atlanta, GA"},
    ],
    "TRK-1234567890": [
        {"timestamp": "2026-07-11T08:00:00Z", "status": "Package picked up", "location": "Warehouse, TX"},
        {"timestamp": "2026-07-13T14:00:00Z", "status": "In transit", "location": "Nashville, TN"},
        {"timestamp": "2026-07-15T10:00:00Z", "status": "In transit", "location": "Charlotte, NC"},
        {"timestamp": "2026-07-17T11:00:00Z", "status": "Delivered", "location": "Raleigh, NC"},
    ],
}
