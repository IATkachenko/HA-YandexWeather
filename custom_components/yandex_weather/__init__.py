from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    ENTRY_NAME,
    UPDATER,
    UPDATES_PER_DAY,
    PLATFORMS,
    UPDATE_LISTENER,
    DEFAULT_UPDATES_PER_DAY,
)
from .updater import WeatherUpdater
from .config_flow import get_value

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    name = get_value(entry, CONF_NAME)
    api_key = get_value(entry, CONF_API_KEY)
    latitude = get_value(entry, CONF_LATITUDE, hass.config.latitude)
    longitude = get_value(entry, CONF_LONGITUDE, hass.config.longitude)
    updates_per_day = get_value(entry, UPDATES_PER_DAY, DEFAULT_UPDATES_PER_DAY)

    weather_updater = WeatherUpdater(
        latitude, longitude, api_key, hass, updates_per_day
    )

    await weather_updater.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        ENTRY_NAME: name,
        UPDATER: weather_updater,
    }

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    update_listener = entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = update_listener

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        update_listener = hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER]
        update_listener()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
