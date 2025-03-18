"""Yandex.Weather custom integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant

from .config_flow import get_value
from .const import (
    CONF_LANGUAGE_KEY,
    CONF_UPDATES_PER_DAY,
    DEFAULT_UPDATES_PER_DAY,
    DOMAIN,
    ENTRY_NAME,
    PLATFORMS,
    UPDATE_LISTENER,
    UPDATER,
    UPDATES_PER_DAY,
)
from .updater import WeatherUpdater

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up entry configured via user interface."""
    name = get_value(entry, CONF_NAME)
    api_key = get_value(entry, CONF_API_KEY)
    latitude = get_value(entry, CONF_LATITUDE, hass.config.latitude)
    longitude = get_value(entry, CONF_LONGITUDE, hass.config.longitude)
    updates_per_day = get_value(entry, UPDATES_PER_DAY, DEFAULT_UPDATES_PER_DAY)

    weather_updater = WeatherUpdater(
        latitude=latitude,
        longitude=longitude,
        api_key=api_key,
        hass=hass,
        device_id=entry.unique_id,
        language=get_value(entry, CONF_LANGUAGE_KEY, "EN"),
        updates_per_day=updates_per_day,
        name=name,
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        ENTRY_NAME: name,
        UPDATER: weather_updater,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    update_listener = entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER] = update_listener

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options for entry that was configured via user interface."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove entry configured via user interface."""
    unload_ok = True
    for platform in PLATFORMS:
        unload_ok = unload_ok & await hass.config_entries.async_forward_entry_unload(
            entry=entry, domain=platform
        )
    if unload_ok:
        update_listener = hass.data[DOMAIN][entry.entry_id][UPDATE_LISTENER]
        update_listener()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug(
        "Migrating configuration from version %s.%s",
        config_entry.version,
        config_entry.minor_version,
    )
    if config_entry.version < 4:
        # have no migration
        new_data = {**config_entry.data}
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, minor_version=0, version=4
        )

    if config_entry.version >= 4 and config_entry.minor_version < 5:
        new_options = {**config_entry.options}
        data = {**config_entry.data}
        new_data = data | new_options
        _LOGGER.warning(f"Going to update config {new_data}")
        new_updates_per_day = min(
            new_data[CONF_UPDATES_PER_DAY], DEFAULT_UPDATES_PER_DAY
        )
        _LOGGER.warning(
            f"Will set update per day to {new_updates_per_day} due to API limits"
        )
        new_data[CONF_UPDATES_PER_DAY] = new_updates_per_day
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, options=new_data, minor_version=4, version=5
        )
    return True
