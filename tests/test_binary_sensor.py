"""Tests for Central Hudson binary sensor platform."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.central_hudson.binary_sensor import (
    CentralHudsonOnPeakSensor,
    async_setup_entry,
)
from custom_components.central_hudson.sensor import CentralHudsonDataCoordinator


@pytest.fixture
def mock_coordinator(hass):
    """Create a mock coordinator."""
    coordinator = CentralHudsonDataCoordinator(hass)
    coordinator.data = {
        "customer_charge": 22.50,
        "effective_date": "2026-03-01",
        "last_updated": "2026-03-11T16:18:00-04:00",
        "standard": {
            "supply_charge": 0.10,
            "delivery_charge": 0.05,
            "total_per_kwh": 0.15,
        },
        "time_of_use": {
            "on_peak": {"total_per_kwh": 0.17},
            "off_peak": {"total_per_kwh": 0.12},
        },
    }
    return coordinator


@pytest.mark.asyncio
async def test_binary_sensor_setup_time_of_use(hass: HomeAssistant):
    """Test binary sensor is created for time_of_use rate type."""
    entry = Mock()
    entry.data = {"rate_type": "time_of_use"}

    entities = []

    def mock_add_entities(new_entities, update_before_add=True):
        entities.extend(new_entities)

    with patch(
        "custom_components.central_hudson.binary_sensor.CentralHudsonDataCoordinator"
    ) as mock_coord_class:
        mock_coordinator = Mock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coord_class.return_value = mock_coordinator

        await async_setup_entry(hass, entry, mock_add_entities)

    assert len(entities) == 1
    assert isinstance(entities[0], CentralHudsonOnPeakSensor)


@pytest.mark.asyncio
async def test_binary_sensor_not_setup_for_standard(hass: HomeAssistant):
    """Test binary sensor is NOT created for standard rate type."""
    entry = Mock()
    entry.data = {"rate_type": "standard"}

    entities = []

    def mock_add_entities(new_entities, update_before_add=True):
        entities.extend(new_entities)

    with patch(
        "custom_components.central_hudson.binary_sensor.CentralHudsonDataCoordinator"
    ) as mock_coord_class:
        mock_coordinator = Mock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coord_class.return_value = mock_coordinator

        await async_setup_entry(hass, entry, mock_add_entities)

    assert len(entities) == 0


def test_on_peak_weekday_during_peak_hours(mock_coordinator):
    """Test sensor returns True during on-peak hours on weekday."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Monday at 3pm (15:00)
    test_time = datetime(2026, 3, 16, 15, 0)  # Monday, not a holiday
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is True


def test_on_peak_weekday_before_peak_hours(mock_coordinator):
    """Test sensor returns False before on-peak hours on weekday."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Monday at 1pm (13:00)
    test_time = datetime(2026, 3, 16, 13, 0)  # Monday, not a holiday
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is False


def test_on_peak_weekday_after_peak_hours(mock_coordinator):
    """Test sensor returns False after on-peak hours on weekday."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Monday at 7pm (19:00)
    test_time = datetime(2026, 3, 16, 19, 0)  # Monday, not a holiday
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is False


def test_on_peak_weekend(mock_coordinator):
    """Test sensor returns False on weekends."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Saturday at 3pm (15:00) - should be off-peak even during peak hours
    test_time = datetime(2026, 3, 21, 15, 0)  # Saturday
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is False


def test_on_peak_friday_during_peak(mock_coordinator):
    """Test sensor returns True on Friday during peak hours."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Friday at 6pm (18:00)
    test_time = datetime(2026, 3, 20, 18, 0)  # Friday, not a holiday
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is True


def test_on_peak_boundary_start(mock_coordinator):
    """Test sensor at start boundary (2pm)."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Monday at 2pm (14:00) - should be on-peak
    test_time = datetime(2026, 3, 16, 14, 0)  # Monday, not a holiday
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is True


def test_on_peak_boundary_end(mock_coordinator):
    """Test sensor at end boundary (7pm)."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Monday at 7pm (19:00) - should be off-peak
    test_time = datetime(2026, 3, 16, 19, 0)  # Monday, not a holiday
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is False


