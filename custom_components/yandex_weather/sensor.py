from __future__ import annotations
import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    ATTRIBUTION,
    DEFAULT_NAME,
    DOMAIN,
    ENTRY_NAME,
    UPDATER,
    MANUFACTURER,
    WEATHER_SENSOR_TYPES,
)
from .updater import WeatherUpdater

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    name = domain_data[ENTRY_NAME]
    updater = domain_data[UPDATER]

    entities: list[YandexWeatherSensor] = [
        YandexWeatherSensor(
            name,
            f"{config_entry.unique_id}-{description.key}",
            description,
            updater,
        )
        for description in WEATHER_SENSOR_TYPES
    ]
    async_add_entities(entities)


class YandexWeatherSensor(SensorEntity):
    _attr_should_poll = False
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        name: str,
        unique_id: str,
        description: SensorEntityDescription,
        updater: WeatherUpdater,
    ) -> None:
        self.entity_description = description
        self._updater = updater

        self._attr_name = f"{name} {description.name}"
        self._attr_unique_id = unique_id
        split_unique_id = unique_id.split("-")
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{split_unique_id[0]}-{split_unique_id[1]}")},
            manufacturer=MANUFACTURER,
            name=DEFAULT_NAME,
        )

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
        await self._updater.async_request_refresh()

    @property
    def native_value(self) -> StateType:
        """:returns: the state of the device."""

        return self._updater.weather_data['fact'].get(self.entity_description.key, None)
