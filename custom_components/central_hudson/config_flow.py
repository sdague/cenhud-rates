"""Config flow for Central Hudson Electric Rates integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

DOMAIN = "central_hudson"

RATE_TYPES = {
    "standard": "Standard Rate - Fixed rate for all hours",
    "time_of_use": "Time-of-Use - Automatic (Recommended for TOU customers)",
}


class CentralHudsonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Central Hudson Electric Rates."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(f"central_hudson_{user_input['rate_type']}")
            self._abort_if_unique_id_configured()

            # Create a friendly title
            rate_type = user_input["rate_type"]
            if rate_type == "standard":
                title = "Central Hudson - Standard Rate"
            else:
                title = "Central Hudson - Time-of-Use"

            return self.async_create_entry(
                title=title,
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required("rate_type", default="time_of_use"): vol.In(RATE_TYPES),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )
