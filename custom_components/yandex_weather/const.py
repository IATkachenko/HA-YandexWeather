"""General constants."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import floor

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_EXCEPTIONAL,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SUNNY,
)
from homeassistant.const import Platform

DOMAIN = "yandex_weather"
DEFAULT_NAME = "Yandex Weather"
API_LIMIT_PER_DAY = 30
API_LIMIT_PER_MONTH = 380  # 2.7 https://yandex.ru/legal/apib2c_weather_agreement/ru/
DEFAULT_UPDATES_PER_DAY = min(24, API_LIMIT_PER_DAY, floor(API_LIMIT_PER_MONTH / 31))
ATTRIBUTION = "Data provided by Yandex Weather"
MANUFACTURER = "Yandex"
ENTRY_NAME = "name"
UPDATER = "updater"
UPDATES_PER_DAY = "updates_per_day"


ATTR_API_TEMPERATURE = "temperature"
"""Temperature"""
ATTR_API_FEELS_LIKE_TEMPERATURE = "feelsLike"
ATTR_API_WIND_SPEED = "windSpeed"
ATTR_API_WIND_BEARING = "windDirection"
"""Wind direction"""
ATTR_API_HUMIDITY = "humidity"
ATTR_API_PRESSURE = "pressure"
ATTR_API_CONDITION = "condition"
ATTR_API_IMAGE = "icon"
ATTR_API_WEATHER_TIME = "obs_time"
ATTR_API_YA_CONDITION = "yandex_condition"

# ATTR_API_TEMP_WATER = "temp_water"
# ATTR_API_WIND_GUST = "windGust"
ATTR_API_ORIGINAL_CONDITION = "original_condition"
ATTR_MIN_FORECAST_TEMPERATURE = "min_forecast_temperature"
ATTR_API_FORECAST_ICONS = "forecast_icons"

ATTR_FORECAST_DATA = "forecast"  # just to be able to load saved forecast after restart
ATTR_FORECAST_HOURLY = "forecastHourly"
ATTR_FORECAST_DAILY = "forecastDaily"

CONF_UPDATES_PER_DAY = "updates_per_day"
CONF_IMAGE_SOURCE = "image_source"
CONF_LANGUAGE_KEY = "language"
UPDATE_LISTENER = "update_listener"
PLATFORMS = [Platform.SENSOR, Platform.WEATHER]


@dataclass
class ConditionMapper:
    HA: dict | str
    icons: dict | str
    custom_weather_card: dict | str


class Conditions(Enum):
    """
    Yandex weather conditions

    https://yandex.ru/dev/weather/doc/ru/concepts/spectaql#definition-Condition
    """

    CLEAR = ConditionMapper(
        HA={"day": ATTR_CONDITION_SUNNY, "night": ATTR_CONDITION_CLEAR_NIGHT},
        icons={"day": "mdi:weather-sunny", "night": "mdi:weather-night"},
        custom_weather_card={"day": "day", "night": "night"},
    )
    PARTLY_CLOUDY = ConditionMapper(
        HA=ATTR_CONDITION_PARTLYCLOUDY,
        icons={
            "day": "mdi:weather-partly-cloudy",
            "night": "mdi:weather-night-partly-cloudy",
        },
        custom_weather_card={
            "day": "cloudy-day-1",
            "night": "cloudy-night-1",
        },
    )
    CLOUDY = ConditionMapper(
        HA=ATTR_CONDITION_CLOUDY,
        icons="mdi:weather-cloudy",
        custom_weather_card={"day": "cloudy-day-2", "night": "cloudy-night-2"},
    )
    OVERCAST = ConditionMapper(
        HA=ATTR_CONDITION_CLOUDY,
        icons="mdi:weather-cloudy",
        custom_weather_card={"day": "cloudy-day-3", "night": "cloudy-night-3"},
    )
    LIGHT_RAIN = ConditionMapper(
        HA=ATTR_CONDITION_RAINY,
        icons="mdi:weather-rainy",
        custom_weather_card="rainy-2",
    )
    RAIN = ConditionMapper(
        HA=ATTR_CONDITION_RAINY,
        icons="mdi:weather-rainy",
        custom_weather_card="rainy-3",
    )
    HEAVY_RAIN = ConditionMapper(
        HA=ATTR_CONDITION_POURING,
        icons="mdi:weather-pouring",
        custom_weather_card="rainy-5",
    )
    SHOWERS = ConditionMapper(
        HA=ATTR_CONDITION_POURING,
        icons="mdi:weather-pouring",
        custom_weather_card="rainy-7",
    )
    SLEET = ConditionMapper(
        HA=ATTR_CONDITION_SNOWY,
        icons="mdi:weather-snowy",
        custom_weather_card="snowy-1",
    )
    LIGHT_SNOW = ConditionMapper(
        HA=ATTR_CONDITION_SNOWY,
        icons="mdi:weather-snowy",
        custom_weather_card="snowy-2",
    )
    SNOW = ConditionMapper(
        HA=ATTR_CONDITION_SNOWY,
        icons="mdi:weather-snowy",
        custom_weather_card="snowy-4",
    )
    SNOWFALL = ConditionMapper(
        HA=ATTR_CONDITION_SNOWY,
        icons="mdi:weather-snowy-heavy",
        custom_weather_card="snowy-5",
    )
    HAIL = ConditionMapper(
        HA=ATTR_CONDITION_HAIL,
        icons="mdi:weather-hail",
        custom_weather_card="snowy-6",
    )
    THUNDERSTORM = ConditionMapper(
        HA=ATTR_CONDITION_LIGHTNING,
        icons="mdi:weather-lightning",
        custom_weather_card="thunder",
    )
    THUNDERSTORM_WITH_RAIN = ConditionMapper(
        HA=ATTR_CONDITION_LIGHTNING_RAINY,
        icons="mdi:weather-lightning-rainy",
        custom_weather_card="thunder",
    )
    THUNDERSTORM_WITH_HAIL = ConditionMapper(
        HA=ATTR_CONDITION_EXCEPTIONAL,
        icons="mdi:weather-lightning-rainy",
        custom_weather_card="thunder",
    )


WEATHER_STATES_CONVERSION: dict[str, dict[str, str] | str] = {}
"""
Map Yandex weather condition to HA
"""
for _condition in Conditions:
    WEATHER_STATES_CONVERSION[_condition.name] = _condition.value.HA

CONDITION_ICONS: dict[Conditions.value, dict[str, str] | str] = {}
"""Mapping for state icon"""
for _condition in Conditions:
    CONDITION_ICONS[_condition.name] = _condition.value.icons

CUSTOM_WEATHER_CARD_MAPPING: dict[Conditions.value, dict[str, str] | str] = {}
"""Condition mapping for images from https://github.com/bramkragten/weather-card"""
for _condition in Conditions:
    CUSTOM_WEATHER_CARD_MAPPING[_condition.name] = _condition.value.custom_weather_card


