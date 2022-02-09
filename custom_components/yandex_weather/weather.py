"""Weather component."""

from __future__ import annotations

from homeassistant.components.weather import WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PRESSURE_HPA, SPEED_METERS_PER_SECOND, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_API_CONDITION,
    ATTR_API_HUMIDITY,
    ATTR_API_IMAGE,
    ATTR_API_PRESSURE,
    ATTR_API_TEMPERATURE,
    ATTR_API_WIND_BEARING,
    ATTR_API_WIND_SPEED,
    DOMAIN,
    ENTRY_NAME,
    UPDATER,
)
from .updater import WeatherUpdater


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up weather "Yandex.Weather" weather entry."""
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    name = domain_data[ENTRY_NAME]
    updater = domain_data[UPDATER]

    unique_id = f"{config_entry.unique_id}"

    async_add_entities([YandexWeather(name, unique_id, updater, hass)], False)


class YandexWeather(WeatherEntity, CoordinatorEntity):
    """Yandex.Weather entry."""

    def __init__(self, name, unique_id, updater: WeatherUpdater, hass: HomeAssistant):
        """Initialize entry."""
        WeatherEntity.__init__(self)
        CoordinatorEntity.__init__(self, coordinator=updater)

        self.hass = hass
        self._updater = updater
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_wind_speed_unit = SPEED_METERS_PER_SECOND
        self._attr_pressure_unit = PRESSURE_HPA
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_device_info = self._updater.device_info

    async def async_update(self) -> None:
        """Update the entity."""
        await CoordinatorEntity.async_update(self)

        self._attr_temperature = self._updater.data["fact"].get(ATTR_API_TEMPERATURE)
        self._attr_condition = self._updater.data["fact"].get(ATTR_API_CONDITION)
        self._attr_pressure = self._updater.data["fact"].get(ATTR_API_PRESSURE)
        self._attr_humidity = self._updater.data["fact"].get(ATTR_API_HUMIDITY)
        self._attr_wind_speed = self._updater.data["fact"].get(ATTR_API_WIND_SPEED)
        self._attr_wind_bearing = self._updater.data["fact"].get(ATTR_API_WIND_BEARING)
        self._attr_entity_picture = f"https://yastatic.net/weather/i/icons/funky/dark/{self._updater.data['fact'].get(ATTR_API_IMAGE)}.svg"
