from __future__ import annotations

from homeassistant.components.weather import WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PRESSURE_HPA, PRESSURE_INHG, TEMP_CELSIUS, SPEED_MILES_PER_HOUR, \
    SPEED_METERS_PER_SECOND, CONF_UNIT_SYSTEM_IMPERIAL, CONF_UNIT_SYSTEM_METRIC
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.pressure import convert as pressure_convert

from .const import (DOMAIN, ENTRY_NAME, UPDATER, MANUFACTURER, DEFAULT_NAME, ATTR_API_CONDITION, ATTR_API_TEMPERATURE,
                    ATTR_API_PRESSURE, ATTR_API_HUMIDITY, ATTR_API_WIND_SPEED, ATTR_API_WIND_BEARING, ATTR_API_IMAGE, )
from .updater import WeatherUpdater


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    name = domain_data[ENTRY_NAME]
    updater = domain_data[UPDATER]

    unique_id = f"{config_entry.unique_id}"

    async_add_entities([YandexWeather(name, unique_id, updater, hass)], False)


class YandexWeather(WeatherEntity):
    _attr_should_poll = False

    def __init__(self, name, unique_id, updater: WeatherUpdater, hass: HomeAssistant):
        super().__init__()
        self.hass = hass
        self._updater = updater
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_wind_speed_unit = SPEED_METERS_PER_SECOND if self.hass.config.units.name == CONF_UNIT_SYSTEM_METRIC \
            else SPEED_MILES_PER_HOUR
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, unique_id)},
            manufacturer=MANUFACTURER,
            name=DEFAULT_NAME,
            configuration_url=self._updater.weather_data['info']['url']
        )

    @property
    def entity_picture(self):
        return f"https://yastatic.net/weather/i/icons/funky/dark/{self._updater.weather_data['fact'][ATTR_API_IMAGE]}.svg"

    @property
    def condition(self) -> str | None:
        """:returns: the current condition."""
        return self._updater.weather_data['fact'][ATTR_API_CONDITION]

    @property
    def temperature(self) -> float | None:
        """:returns: The temperature."""
        return self._updater.weather_data['fact'][ATTR_API_TEMPERATURE]

    @property
    def pressure(self) -> float | None:
        """:returns: The pressure."""
        pressure = self._updater.weather_data['fact'][ATTR_API_PRESSURE]
        if self.hass.config.units.name == CONF_UNIT_SYSTEM_IMPERIAL:
            return pressure_convert(pressure, PRESSURE_HPA, PRESSURE_INHG)
        return pressure

    @property
    def humidity(self) -> float | None:
        """:returns: The humidity."""
        return self._updater.weather_data['fact'][ATTR_API_HUMIDITY]

    @property
    def wind_speed(self) -> float | None:
        """:returns: The wind speed."""
        wind_speed = self._updater.weather_data['fact'][ATTR_API_WIND_SPEED]
        if self.hass.config.units.name == CONF_UNIT_SYSTEM_IMPERIAL:
            return round(wind_speed * 2.24, 2)
        return wind_speed

    @property
    def wind_bearing(self) -> float | str | None:
        """Return the wind bearing."""
        return self._updater.weather_data['fact'][ATTR_API_WIND_BEARING]

    @property
    def available(self) -> bool:
        """:returns: True if entity is available."""
        return self._updater.last_update_success

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._updater.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Get the latest data from and updates the states."""
        await self._updater.async_request_refresh()
