"""Tests for the Central Hudson sensor platform."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.central_hudson.sensor import (
    CentralHudsonDataCoordinator,
    CentralHudsonElectricRateSensor,
)


@pytest.fixture
def mock_prices_data():
    """Return mock price data."""
    return {
        "customer_charge": 18.00,
        "effective_date": "2026-03-01",
        "last_updated": "2026-03-11T16:18:00-04:00",
        "standard": {
            "supply_charge": 0.10,
            "delivery_charge": 0.05,
            "total_per_kwh": 0.15,
        },
        "time_of_use": {
            "on_peak": {
                "supply_charge": 0.12,
                "delivery_charge": 0.05,
                "total_per_kwh": 0.17,
            },
            "off_peak": {
                "supply_charge": 0.07,
                "delivery_charge": 0.05,
                "total_per_kwh": 0.12,
            },
        },
    }


@pytest.fixture
async def mock_coordinator(hass: HomeAssistant, mock_prices_data):
    """Return a mock coordinator with test data."""
    coordinator = CentralHudsonDataCoordinator(hass)
    coordinator.data = mock_prices_data
    return coordinator


@pytest.mark.asyncio
async def test_coordinator_update_success(
    hass: HomeAssistant, mock_prices_data, tmp_path
):
    """Test successful data update."""
    # Create temporary prices file with the new format (rates array)
    data_file = tmp_path / "data" / "prices.json"
    data_file.parent.mkdir(parents=True, exist_ok=True)

    # Wrap in rates array format
    file_data = {"customer_charge": 18.00, "rates": [mock_prices_data]}
    data_file.write_text(json.dumps(file_data))

    coordinator = CentralHudsonDataCoordinator(hass)

    # Mock the __file__ path to point to our temp directory
    with patch(
        "custom_components.central_hudson.sensor.__file__", str(tmp_path / "sensor.py")
    ):
        data = await coordinator._async_update_data()

    assert data["standard"]["total_per_kwh"] == 0.15
    assert data["effective_date"] == "2026-03-01"


@pytest.mark.asyncio
async def test_coordinator_update_file_not_found(hass: HomeAssistant):
    """Test update when file doesn't exist."""
    coordinator = CentralHudsonDataCoordinator(hass)

    with patch.object(Path, "exists", return_value=False):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_sensor_standard_rate(mock_coordinator):
    """Test standard rate sensor."""
    sensor = CentralHudsonElectricRateSensor(mock_coordinator, "standard")

    assert sensor.native_value == 0.15
    assert sensor.name == "Standard Electric Rate"
    assert sensor.unique_id == "central_hudson_standard_rate"
    assert sensor.native_unit_of_measurement == "$/kWh"


@pytest.mark.asyncio
async def test_sensor_time_of_use_rate(mock_coordinator):
    """Test time-of-use rate sensor."""
    sensor = CentralHudsonElectricRateSensor(mock_coordinator, "time_of_use")

    # Should return off-peak rate by default (not during 2pm-7pm Mon-Fri)
    assert sensor.native_value == 0.12
    assert sensor.name == "Current Electric Rate"
    assert sensor.unique_id == "central_hudson_time_of_use_rate"


@pytest.mark.asyncio
async def test_sensor_attributes(mock_coordinator):
    """Test sensor extra state attributes."""
    sensor = CentralHudsonElectricRateSensor(mock_coordinator, "standard")

    attrs = sensor.extra_state_attributes
    assert attrs["rate_type"] == "standard"
    assert attrs["last_updated"] == "2026-03-11T16:18:00-04:00"
    assert attrs["supply_charge"] == 0.10
    assert attrs["delivery_charge"] == 0.05


@pytest.mark.asyncio
async def test_sensor_no_data(hass: HomeAssistant):
    """Test sensor when coordinator has no data."""
    coordinator = CentralHudsonDataCoordinator(hass)
    coordinator.data = None

    sensor = CentralHudsonElectricRateSensor(coordinator, "residential")

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


@pytest.mark.asyncio
async def test_sensor_icon(mock_coordinator):
    """Test sensor icon."""
    sensor = CentralHudsonElectricRateSensor(mock_coordinator, "residential")

    assert sensor.icon == "mdi:currency-usd"
