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

"""Tool: look up an order by its ID."""

from __future__ import annotations

from app.config import MOCK_ORDERS


def lookup_order(order_id: str) -> dict:
    """Look up an order by its ID and return its details.

    Args:
        order_id: The order identifier (e.g. "ORD-1001").

    Returns:
        A dict with order details, or an error message if not found.
    """
    order_id = order_id.strip().upper()
    order = MOCK_ORDERS.get(order_id)
    if order is None:
        return {
            "error": f"Order '{order_id}' not found. Please double-check the order ID."
        }
    return {
        "order_id": order_id,
        "items": order["items"],
        "total": f"${order['total']:.2f}",
        "status": order["status"],
        "shipping_method": order["shipping_method"],
        "tracking_number": order.get("tracking_number"),
        "ordered_at": order["ordered_at"],
        "delivered_at": order.get("delivered_at"),
    }
