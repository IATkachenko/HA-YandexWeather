"""Weather component."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

from homeassistant.components.weather import (
    ATTR_FORECAST,
    ATTR_WEATHER_PRECIPITATION_UNIT,
    ATTR_WEATHER_PRESSURE_UNIT,
    ATTR_WEATHER_TEMPERATURE_UNIT,
    ATTR_WEATHER_WIND_SPEED_UNIT,
    UNIT_CONVERSIONS,
    WeatherEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    LENGTH_MILLIMETERS,
    PRESSURE_HPA,
    SPEED_METERS_PER_SECOND,
    STATE_UNAVAILABLE,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .config_flow import get_value
from .const import (
    ATTR_API_CONDITION,
    ATTR_API_FEELS_LIKE_TEMPERATURE,
    ATTR_API_HUMIDITY,
    ATTR_API_IMAGE,
    ATTR_API_ORIGINAL_CONDITION,
    ATTR_API_PRESSURE,
    ATTR_API_TEMP_WATER,
    ATTR_API_TEMPERATURE,
    ATTR_API_WIND_BEARING,
    ATTR_API_WIND_GUST,
    ATTR_API_WIND_SPEED,
    ATTR_API_YA_CONDITION,
    ATTRIBUTION,
    CONF_IMAGE_SOURCE,
    DOMAIN,
    ENTRY_NAME,
    UPDATER,
    get_image,
)
from .updater import WeatherUpdater

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up weather "Yandex.Weather" weather entry."""
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    name = domain_data[ENTRY_NAME]
    updater = domain_data[UPDATER]

    async_add_entities([YandexWeather(name, config_entry, updater, hass)], False)


class YandexWeather(WeatherEntity, CoordinatorEntity, RestoreEntity):
    """Yandex.Weather entry."""

    _attr_attribution = ATTRIBUTION
    _attr_native_wind_speed_unit = SPEED_METERS_PER_SECOND
    _attr_native_pressure_unit = PRESSURE_HPA
    _attr_native_temperature_unit = TEMP_CELSIUS
    _attr_native_precipitation_unit = LENGTH_MILLIMETERS
    coordinator: WeatherUpdater

    def __init__(
        self,
        name,
        config_entry: ConfigEntry,
        updater: WeatherUpdater,
        hass: HomeAssistant,
    ):
        """Initialize entry."""
        WeatherEntity.__init__(self)
        CoordinatorEntity.__init__(self, coordinator=updater)
        RestoreEntity.__init__(self)

        self.hass = hass
        self._attr_name = name
        self._attr_unique_id = config_entry.unique_id
        self._attr_device_info = self.coordinator.device_info
        self._image_source = get_value(config_entry, CONF_IMAGE_SOURCE, "Yandex")

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await RestoreEntity.async_added_to_hass(self)
        await CoordinatorEntity.async_added_to_hass(self)

        state = await self.async_get_last_state()
        if not state:
            _LOGGER.debug("Have no state for restore!")
            await self.coordinator.async_config_entry_first_refresh()
            return

        if state.state == STATE_UNAVAILABLE:
            self._attr_available = False
            await self.coordinator.async_config_entry_first_refresh()
        else:
            _LOGGER.debug(f"state for restore: {state}")
            self._attr_available = True
            self._attr_condition = state.state
            for (attribute, converter) in [
                ("temperature", UNIT_CONVERSIONS[ATTR_WEATHER_TEMPERATURE_UNIT]),
                ("pressure", UNIT_CONVERSIONS[ATTR_WEATHER_PRESSURE_UNIT]),
                ("wind_speed", UNIT_CONVERSIONS[ATTR_WEATHER_WIND_SPEED_UNIT]),
            ]:
                setattr(
                    self,
                    f"_attr_native_{attribute}",
                    converter(
                        state.attributes.get(attribute),
                        state.attributes.get(
                            f"_{attribute}_unit",
                            getattr(self, f"_attr_native_{attribute}_unit"),
                        ),
                        getattr(self, f"_attr_native_{attribute}_unit"),
                    ),
                )

            self._attr_humidity = state.attributes.get("humidity")
            self._attr_wind_bearing = state.attributes.get("wind_bearing")
            self._attr_entity_picture = state.attributes.get("entity_picture")
            self._attr_forecast = state.attributes.get(ATTR_FORECAST)
            for f in self._attr_forecast:
                for (attribute, converter) in [
                    ("temperature", UNIT_CONVERSIONS[ATTR_WEATHER_TEMPERATURE_UNIT]),
                    ("pressure", UNIT_CONVERSIONS[ATTR_WEATHER_PRESSURE_UNIT]),
                    ("wind_speed", UNIT_CONVERSIONS[ATTR_WEATHER_WIND_SPEED_UNIT]),
                    (
                        "precipitation",
                        UNIT_CONVERSIONS[ATTR_WEATHER_PRECIPITATION_UNIT],
                    ),
                ]:
                    f[attribute] = converter(
                        f.get(attribute),
                        getattr(
                            self,
                            f"_{attribute}_unit",
                            getattr(self, f"_attr_native_{attribute}_unit"),
                        ),
                        getattr(self, f"_attr_native_{attribute}_unit"),
                    )
            self._attr_extra_state_attributes = {}
            for attribute in [
                "feels_like",
                "wind_gust",
                "yandex_condition",
                "temp_water",
            ]:
                value = state.attributes.get(attribute)
                if value is not None:
                    self._attr_extra_state_attributes[attribute] = value

            # last_updated is last call of self.async_write_ha_state(), not a real last update
            since_last_update = datetime.now(timezone.utc) - state.last_updated.replace(
                tzinfo=timezone.utc
            )
            _LOGGER.debug(
                f"Time since last update: {since_last_update} ({state.last_updated}), "
                f"update interval is {self.coordinator.update_interval}"
            )
            if since_last_update > self.coordinator.update_interval:
                await self.coordinator.async_config_entry_first_refresh()
            else:
                self.coordinator.schedule_refresh(
                    offset=self.coordinator.update_interval - since_last_update
                )
        self.async_write_ha_state()

    def _handle_coordinator_update(self) -> None:
        self._attr_available = True
        self._attr_condition = self.coordinator.data.get(ATTR_API_CONDITION)
        self._attr_entity_picture = get_image(
            image_source=self._image_source,
            condition=self.coordinator.data.get(ATTR_API_ORIGINAL_CONDITION),
            is_day=self.coordinator.data.get("daytime") == "d",
            image=self.coordinator.data.get(ATTR_API_IMAGE),
        )
        self._attr_forecast = self.coordinator.data.get(ATTR_FORECAST)
        self._attr_humidity = self.coordinator.data.get(ATTR_API_HUMIDITY)
        self._attr_native_pressure = self.coordinator.data.get(ATTR_API_PRESSURE)
        self._attr_native_temperature = self.coordinator.data.get(ATTR_API_TEMPERATURE)
        self._attr_native_wind_speed = self.coordinator.data.get(ATTR_API_WIND_SPEED)
        self._attr_wind_bearing = self.coordinator.data.get(ATTR_API_WIND_BEARING)
        self._attr_extra_state_attributes = {
            "feels_like": self.coordinator.data.get(ATTR_API_FEELS_LIKE_TEMPERATURE),
            "wind_gust": self.coordinator.data.get(ATTR_API_WIND_GUST),
            "yandex_condition": self.coordinator.data.get(ATTR_API_YA_CONDITION),
        }
        try:
            self._attr_extra_state_attributes["temp_water"] = self.coordinator.data.get(
                ATTR_API_TEMP_WATER
            )
        except KeyError:
            self.coordinator.logger.debug("data have no temp_water. Skipping.")

        self.async_write_ha_state()
