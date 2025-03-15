"""General constants."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.weather import ATTR_CONDITION_CLEAR_NIGHT, ATTR_CONDITION_CLOUDY, \
    ATTR_CONDITION_EXCEPTIONAL, ATTR_CONDITION_HAIL, ATTR_CONDITION_LIGHTNING, ATTR_CONDITION_LIGHTNING_RAINY, \
    ATTR_CONDITION_PARTLYCLOUDY, ATTR_CONDITION_POURING, ATTR_CONDITION_RAINY, ATTR_CONDITION_SNOWY, \
    ATTR_CONDITION_SUNNY
from homeassistant.const import Platform

DOMAIN = "yandex_weather"
DEFAULT_NAME = "Yandex Weather"
DEFAULT_UPDATES_PER_DAY = 24
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

CONF_UPDATES_PER_DAY = "updates_per_day"
CONF_IMAGE_SOURCE = "image_source"
CONF_LANGUAGE_KEY = "language"
UPDATE_LISTENER = "update_listener"
PLATFORMS = [Platform.SENSOR, Platform.WEATHER]


WEATHER_STATES_CONVERSION = {
    "CLEAR": {
        "day": ATTR_CONDITION_SUNNY,
        "night": ATTR_CONDITION_CLEAR_NIGHT,
    },
    "PARTLY_CLOUDY": ATTR_CONDITION_PARTLYCLOUDY,
    "CLOUDY": ATTR_CONDITION_CLOUDY,
    "OVERCAST": ATTR_CONDITION_CLOUDY,
    "LIGHT_RAIN": ATTR_CONDITION_RAINY,
    "RAIN": ATTR_CONDITION_RAINY,
    "HEAVY_RAIN": ATTR_CONDITION_POURING,
    "SHOWERS": ATTR_CONDITION_POURING,
    "SLEET": ATTR_CONDITION_SNOWY,
    "LIGHT_SNOW": ATTR_CONDITION_SNOWY,
    "SNOW": ATTR_CONDITION_SNOWY,
    "SNOWFALL": ATTR_CONDITION_SNOWY,
    "HAIL": ATTR_CONDITION_HAIL,
    "THUNDERSTORM": ATTR_CONDITION_LIGHTNING,
    "THUNDERSTORM_WITH_RAIN": ATTR_CONDITION_LIGHTNING_RAINY,
    "THUNDERSTORM_WITH_HAIL": ATTR_CONDITION_EXCEPTIONAL,
}
"""Map Yandex weather condition https://yandex.ru/dev/weather/doc/ru/concepts/spectaql#definition-Condition 
to HA"""

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

    link: str
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