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

"""Tool: request a refund for an order."""

from __future__ import annotations

from datetime import datetime, timezone

from app.config import MOCK_ORDERS, RETURN_WINDOW_DAYS


def request_refund(order_id: str, reason: str) -> dict:
    """Request a refund for an order.

    Validates that the order exists and is within the return window
    before initiating the refund process.

    Args:
        order_id: The order identifier (e.g. "ORD-1002").
        reason: The reason for the refund request.

    Returns:
        A dict indicating the refund status or an error message.
    """
    order_id = order_id.strip().upper()
    order = MOCK_ORDERS.get(order_id)

    if order is None:
        return {
            "error": f"Order '{order_id}' not found. Please double-check the order ID."
        }

    # Must be delivered to request a refund
    if order["status"] != "delivered":
        return {
            "error": (
                f"Order '{order_id}' has status '{order['status']}'. "
                "Refunds can only be processed for delivered orders."
            ),
            "suggestion": (
                "If your order hasn't shipped yet, you can cancel it instead."
                if order["status"] == "processing"
                else "Please wait until your order is delivered to request a refund."
            ),
        }

    # Check return window
    delivered_at = order.get("delivered_at")
    if delivered_at:
        delivery_date = datetime.fromisoformat(delivered_at)
        now = datetime.now(timezone.utc)
        days_since = (now - delivery_date).days
        if days_since > RETURN_WINDOW_DAYS:
            return {
                "error": (
                    f"Order '{order_id}' was delivered {days_since} days ago. "
                    f"The return window is {RETURN_WINDOW_DAYS} days."
                ),
                "eligible": False,
            }

    # Process the refund (mock)
    return {
        "refund_id": f"RFD-{order_id.split('-')[1]}",
        "order_id": order_id,
        "amount": f"${order['total']:.2f}",
        "reason": reason,
        "status": "approved",
        "message": (
            f"Refund of ${order['total']:.2f} has been initiated for order {order_id}. "
            "You will receive the refund within 5–7 business days."
        ),
    }
