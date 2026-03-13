"""Sensor platform for Central Hudson Electric Rates."""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .utils import is_on_peak_time

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

    rate_type = entry.data.get("rate_type", "standard")

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

            with open(data_file) as f:
                raw_data = json.load(f)

            # Get the most recent rate entry
            if "rates" in raw_data and raw_data["rates"]:
                # Sort by effective_date to get the most recent
                sorted_rates = sorted(
                    raw_data["rates"],
                    key=lambda x: x.get("effective_date", ""),
                    reverse=True,
                )
                current_rate = sorted_rates[0]

                # Combine with customer charge
                data = {
                    "customer_charge": raw_data.get("customer_charge"),
                    "effective_date": current_rate.get("effective_date"),
                    "last_updated": current_rate.get("last_updated"),
                    "standard": current_rate.get("standard", {}),
                    "time_of_use": current_rate.get("time_of_use", {}),
                    "historical_rates": raw_data["rates"],  # Keep all historical data
                }
            else:
                # Fallback for old format
                data = raw_data

            _LOGGER.debug(
                "Loaded current price data from %s", data.get("effective_date")
            )
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

        # Set name based on rate type
        if rate_type == "time_of_use":
            self._attr_name = "Current Electric Rate"
        else:
            self._attr_name = f"{rate_type.capitalize()} Electric Rate"

    def _is_on_peak(self) -> bool:
        """Determine if current time is on-peak (Mon-Fri 2pm-7pm, excluding holidays)."""
        return is_on_peak_time()

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        # Handle different rate types
        if self._rate_type == "standard":
            rate_data = self.coordinator.data.get("standard", {})
            return rate_data.get("total_per_kwh")
        elif self._rate_type == "time_of_use":
            # Automatically return on-peak or off-peak based on current time
            tou_data = self.coordinator.data.get("time_of_use", {})
            if self._is_on_peak():
                rate_data = tou_data.get("on_peak", {})
            else:
                rate_data = tou_data.get("off_peak", {})
            return rate_data.get("total_per_kwh")
        elif self._rate_type in ["on_peak", "off_peak"]:
            # Legacy support for specific rate type selection
            tou_data = self.coordinator.data.get("time_of_use", {})
            rate_data = tou_data.get(self._rate_type, {})
            return rate_data.get("total_per_kwh")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        attrs = {
            "rate_type": self._rate_type,
            "last_updated": self.coordinator.data.get("last_updated"),
            "effective_date": self.coordinator.data.get("effective_date"),
            "customer_charge": self.coordinator.data.get("customer_charge"),
        }

        # Get rate details based on rate type
        if self._rate_type == "standard":
            rate_data = self.coordinator.data.get("standard", {})
        elif self._rate_type == "time_of_use":
            # Show current rate details based on time
            tou_data = self.coordinator.data.get("time_of_use", {})
            is_on_peak = self._is_on_peak()

            if is_on_peak:
                rate_data = tou_data.get("on_peak", {})
                attrs["current_period"] = "on_peak"
            else:
                rate_data = tou_data.get("off_peak", {})
                attrs["current_period"] = "off_peak"

            # Also include both rates for reference
            attrs["on_peak_rate"] = tou_data.get("on_peak", {}).get("total_per_kwh")
            attrs["off_peak_rate"] = tou_data.get("off_peak", {}).get("total_per_kwh")
            attrs["on_peak_hours"] = "Mon-Fri 2pm-7pm"
        elif self._rate_type in ["on_peak", "off_peak"]:
            tou_data = self.coordinator.data.get("time_of_use", {})
            rate_data = tou_data.get(self._rate_type, {})
        else:
            rate_data = {}

        if "description" in rate_data:
            attrs["description"] = rate_data["description"]
        if "supply_charge" in rate_data:
            attrs["supply_charge"] = rate_data["supply_charge"]
        if "delivery_charge" in rate_data:
            attrs["delivery_charge"] = rate_data["delivery_charge"]

        return attrs

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:currency-usd"
