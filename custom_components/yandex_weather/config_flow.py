"""Configuration flows."""

from __future__ import annotations

import logging

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    CONDITION_IMAGE,
    CONF_IMAGE_SOURCE,
    CONF_LANGUAGE_KEY,
    CONF_UPDATES_PER_DAY,
    DEFAULT_NAME,
    DEFAULT_UPDATES_PER_DAY,
    DOMAIN,
)
from .updater import WeatherUpdater

_LOGGER = logging.getLogger(__name__)


def get_supported_languages() -> list[str]:
    """Get supported translations."""
    return ["EN", "RU"]


def get_value(config_entry: config_entries | None, param: str, default=None):
    """Get current value for configuration parameter.

    :param config_entry: config_entries|None: config entry from Flow
    :param param: str: parameter name for getting value
    :param default: default value for parameter, defaults to None
    :returns: parameter value, or default value or None
    """
    if config_entry is not None:
        return config_entry.options.get(param, config_entry.data.get(param, default))
    else:
        return default


class YandexWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """First time set up flow."""

    VERSION = 4
    MINOR_VERSION = 4

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return YandexWeatherOptionsFlow()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            latitude = user_input[CONF_LATITUDE]
            longitude = user_input[CONF_LONGITUDE]

            await self.async_set_unique_id(f"{latitude}-{longitude}")
            self._abort_if_unique_id_configured()

            if await _is_online(
                user_input[CONF_API_KEY], latitude, longitude, self.hass
            ):
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            else:
                errors["base"] = "could_not_get_data"

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
                vol.Optional(
                    CONF_UPDATES_PER_DAY, default=DEFAULT_UPDATES_PER_DAY
                ): int,
                vol.Required(
                    CONF_LANGUAGE_KEY, default=get_supported_languages()[0]
                ): vol.In(get_supported_languages()),
                vol.Optional(CONF_IMAGE_SOURCE, default="Yandex"): vol.In(
                    CONDITION_IMAGE.keys()
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class YandexWeatherOptionsFlow(config_entries.OptionsFlow):
    """Changing options flow."""

    @property
    def config_entry(self):
        return self.hass.config_entries.async_get_entry(self.handler)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        if user_input is not None:
            if await _is_online(
                user_input[CONF_API_KEY],
                get_value(self.config_entry, CONF_LATITUDE),
                get_value(self.config_entry, CONF_LONGITUDE),
                self.hass,
            ):
                return self.async_create_entry(title="", data=user_input)
            else:
                errors["base"] = "could_not_get_data"

        return self.async_show_form(
            step_id="init", data_schema=self._get_options_schema(), errors=errors
        )

    def _get_options_schema(self):
        return vol.Schema(
            {
                vol.Required(
                    CONF_API_KEY, default=get_value(self.config_entry, CONF_API_KEY)
                ): str,
                vol.Required(
                    CONF_LANGUAGE_KEY,
                    default=get_value(self.config_entry, CONF_LANGUAGE_KEY),
                ): vol.In(get_supported_languages()),
                vol.Optional(
                    CONF_UPDATES_PER_DAY,
                    default=get_value(
                        self.config_entry, CONF_UPDATES_PER_DAY, DEFAULT_UPDATES_PER_DAY
                    ),
                ): int,
                vol.Optional(
                    CONF_IMAGE_SOURCE,
                    default=get_value(self.config_entry, CONF_IMAGE_SOURCE, "Yandex"),
                ): vol.In(CONDITION_IMAGE.keys()),
            }
        )


async def _is_online(api_key, lat, lon, hass: HomeAssistant) -> bool:
    weather = WeatherUpdater(lat, lon, api_key, hass, "config_flow_test_id")
    await weather.async_request_refresh()
    return weather.last_update_success
