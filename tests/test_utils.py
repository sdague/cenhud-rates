"""Tests for Central Hudson utility functions."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from custom_components.central_hudson.utils import get_us_holidays, is_on_peak_time


def test_get_us_holidays_2026():
    """Test getting holidays for 2026."""
    holidays = get_us_holidays(2026)

    assert len(holidays) == 6
    assert date(2026, 1, 1) in holidays  # New Year's Day
    assert date(2026, 7, 4) in holidays  # Independence Day
    assert date(2026, 12, 25) in holidays  # Christmas
    assert date(2026, 5, 25) in holidays  # Memorial Day (last Monday in May)
    assert date(2026, 9, 7) in holidays  # Labor Day (first Monday in September)
    assert date(2026, 11, 26) in holidays  # Thanksgiving (4th Thursday in November)


def test_get_us_holidays_2025():
    """Test getting holidays for 2025."""
    holidays = get_us_holidays(2025)

    assert len(holidays) == 6
    assert date(2025, 1, 1) in holidays  # New Year's Day
    assert date(2025, 5, 26) in holidays  # Memorial Day
    assert date(2025, 7, 4) in holidays  # Independence Day
    assert date(2025, 9, 1) in holidays  # Labor Day
    assert date(2025, 11, 27) in holidays  # Thanksgiving
    assert date(2025, 12, 25) in holidays  # Christmas


def test_is_on_peak_weekday_during_peak():
    """Test on-peak detection during peak hours on weekday."""
    # Monday at 3pm
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(2026, 3, 16, 15, 0, 0, tzinfo=ny_tz)  # Monday, not a holiday

    assert is_on_peak_time(test_time) is True


def test_is_on_peak_weekday_before_peak():
    """Test off-peak before peak hours on weekday."""
    # Monday at 1pm
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(2026, 3, 16, 13, 0, 0, tzinfo=ny_tz)  # Monday, not a holiday

    assert is_on_peak_time(test_time) is False


def test_is_on_peak_weekday_after_peak():
    """Test off-peak after peak hours on weekday."""
    # Monday at 7pm
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(2026, 3, 16, 19, 0, 0, tzinfo=ny_tz)  # Monday, not a holiday

    assert is_on_peak_time(test_time) is False


def test_is_on_peak_weekend():
    """Test off-peak on weekend."""
    # Saturday at 3pm
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(2026, 3, 21, 15, 0, 0, tzinfo=ny_tz)  # Saturday

    assert is_on_peak_time(test_time) is False


def test_is_on_peak_new_years():
    """Test off-peak on New Year's Day during peak hours."""
    # New Year's Day at 3pm (would be on-peak if not a holiday)
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(2026, 1, 1, 15, 0, 0, tzinfo=ny_tz)  # Thursday, New Year's

    assert is_on_peak_time(test_time) is False


def test_is_on_peak_independence_day():
    """Test off-peak on Independence Day during peak hours."""
    # July 4th at 3pm (would be on-peak if not a holiday)
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(2026, 7, 4, 15, 0, 0, tzinfo=ny_tz)  # Saturday in 2026

    assert is_on_peak_time(test_time) is False


def test_is_on_peak_christmas():
    """Test off-peak on Christmas during peak hours."""
    # Christmas at 3pm (would be on-peak if not a holiday)
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(2026, 12, 25, 15, 0, 0, tzinfo=ny_tz)  # Friday in 2026

    assert is_on_peak_time(test_time) is False


def test_is_on_peak_memorial_day():
    """Test off-peak on Memorial Day during peak hours."""
    # Memorial Day 2026 at 3pm
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(2026, 5, 25, 15, 0, 0, tzinfo=ny_tz)  # Last Monday in May

    assert is_on_peak_time(test_time) is False


def test_is_on_peak_labor_day():
    """Test off-peak on Labor Day during peak hours."""
    # Labor Day 2026 at 3pm
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(
        2026, 9, 7, 15, 0, 0, tzinfo=ny_tz
    )  # First Monday in September

    assert is_on_peak_time(test_time) is False


def test_is_on_peak_thanksgiving():
    """Test off-peak on Thanksgiving during peak hours."""
    # Thanksgiving 2026 at 3pm
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(
        2026, 11, 26, 15, 0, 0, tzinfo=ny_tz
    )  # 4th Thursday in November

    assert is_on_peak_time(test_time) is False


def test_is_on_peak_boundary_start():
    """Test on-peak at start boundary (2pm)."""
    # Monday at 2pm
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(2026, 3, 16, 14, 0, 0, tzinfo=ny_tz)  # Monday, not a holiday

    assert is_on_peak_time(test_time) is True


def test_is_on_peak_boundary_end():
    """Test off-peak at end boundary (7pm)."""
    # Monday at 7pm
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(2026, 3, 16, 19, 0, 0, tzinfo=ny_tz)  # Monday, not a holiday

    assert is_on_peak_time(test_time) is False


def test_is_on_peak_friday():
    """Test on-peak on Friday during peak hours."""
    # Friday at 6pm
    ny_tz = ZoneInfo("America/New_York")
    test_time = datetime(2026, 3, 20, 18, 0, 0, tzinfo=ny_tz)  # Friday, not a holiday

    assert is_on_peak_time(test_time) is True


# Made with Bob
