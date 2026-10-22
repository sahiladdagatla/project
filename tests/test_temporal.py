from datetime import datetime, timezone, timedelta
from backend.app.core.temporal import parse_iso_timestamp, format_iso_timestamp, ForecastHorizonValidator


def test_iso_parsing_and_formatting():
    dt_str = "2026-07-15T06:00:00Z"
    dt = parse_iso_timestamp(dt_str)
    assert dt.year == 2026
    assert dt.month == 7
    assert dt.day == 15
    assert dt.hour == 6
    assert format_iso_timestamp(dt) == "2026-07-15T06:00:00Z"


def test_forecast_horizon_validation():
    validator = ForecastHorizonValidator(max_horizon_seconds=180 * 60)  # 3 hours
    issue_time = datetime(2026, 7, 15, 6, 0, 0, tzinfo=timezone.utc)
    dep_time = datetime(2026, 7, 15, 7, 0, 0, tzinfo=timezone.utc)

    # Valid: journey ends at 8:30 (total 2.5 hours from issue)
    arr_valid = datetime(2026, 7, 15, 8, 30, 0, tzinfo=timezone.utc)
    is_valid, msg = validator.validate_journey_window(issue_time, dep_time, arr_valid)
    assert is_valid is True
    assert msg is None

    # Invalid: journey ends at 9:30 (3.5 hours from issue, exceeding 3-hour limit)
    arr_invalid = datetime(2026, 7, 15, 9, 30, 0, tzinfo=timezone.utc)
    is_valid, msg = validator.validate_journey_window(issue_time, dep_time, arr_invalid)
    assert is_valid is False
    assert "journey_exceeds_supported_forecast_horizon" in msg
