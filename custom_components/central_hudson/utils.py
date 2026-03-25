"""Utility functions for Central Hudson integration."""

from datetime import date
from zoneinfo import ZoneInfo

from homeassistant.util import dt as dt_util


def get_us_holidays(year: int) -> list[date]:
    """Get list of US holidays that are always off-peak for the given year.

    Returns holidays for:
    - New Year's Day (January 1)
    - Memorial Day (Last Monday in May)
    - Independence Day (July 4)
    - Labor Day (First Monday in September)
    - Thanksgiving (Fourth Thursday in November)
    - Christmas (December 25)
    """
    holidays = [
        date(year, 1, 1),  # New Year's Day
        date(year, 7, 4),  # Independence Day
        date(year, 12, 25),  # Christmas
    ]

    # Memorial Day - Last Monday in May
    memorial_day = date(year, 5, 31)
    while memorial_day.weekday() != 0:  # 0 = Monday
        memorial_day = date(year, memorial_day.month, memorial_day.day - 1)
    holidays.append(memorial_day)

    # Labor Day - First Monday in September
    labor_day = date(year, 9, 1)
    while labor_day.weekday() != 0:  # 0 = Monday
        labor_day = date(year, labor_day.month, labor_day.day + 1)
    holidays.append(labor_day)

    # Thanksgiving - Fourth Thursday in November
    thanksgiving = date(year, 11, 1)
    thursdays = 0
    while thursdays < 4:
        if thanksgiving.weekday() == 3:  # 3 = Thursday
            thursdays += 1
            if thursdays < 4:
                thanksgiving = date(year, thanksgiving.month, thanksgiving.day + 1)
        else:
            thanksgiving = date(year, thanksgiving.month, thanksgiving.day + 1)
    holidays.append(thanksgiving)

    return holidays


def is_on_peak_time(now=None) -> bool:
    """Determine if given datetime is on-peak (Mon-Fri 2pm-7pm, excluding holidays).

    Args:
        now: datetime object to check (defaults to current time in New York timezone)

    Returns:
        True if on-peak, False otherwise
    """
    ny_tz = ZoneInfo("America/New_York")

    if now is None:
        now = dt_util.now(ny_tz)
    else:
        # Convert to New York timezone if not already
        now = now.astimezone(ny_tz)

    # Check if it's a holiday (always off-peak)
    today = now.date()
    holidays = get_us_holidays(now.year)
    if today in holidays:
        return False

    # Check if weekday (Monday=0, Friday=4)
    if now.weekday() > 4:  # Saturday=5, Sunday=6
        return False

    # Check if between 2pm (14:00) and 7pm (19:00)
    hour = now.hour
    return 14 <= hour < 19


# Made with Bob
