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
        "last_updated": "2026-03-11T16:18:00-04:00",
        "residential": {
            "per_kwh": 0.15,
        },
        "commercial": {
            "per_kwh": 0.12,
        },
    }


@pytest.fixture
def mock_coordinator(hass: HomeAssistant, mock_prices_data):
    """Return a mock coordinator with test data."""
    coordinator = CentralHudsonDataCoordinator(hass)
    coordinator.data = mock_prices_data
    return coordinator


async def test_coordinator_update_success(hass: HomeAssistant, mock_prices_data, tmp_path):
    """Test successful data update."""
    # Create temporary prices file
    data_file = tmp_path / "prices.json"
    data_file.write_text(json.dumps(mock_prices_data))

    coordinator = CentralHudsonDataCoordinator(hass)

    with patch.object(Path, "parent", return_value=tmp_path):
        data = await coordinator._async_update_data()

    assert data == mock_prices_data
    assert data["residential"]["per_kwh"] == 0.15


async def test_coordinator_update_file_not_found(hass: HomeAssistant):
    """Test update when file doesn't exist."""
    coordinator = CentralHudsonDataCoordinator(hass)

    with patch.object(Path, "exists", return_value=False):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


async def test_sensor_residential_rate(mock_coordinator):
    """Test residential rate sensor."""
    sensor = CentralHudsonElectricRateSensor(mock_coordinator, "residential")

    assert sensor.native_value == 0.15
    assert sensor.name == "Residential Electric Rate"
    assert sensor.unique_id == "central_hudson_residential_rate"
    assert sensor.native_unit_of_measurement == "$/kWh"


async def test_sensor_commercial_rate(mock_coordinator):
    """Test commercial rate sensor."""
    sensor = CentralHudsonElectricRateSensor(mock_coordinator, "commercial")

    assert sensor.native_value == 0.12
    assert sensor.name == "Commercial Electric Rate"
    assert sensor.unique_id == "central_hudson_commercial_rate"


async def test_sensor_attributes(mock_coordinator):
    """Test sensor extra state attributes."""
    sensor = CentralHudsonElectricRateSensor(mock_coordinator, "residential")

    attrs = sensor.extra_state_attributes
    assert attrs["rate_type"] == "residential"
    assert attrs["last_updated"] == "2026-03-11T16:18:00-04:00"


async def test_sensor_no_data(hass: HomeAssistant):
    """Test sensor when coordinator has no data."""
    coordinator = CentralHudsonDataCoordinator(hass)
    coordinator.data = None

    sensor = CentralHudsonElectricRateSensor(coordinator, "residential")

    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {}


async def test_sensor_icon(mock_coordinator):
    """Test sensor icon."""
    sensor = CentralHudsonElectricRateSensor(mock_coordinator, "residential")

    assert sensor.icon == "mdi:currency-usd"
