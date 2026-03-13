"""Tests for Central Hudson utility functions."""

from datetime import date, datetime
from unittest.mock import Mock, patch

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
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 3, 16)  # Monday, not a holiday
    mock_now.year = 2026
    mock_now.weekday.return_value = 0  # Monday
    mock_now.hour = 15

    assert is_on_peak_time(mock_now) is True


def test_is_on_peak_weekday_before_peak():
    """Test off-peak before peak hours on weekday."""
    # Monday at 1pm
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 3, 16)  # Monday, not a holiday
    mock_now.year = 2026
    mock_now.weekday.return_value = 0  # Monday
    mock_now.hour = 13

    assert is_on_peak_time(mock_now) is False


def test_is_on_peak_weekday_after_peak():
    """Test off-peak after peak hours on weekday."""
    # Monday at 7pm
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 3, 16)  # Monday, not a holiday
    mock_now.year = 2026
    mock_now.weekday.return_value = 0  # Monday
    mock_now.hour = 19

    assert is_on_peak_time(mock_now) is False


def test_is_on_peak_weekend():
    """Test off-peak on weekend."""
    # Saturday at 3pm
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 3, 21)  # Saturday
    mock_now.year = 2026
    mock_now.weekday.return_value = 5  # Saturday
    mock_now.hour = 15

    assert is_on_peak_time(mock_now) is False


def test_is_on_peak_new_years():
    """Test off-peak on New Year's Day during peak hours."""
    # New Year's Day at 3pm (would be on-peak if not a holiday)
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 1, 1)  # Thursday, New Year's
    mock_now.year = 2026
    mock_now.weekday.return_value = 3  # Thursday
    mock_now.hour = 15

    assert is_on_peak_time(mock_now) is False


def test_is_on_peak_independence_day():
    """Test off-peak on Independence Day during peak hours."""
    # July 4th at 3pm (would be on-peak if not a holiday)
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 7, 4)  # Saturday in 2026
    mock_now.year = 2026
    mock_now.weekday.return_value = 5  # Saturday
    mock_now.hour = 15

    assert is_on_peak_time(mock_now) is False


def test_is_on_peak_christmas():
    """Test off-peak on Christmas during peak hours."""
    # Christmas at 3pm (would be on-peak if not a holiday)
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 12, 25)  # Friday in 2026
    mock_now.year = 2026
    mock_now.weekday.return_value = 4  # Friday
    mock_now.hour = 15

    assert is_on_peak_time(mock_now) is False


def test_is_on_peak_memorial_day():
    """Test off-peak on Memorial Day during peak hours."""
    # Memorial Day 2026 at 3pm
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 5, 25)  # Last Monday in May
    mock_now.year = 2026
    mock_now.weekday.return_value = 0  # Monday
    mock_now.hour = 15

    assert is_on_peak_time(mock_now) is False


def test_is_on_peak_labor_day():
    """Test off-peak on Labor Day during peak hours."""
    # Labor Day 2026 at 3pm
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 9, 7)  # First Monday in September
    mock_now.year = 2026
    mock_now.weekday.return_value = 0  # Monday
    mock_now.hour = 15

    assert is_on_peak_time(mock_now) is False


def test_is_on_peak_thanksgiving():
    """Test off-peak on Thanksgiving during peak hours."""
    # Thanksgiving 2026 at 3pm
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 11, 26)  # 4th Thursday in November
    mock_now.year = 2026
    mock_now.weekday.return_value = 3  # Thursday
    mock_now.hour = 15

    assert is_on_peak_time(mock_now) is False


def test_is_on_peak_boundary_start():
    """Test on-peak at start boundary (2pm)."""
    # Monday at 2pm
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 3, 16)  # Monday, not a holiday
    mock_now.year = 2026
    mock_now.weekday.return_value = 0  # Monday
    mock_now.hour = 14

    assert is_on_peak_time(mock_now) is True


def test_is_on_peak_boundary_end():
    """Test off-peak at end boundary (7pm)."""
    # Monday at 7pm
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 3, 16)  # Monday, not a holiday
    mock_now.year = 2026
    mock_now.weekday.return_value = 0  # Monday
    mock_now.hour = 19

    assert is_on_peak_time(mock_now) is False


def test_is_on_peak_friday():
    """Test on-peak on Friday during peak hours."""
    # Friday at 6pm
    mock_now = Mock()
    mock_now.date.return_value = date(2026, 3, 20)  # Friday, not a holiday
    mock_now.year = 2026
    mock_now.weekday.return_value = 4  # Friday
    mock_now.hour = 18

    assert is_on_peak_time(mock_now) is True

# Made with Bob
