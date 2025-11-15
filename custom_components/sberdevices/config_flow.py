"""Config flow for SberDevices integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .api import SberAPI, async_create_sber_ssl_context
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("url"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    _client: SberAPI | None = None

    async def complete_external(self):
        await asyncio.sleep(10)
        await self.hass.config_entries.flow.async_configure(
            flow_id=self.flow_id, user_input={"test": 1}
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._client is None:
            ssl_context = await async_create_sber_ssl_context(self.hass)
            self._client = SberAPI(ssl_context=ssl_context)

        if not user_input:
            self.hass.async_create_task(self.complete_external())
            return self.async_external_step(
                step_id="user", url=self._client.create_authorization_url()
            )

        return self.async_external_step_done(next_step_id="finish")

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if self._client is None:
                ssl_context = await async_create_sber_ssl_context(self.hass)
                self._client = SberAPI(ssl_context=ssl_context)

            result = await self._client.authorize_by_url(user_input["url"])
            if not result:
                errors["base"] = "invalid_auth"
            return self.async_create_entry(
                title="SberDevices", data={"token": self._client.token}
            )

        return self.async_show_form(
            step_id="finish", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )