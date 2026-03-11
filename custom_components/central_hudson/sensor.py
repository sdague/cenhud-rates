"""Sensor platform for Central Hudson Electric Rates."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Central Hudson sensors from a config entry."""
    coordinator = CentralHudsonDataCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    rate_type = entry.data.get("rate_type", "residential")

    async_add_entities(
        [CentralHudsonElectricRateSensor(coordinator, rate_type)],
        True,
    )


class CentralHudsonDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Central Hudson data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="Central Hudson Electric Rates",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the prices JSON file."""
        try:
            data_file = Path(__file__).parent / "data" / "prices.json"

            if not data_file.exists():
                raise UpdateFailed(f"Prices data file not found: {data_file}")

            with open(data_file, "r") as f:
                data = json.load(f)

            _LOGGER.debug("Loaded price data: %s", data)
            return data

        except Exception as err:
            raise UpdateFailed(f"Error loading price data: {err}") from err


class CentralHudsonElectricRateSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Central Hudson Electric Rate sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "$/kWh"

    def __init__(
        self,
        coordinator: CentralHudsonDataCoordinator,
        rate_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._rate_type = rate_type
        self._attr_unique_id = f"central_hudson_{rate_type}_rate"
        self._attr_name = f"{rate_type.capitalize()} Electric Rate"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            rate_data = self.coordinator.data.get(self._rate_type, {})
            return rate_data.get("per_kwh")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        attrs = {
            "rate_type": self._rate_type,
            "last_updated": self.coordinator.data.get("last_updated"),
        }

        rate_data = self.coordinator.data.get(self._rate_type, {})
        if "note" in rate_data:
            attrs["note"] = rate_data["note"]

        return attrs

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:currency-usd"

# Made with Bob
