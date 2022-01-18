from __future__ import annotations

import voluptuous as vol
import logging
from .updater import WeatherUpdater

from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
)
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_UPDATES_PER_DAY,
    DEFAULT_UPDATES_PER_DAY,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class YandexWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return YandexWeatherOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            latitude = user_input[CONF_LATITUDE]
            longitude = user_input[CONF_LONGITUDE]

            await self.async_set_unique_id(f"{latitude}-{longitude}")
            self._abort_if_unique_id_configured()

            if await _is_online(user_input[CONF_API_KEY], latitude, longitude, self.hass):
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Optional(
                    CONF_LATITUDE, default=self.hass.config.latitude
                ): cv.latitude,
                vol.Optional(
                    CONF_LONGITUDE, default=self.hass.config.longitude
                ): cv.longitude,
                vol.Optional(CONF_UPDATES_PER_DAY, default=DEFAULT_UPDATES_PER_DAY): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class YandexWeatherOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    def _get_options_schema(self):
        return vol.Schema(
            {
                vol.Required(
                    CONF_API_KEY,
                    default=self._get_value(CONF_API_KEY)): str,
                vol.Optional(
                    CONF_UPDATES_PER_DAY,
                    default=self._get_value(CONF_UPDATES_PER_DAY, DEFAULT_UPDATES_PER_DAY)
                ): int,
            }
        )

    def _get_value(self, param: str, default: str | None = None):
        """Get current value for configuration parameter

        :param param: str: parameter name for getting value
        :param default: str|None: default value for parameter, defaults to None
        :returns: parameter value, or default value or None
        """
        return self.config_entry.options.get(param, self.config_entry.data.get(param, default))


async def _is_online(api_key, lat, lon, hass: HomeAssistant) -> bool:
    weather = WeatherUpdater(lat, lon, api_key, hass)
    await weather.async_request_refresh()
    return True if 'fact' in weather.weather_data.keys() else False
