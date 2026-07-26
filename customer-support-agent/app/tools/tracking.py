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

"""Tool: track a shipment by its tracking number."""

from __future__ import annotations

from app.config import MOCK_TRACKING


def track_shipment(tracking_number: str) -> dict:
    """Track a shipment and return its event history.

    Args:
        tracking_number: The tracking identifier (e.g. "TRK-9876543210").

    Returns:
        A dict with tracking events, or an error message if not found.
    """
    tracking_number = tracking_number.strip().upper()
    events = MOCK_TRACKING.get(tracking_number)
    if events is None:
        return {
            "error": (
                f"Tracking number '{tracking_number}' not found. "
                "Please verify the number and try again."
            )
        }
    latest = events[-1]
    return {
        "tracking_number": tracking_number,
        "current_status": latest["status"],
        "current_location": latest["location"],
        "events": events,
    }
