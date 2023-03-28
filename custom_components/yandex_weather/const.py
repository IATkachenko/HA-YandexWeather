"""General constants."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.backports.enum import StrEnum
from homeassistant.const import Platform

DOMAIN = "yandex_weather"
DEFAULT_NAME = "Yandex Weather"
DEFAULT_UPDATES_PER_DAY = 48
ATTRIBUTION = "Data provided by Yandex Weather"
MANUFACTURER = "Yandex"
ENTRY_NAME = "name"
UPDATER = "updater"
UPDATES_PER_DAY = "updates_per_day"

ATTR_API_TEMPERATURE = "temp"
ATTR_API_FEELS_LIKE_TEMPERATURE = "feels_like"
ATTR_API_WIND_SPEED = "wind_speed"
ATTR_API_WIND_BEARING = "wind_dir"
ATTR_API_HUMIDITY = "humidity"
ATTR_API_PRESSURE = "pressure_pa"
ATTR_API_CONDITION = "condition"
ATTR_API_IMAGE = "icon"
ATTR_API_WEATHER_TIME = "obs_time"
ATTR_API_YA_CONDITION = "yandex_condition"
ATTR_API_PRESSURE_MMHG = "pressure_mm"
ATTR_API_TEMP_WATER = "temp_water"
ATTR_API_WIND_GUST = "wind_gust"
ATTR_API_ORIGINAL_CONDITION = "original_condition"
ATTR_MIN_FORECAST_TEMPERATURE = "min_forecast_temperature"

CONF_UPDATES_PER_DAY = "updates_per_day"
CONF_IMAGE_SOURCE = "image_source"
CONF_LANGUAGE_KEY = "language"
UPDATE_LISTENER = "update_listener"
PLATFORMS = [Platform.SENSOR, Platform.WEATHER]


WEATHER_STATES_CONVERSION = {
    "clear": {
        "day": "sunny",
        "night": "clear-night",
    },
    "partly-cloudy": "partlycloudy",
    "cloudy": "cloudy",
    "overcast": "cloudy",
    "drizzle": "fog",
    "light-rain": "rainy",
    "rain": "rainy",
    "moderate-rain": "rainy",
    "heavy-rain": "pouring",
    "continuous-heavy-rain": "pouring",
    "showers": "pouring",
    "wet-snow": "snowy-rainy",
    "light-snow": "snowy",
    "snow": "snowy",
    "snow-showers": "snowy",
    "hail": "hail",
    "thunderstorm": "lightning",
    "thunderstorm-with-rain": "lightning-rainy",
    "thunderstorm-with-hail": "lightning-rainy",
}
"""Map rich Yandex weather condition to ordinary HA"""

CONDITION_ICONS = {
    "clear": {
        "day": "mdi:weather-sunny",
        "night": "mdi:weather-night",
    },
    "partly-cloudy": {
        "day": "mdi:weather-partly-cloudy",
        "night": "mdi:weather-night-partly-cloudy",
    },
    "cloudy": "mdi:weather-cloudy",
    "overcast": "mdi:weather-cloudy",
    "drizzle": "mdi:weather-fog",
    "light-rain": "mdi:weather-rainy",
    "rain": "mdi:weather-rainy",
    "moderate-rain": "mdi:weather-rainy",
    "heavy-rain": "mdi:weather-pouring",
    "continuous-heavy-rain": "mdi:weather-pouring",
    "showers": "mdi:weather-pouring",
    "wet-snow": "mdi:weather-snowy-rainy",
    "light-snow": "mdi:weather-snowy",
    "snow": "mdi:weather-snowy",
    "snow-showers": "mdi:weather-snowy-heavy",
    "hail": "mdi:weather-hail",
    "thunderstorm": "mdi:weather-lightning",
    "thunderstorm-with-rain": "mdi:weather-lightning-rainy",
    "thunderstorm-with-hail": "mdi:weather-lightning-rainy",
}
"""Mapping for state icon"""

CUSTOM_WEATHER_CARD_MAPPING = {
    "clear": {
        "day": "day",
        "night": "night",
    },
    "partly-cloudy": {
        "day": "cloudy-day-1",
        "night": "cloudy-night-1",
    },
    "cloudy": {
        "day": "cloudy-day-2",
        "night": "cloudy-night-2",
    },
    "overcast": {"day": "cloudy-day-3", "night": "cloudy-night-3"},
    "drizzle": "rainy-1",
    "light-rain": "rainy-2",
    "rain": "rainy-3",
    "moderate-rain": "rainy-4",
    "heavy-rain": "rainy-5",
    "continuous-heavy-rain": "rainy-6",
    "showers": "rainy-7",
    "wet-snow": "snowy-2",
    "light-snow": "snowy-1",
    "snow": "snowy-4",
    "snow-showers": "snowy-5",
    "hail": "snowy-6",
    "thunderstorm": "thunder",
    "thunderstorm-with-rain": "thunder",
    "thunderstorm-with-hail": "thunder",
}
"""Condition mapping for images from https://github.com/bramkragten/weather-card"""


@dataclass
class ConditionImage:
    """Way to get image for weather condition."""

    link: str | None = None
    mapping: dict | None = None


CONDITION_IMAGE: dict[str, ConditionImage] = {
    "HomeAssistant": None,
    "Yandex": ConditionImage(
        link="https://yastatic.net/weather/i/icons/funky/dark/{}.svg",
        mapping=None,
    ),
    "Custom weather card animated": ConditionImage(
        link="https://cdn.jsdelivr.net/gh/bramkragten/weather-card/dist/icons/{}.svg",
        mapping=CUSTOM_WEATHER_CARD_MAPPING,
    ),
    "Custom weather card static": ConditionImage(
        link="https://cdn.jsdelivr.net/gh/bramkragten/weather-card/icons/static/{}.svg",
        mapping=CUSTOM_WEATHER_CARD_MAPPING,
    ),
}


def map_state(src: str, is_day: bool = True, mapping: dict | None = None) -> str:
    """
    Map weather condition based on WEATHER_STATES_CONVERSION.

    :param src: str: Yandex weather state
    :param is_day: bool: Is it day? Used for 'clear' state
    :param mapping: use this dict for mapping
    :return: str: Home Assistant weather state
    """
    if mapping is None:
        mapping = {}
    try:
        result: str | dict[str, str] = mapping[src]
    except KeyError:
        result = src

    if type(result) == dict:
        t = "day" if is_day else "night"
        result = result[t]

    return result


def get_image(
    image_source: str, condition: str, image: str, is_day: bool = True
) -> str | None:
    """Get image for current condition.

    :param image_source: str: What kind of image is used
    :param condition: str: get image for this condition
    :param image: str: backup image that will be used if we have no mapping
    :param is_day: bool: is it day condition or not
    :return: str|None: url for current condition image
    """

    if image_source not in CONDITION_IMAGE.keys():
        return None
    if CONDITION_IMAGE[image_source] is None:
        return None
    if (link := CONDITION_IMAGE[image_source].link) is None:
        return None

    if (mapping := CONDITION_IMAGE[image_source].mapping) is not None:
        # map condition to image_source-friendly
        condition = map_state(
            src=condition,
            is_day=is_day,
            mapping=mapping,
        )
    else:
        condition = image

    return link.format(condition)


class YandexWeatherDeviceClass(StrEnum):
    """State class for weather sensors."""

    WIND_BEARING = f"{DOMAIN}__wind_bearing"
    CONDITION_YA = f"{DOMAIN}__condition_ya"
    CONDITION_HA = f"{DOMAIN}__condition_ha"