def test_binary_sensor_icon_on_peak(mock_coordinator):
    """Test icon changes based on on-peak status."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # During on-peak
    test_time = datetime(2026, 3, 16, 15, 0)  # Monday at 3pm
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.icon == "mdi:clock-alert"


def test_binary_sensor_icon_off_peak(mock_coordinator):
    """Test icon during off-peak."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # During off-peak
    test_time = datetime(2026, 3, 21, 15, 0)  # Saturday at 3pm
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.icon == "mdi:clock-outline"


def test_binary_sensor_attributes(mock_coordinator):
    """Test binary sensor attributes."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    test_time = datetime(2026, 3, 16, 15, 0)  # Monday at 3pm
    with patch("custom_components.central_hudson.binary_sensor.datetime") as mock_dt:
        mock_dt.now.return_value = test_time
        attrs = sensor.extra_state_attributes

        assert "on_peak_hours" in attrs
        assert "Mon-Fri 2pm-7pm" in attrs["on_peak_hours"]
        assert attrs["current_day"] == "Monday"
        assert attrs["current_time"] == "03:00 PM"
        assert attrs["is_holiday"] == "False"


def test_binary_sensor_unique_id(mock_coordinator):
    """Test binary sensor has correct unique_id."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)
    assert sensor.unique_id == "central_hudson_on_peak"


def test_binary_sensor_name(mock_coordinator):
    """Test binary sensor has correct name."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)
    assert sensor.name == "On Peak Period"


def test_on_peak_new_years_day(mock_coordinator):
    """Test sensor returns False on New Year's Day during peak hours."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Thursday, January 1, 2026 at 3pm (would be on-peak if not a holiday)
    test_time = datetime(2026, 1, 1, 15, 0)
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is False


def test_on_peak_independence_day(mock_coordinator):
    """Test sensor returns False on Independence Day during peak hours."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Friday, July 4, 2025 at 3pm (would be on-peak if not a holiday)
    test_time = datetime(2025, 7, 4, 15, 0)
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is False


def test_on_peak_christmas(mock_coordinator):
    """Test sensor returns False on Christmas during peak hours."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Friday, December 25, 2026 at 3pm (would be on-peak if not a holiday)
    test_time = datetime(2026, 12, 25, 15, 0)
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is False


def test_on_peak_memorial_day(mock_coordinator):
    """Test sensor returns False on Memorial Day during peak hours."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Monday, May 25, 2026 at 3pm (would be on-peak if not a holiday)
    test_time = datetime(2026, 5, 25, 15, 0)
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is False


def test_on_peak_labor_day(mock_coordinator):
    """Test sensor returns False on Labor Day during peak hours."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Monday, September 7, 2026 at 3pm (would be on-peak if not a holiday)
    test_time = datetime(2026, 9, 7, 15, 0)
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is False


def test_on_peak_thanksgiving(mock_coordinator):
    """Test sensor returns False on Thanksgiving during peak hours."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Thursday, November 26, 2026 at 3pm (would be on-peak if not a holiday)
    test_time = datetime(2026, 11, 26, 15, 0)
    with patch("custom_components.central_hudson.utils.dt_util.now") as mock_now:
        mock_now.return_value = test_time
        assert sensor.is_on is False


def test_on_peak_holiday_attribute(mock_coordinator):
    """Test holiday attribute is set correctly on holidays."""
    sensor = CentralHudsonOnPeakSensor(mock_coordinator)

    # Christmas
    test_time = datetime(2026, 12, 25, 15, 0)
    with patch("custom_components.central_hudson.binary_sensor.datetime") as mock_dt:
        mock_dt.now.return_value = test_time
        attrs = sensor.extra_state_attributes

        assert attrs["is_holiday"] == "True"
        assert attrs["holiday_name"] == "Christmas"


# Made with Bob
