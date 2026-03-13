"""Binary sensor platform for Central Hudson Electric Rates."""

from __future__ import annotations

import logging
from datetime import date, datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .sensor import CentralHudsonDataCoordinator
from .utils import get_us_holidays, is_on_peak_time

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Central Hudson binary sensors from a config entry."""
    # Get the coordinator from the sensor platform
    # We'll share the same coordinator instance
    coordinator = CentralHudsonDataCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    rate_type = entry.data.get("rate_type", "standard")

    # Only add the on-peak sensor for time_of_use customers
    if rate_type == "time_of_use":
        async_add_entities(
            [CentralHudsonOnPeakSensor(coordinator)],
            True,
        )


class CentralHudsonOnPeakSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that indicates if current time is on-peak."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CentralHudsonDataCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = "central_hudson_on_peak"
        self._attr_name = "On Peak Period"

    def _is_on_peak(self) -> bool:
        """Determine if current time is on-peak (Mon-Fri 2pm-7pm, excluding holidays)."""
        return is_on_peak_time()

    @property
    def is_on(self) -> bool:
        """Return true if currently in on-peak period."""
        return self._is_on_peak()

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self.is_on:
            return "mdi:clock-alert"
        return "mdi:clock-outline"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return additional state attributes."""
        now = datetime.now()
        today = now.date()
        holidays = get_us_holidays(now.year)
        is_holiday = today in holidays

        attrs = {
            "on_peak_hours": "Mon-Fri 2pm-7pm (excluding holidays)",
            "current_day": now.strftime("%A"),
            "current_time": now.strftime("%I:%M %p"),
            "is_holiday": str(is_holiday),
        }

        # If it's a holiday, indicate which one
        if is_holiday:
            holiday_names = {
                date(now.year, 1, 1): "New Year's Day",
                date(now.year, 7, 4): "Independence Day",
                date(now.year, 12, 25): "Christmas",
            }
            # Add calculated holidays
            for holiday in holidays:
                if holiday.month == 5 and holiday not in holiday_names:
                    holiday_names[holiday] = "Memorial Day"
                elif holiday.month == 9 and holiday not in holiday_names:
                    holiday_names[holiday] = "Labor Day"
                elif holiday.month == 11 and holiday not in holiday_names:
                    holiday_names[holiday] = "Thanksgiving"

            attrs["holiday_name"] = holiday_names.get(today, "Holiday")

        return attrs


# Made with Bob