@dataclass
class ConditionImage:
    """Way to get image for weather condition."""

    link: str
    mapping: dict | None = None


CONDITION_IMAGE: dict[str, ConditionImage] = {
    "HomeAssistant": None,
    "Yandex": ConditionImage(
        link="{}",  # Now Yandex send full image URL
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

    if type(result) is dict:
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
    if (ci := CONDITION_IMAGE[image_source]) is None:
        return None

    if (mapping := ci.mapping) is not None:
        # map condition to image_source-friendly
        condition = map_state(
            src=condition,
            is_day=is_day,
            mapping=mapping,
        )
    else:
        condition = image

    return ci.link.format(condition)


# https://yandex.ru/dev/weather/doc/ru/concepts/parameters#pressure
# access denied for free role: pressure, humidity, cloudiness, precStrength, precProbability, uvIndex
QUERY = """
    query($lat: Float!, $lon: Float!) {
        weatherByPoint(request: { lat: $lat, lon: $lon }, language: EN) {
            now {
              temperature
              feelsLike
              windSpeed
              windDirection
              condition
              icon(format: SVG)
              daytime
            }
            forecast {
                days(limit: 2) {
                    hours {
                        condition
                        time
                        temperature
                        feelsLike
                        windSpeed
                        windAngle
                        windGust
                        icon(format: SVG)
                    }
                }
            }
        }
    }
"""
