"""
Temporal Alignment, Lead-Time Tracking, and Forecast Horizon Management.

Ensures:
- Consistent ISO8601 formatting and timezone awareness (UTC default).
- Strict separation of forecast issue time, valid time, and lead time.
- Enforcement of supported forecast horizons (no silent extrapolation beyond data boundaries).
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple


def parse_iso_timestamp(ts_str: str) -> datetime:
    """Parses an ISO 8601 timestamp string into a timezone-aware UTC datetime."""
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_iso_timestamp(dt: datetime) -> str:
    """Formats a datetime into a standard ISO 8601 UTC string ending in 'Z'."""
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class ForecastHorizonValidator:
    """
    Validates whether a proposed journey departure and arrival window fall within
    the reliable forecast horizon supported by the model and simulation data.
    """
    def __init__(self, max_horizon_seconds: int = 180 * 60):  # 180 minutes = 3 hours
        self.max_horizon_seconds = max_horizon_seconds

    def validate_journey_window(
        self,
        issue_time: datetime,
        departure_time: datetime,
        estimated_arrival_time: datetime
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates timing against forecast issue time and maximum supported horizon.
        Section 5.4: "When a journey extends beyond the forecast horizon, flag or reject it
        according to a documented policy. Do not silently extrapolate."
        """
        if departure_time < issue_time:
            return False, "departure_time_prior_to_forecast_issue_time"

        total_elapsed_lead_time_s = (estimated_arrival_time - issue_time).total_seconds()
        if total_elapsed_lead_time_s > self.max_horizon_seconds:
            exceeded_min = (total_elapsed_lead_time_s - self.max_horizon_seconds) / 60.0
            return False, (
                f"journey_exceeds_supported_forecast_horizon_by_{exceeded_min:.1f}_minutes "
                f"(max_horizon={self.max_horizon_seconds / 60:.0f}m)"
            )

        return True, None
