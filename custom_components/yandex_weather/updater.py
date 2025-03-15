"""Weather data updater."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
import math
import os

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from homeassistant.components.weather import (
    ATTR_FORECAST_CLOUD_COVERAGE,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_HUMIDITY,
    ATTR_FORECAST_NATIVE_APPARENT_TEMP,
    ATTR_FORECAST_NATIVE_DEW_POINT,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_PRESSURE,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_WIND_GUST_SPEED,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_UV_INDEX,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    ATTR_API_CONDITION,
    ATTR_API_FEELS_LIKE_TEMPERATURE,
    ATTR_API_FORECAST_ICONS,
    ATTR_API_HUMIDITY,
    ATTR_API_IMAGE,
    ATTR_API_ORIGINAL_CONDITION,
    ATTR_API_PRESSURE,
    ATTR_API_TEMPERATURE,
    ATTR_API_WEATHER_TIME,
    ATTR_API_WIND_BEARING,
    ATTR_API_WIND_SPEED,
    ATTR_API_YA_CONDITION,
    ATTR_FORECAST_DATA,
    ATTR_MIN_FORECAST_TEMPERATURE,
    CONDITION_ICONS,
    DOMAIN,
    MANUFACTURER,
    QUERY,
    WEATHER_STATES_CONVERSION,
    map_state,
)

API_URL = "https://api.weather.yandex.ru/graphql/query"
API_VERSION = "3"
_LOGGER = logging.getLogger(__name__)


WIND_DIRECTION_MAPPING: dict[str, int | None] = {
    "NORTH": 0,
    "NORTH_EAST": 45,
    "EAST": 90,
    "SOUTH_EAST": 135,
    "SOUTH": 180,
    "SOUTH_WEST": 225,
    "WEST": 270,
    "NORTH_WEST": 315,
}
"""Wind directions mapping."""

CLOUDINESS_MAPPING: dict[str, int] = {
    "CLEAR": 0,
    "PARTLY": int(1.5 / 8 * 100),
    "SIGNIFICANT": int(3.5 / 8 * 100),
    "CLOUDY": int(6 / 8 * 100),
    "OVERCAST": 100,
}
"""https://yandex.ru/dev/weather/doc/ru/concepts/spectaql#definition-Cloudiness"""


@dataclass
class AttributeMapper:
    """Attribute mapper."""

    src: str
    _dst: str | None = None
    mapping: dict | None = None
    default: str | float | None = None
    should_translate: bool = False

    @property
    def dst(self) -> str:
        """Destination for mapping."""
        return self.src if self._dst is None else self._dst


FORECAST_DATA_ATTRIBUTE_TRANSLATION: list[AttributeMapper] = [
    AttributeMapper(
        src="condition", _dst=ATTR_FORECAST_CONDITION, mapping=WEATHER_STATES_CONVERSION
    ),
    AttributeMapper(src="time", _dst="datetime"),
    AttributeMapper(src="humidity", _dst=ATTR_FORECAST_HUMIDITY),
    AttributeMapper(
        src="precProbability", _dst=ATTR_FORECAST_PRECIPITATION_PROBABILITY
    ),
    AttributeMapper(
        src="cloudiness",
        _dst=ATTR_FORECAST_CLOUD_COVERAGE,
        mapping=CLOUDINESS_MAPPING,
        default=0,
    ),
    AttributeMapper(src="prec", _dst=ATTR_FORECAST_NATIVE_PRECIPITATION),
    AttributeMapper(src="pressure", _dst=ATTR_FORECAST_NATIVE_PRESSURE),
    AttributeMapper(src="temperature", _dst=ATTR_FORECAST_NATIVE_TEMP),
    AttributeMapper(src="feelsLike", _dst=ATTR_FORECAST_NATIVE_APPARENT_TEMP),
    AttributeMapper(src="windAngle", _dst=ATTR_FORECAST_WIND_BEARING),
    AttributeMapper(src="windGust", _dst=ATTR_FORECAST_NATIVE_WIND_GUST_SPEED),
    AttributeMapper(src="windSpeed", _dst=ATTR_FORECAST_NATIVE_WIND_SPEED),
    AttributeMapper(src="dewPoint", _dst=ATTR_FORECAST_NATIVE_DEW_POINT),
    AttributeMapper(src="uvIndex", _dst=ATTR_FORECAST_UV_INDEX),
]
CURRENT_WEATHER_ATTRIBUTE_TRANSLATION: list[AttributeMapper] = [
    AttributeMapper(ATTR_API_WIND_BEARING, mapping=WIND_DIRECTION_MAPPING),
    AttributeMapper(ATTR_API_CONDITION, ATTR_API_ORIGINAL_CONDITION),
    AttributeMapper(
        ATTR_API_CONDITION, f"{ATTR_API_YA_CONDITION}_icon", CONDITION_ICONS
    ),
    AttributeMapper(ATTR_API_CONDITION, ATTR_API_YA_CONDITION, should_translate=True),
    AttributeMapper(ATTR_API_CONDITION, mapping=WEATHER_STATES_CONVERSION),
    AttributeMapper(ATTR_API_FEELS_LIKE_TEMPERATURE),
    AttributeMapper(ATTR_API_HUMIDITY),
    AttributeMapper(ATTR_API_IMAGE),
    AttributeMapper(ATTR_API_PRESSURE),
    # AttributeMapper(ATTR_API_PRESSURE_MMHG),
    # AttributeMapper(ATTR_API_TEMP_WATER),
    AttributeMapper(ATTR_API_TEMPERATURE),
    # AttributeMapper(ATTR_API_WIND_GUST),
    AttributeMapper(ATTR_API_WIND_SPEED, default=0),
    AttributeMapper("daytime"),
    AttributeMapper(
        "cloudiness", _dst="cloud_coverage", mapping=CLOUDINESS_MAPPING, default=0
    ),
]


def translate_condition(value: str, _language: str) -> str:
    """Translate Yandex condition."""
    _my_location = os.path.dirname(os.path.realpath(__file__))
    _translation_location = f"{_my_location}/translations/{_language.lower()}.json"
    try:
        with open(_translation_location) as f:
            value = json.loads(f.read())["entity"]["sensor"][ATTR_API_YA_CONDITION][
                "state"
            ][value]
    except FileNotFoundError:
        _LOGGER.debug(f"We have no translation for {_language=} in {_my_location}")
    except KeyError:
        _LOGGER.debug(f"Have no translation for {value} in {_translation_location}")
    return value


class WeatherUpdater(DataUpdateCoordinator):
    """Weather data updater for interaction with Yandex.Weather API."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        api_key: str,
        hass: HomeAssistant,
        device_id: str,
        language: str = "EN",
        updates_per_day: int = 50,
        name="Yandex Weather",
    ):
        """Initialize updater.

        :param latitude: latitude of location for weather data
        :param longitude: longitude of location for weather data
        :param api_key: Yandex weather API. MUST be weather for site tariff plan
        :param hass: Home Assistant object
        :param language: Language for yandex_condition
        :param updates_per_day: int: how many updates per day we should do?
        :param device_id: ID of integration Device in Home Assistant
        """

        self.__api_key = api_key
        self._lat = latitude
        self._lon = longitude
        self._device_id = device_id
        self._name = name
        self._language = language
        # Site tariff have 50 free requests per day, but it may be changed
        self.update_interval = timedelta(
            seconds=math.ceil((24 * 60 * 60) / updates_per_day)
        )

        if hass is not None:
            super().__init__(
                hass,
                _LOGGER,
                name=f"{self._name} updater",
                update_interval=self.update_interval,
                update_method=self.update,
            )
        self.data = {}

    @staticmethod
    async def process_data(dst: dict, src: dict, attributes: list[AttributeMapper]):
        """Convert Yandex API weather state to HA friendly.

        :param dst: weather data for HomeAssistant
        :param src: weather data form Yandex
        :param attributes: how to translate src to dst
        """

        for attribute in attributes:
            value = src.get(attribute.src, attribute.default)
            if attribute.mapping is not None and value is not None:
                value = map_state(
                    src=value,
                    mapping=attribute.mapping,
                    is_day=(src.get("daytime", "DAY") == "DAY"),
                )
            # if attribute.should_translate and value is not None:
            #     value = await translate_condition(
            #         value=value,
            #         _language=self._language,
            #     )

            dst[attribute.dst] = value

    @staticmethod
    async def get_min_forecast_temperature(forecasts: list[dict]) -> float | None:
        """Get minimum temperature from forecast data."""
        low_fc_temperatures: list[float] = []

        for f in forecasts:
            f_low_temperature: float = f.get(ATTR_FORECAST_NATIVE_TEMP, None)
            if f_low_temperature is not None:
                low_fc_temperatures.append(f_low_temperature)

        return min(low_fc_temperatures) if len(low_fc_temperatures) > 0 else None

    @property
    def geo(self) -> dict[str, float]:
        return {"lat": self._lat, "lon": self._lon}

    async def update(self):
        """Update weather information.

        :returns: dict with weather data.
        """

        transport = AIOHTTPTransport(
            url=API_URL, headers={"X-Yandex-Weather-Key": self.__api_key}, timeout=20
        )
        async with Client(
            transport=transport, fetch_schema_from_transport=False
        ) as client:
            r = await client.execute(gql(QUERY), variable_values=self.geo)
            _LOGGER.debug(f"Raw data is {r=}")
            now = datetime.now().astimezone()
            weather = r.get("weatherByPoint", {})
            result = {
                ATTR_API_WEATHER_TIME: now,
                ATTR_API_FORECAST_ICONS: [],
                ATTR_FORECAST_DATA: [],
            }
            await self.process_data(
                result, weather.get("now", {}), CURRENT_WEATHER_ATTRIBUTE_TRANSLATION
            )

            await self.fill_forecast(now, result, weather["forecast"]["days"])

            result[ATTR_MIN_FORECAST_TEMPERATURE] = await self.get_min_forecast_temperature(
                result[ATTR_FORECAST_DATA]
            )

            return result

    async def fill_forecast(
        self, now: datetime, weather_data, forecast_data: list[dict]
    ):
        """
        Fill weather_data ATTR_FORECAST_DATA and ATTR_API_FORECAST_ICONS fields

        :param now: current datetime
        :param weather_data: this integration weather result
        :param forecast_data: Yandex forecast days data
        """
        for d in forecast_data:
            for f in d["hours"]:
                if len(weather_data[ATTR_FORECAST_DATA]) > 24:
                    return

                f_time = datetime.fromisoformat(f["time"])
                if f_time > now:
                    forecast = Forecast(datetime=datetime.isoformat(f_time))
                    await self.process_data(
                        forecast, f, FORECAST_DATA_ATTRIBUTE_TRANSLATION
                    )
                    weather_data[ATTR_FORECAST_DATA].append(forecast)
                    weather_data[ATTR_API_FORECAST_ICONS].append(
                        f.get("icon", "no_image")
                    )

    def __str__(self):
        """Show as pretty look data json."""
        _d = dict(self.data)
        _d[ATTR_API_WEATHER_TIME] = str(_d[ATTR_API_WEATHER_TIME])
        return json.dumps(_d, indent=4, sort_keys=True)

    @property
    def url(self) -> str:
        """Weather URL."""
        return f"https://yandex.com/weather/?lat={self._lat}&lon={self._lon}"

    @property
    def device_info(self):
        """Device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self.device_id)},
            manufacturer=MANUFACTURER,
            name=self._name,
            configuration_url=self.url,
        )

    def schedule_refresh(self, offset: timedelta):
        """Schedule refresh."""
        if self._unsub_refresh:
            self._unsub_refresh()
            self._unsub_refresh = None

        _LOGGER.debug(f"scheduling next refresh after {offset=}")
        next_refresh = (
            int(self.hass.loop.time()) + self._microsecond + offset.total_seconds()
        )
        self._unsub_refresh = self.hass.loop.call_at(
            next_refresh, self.__wrap_handle_refresh_interval
        ).cancel

    @callback
    def __wrap_handle_refresh_interval(self) -> None:
        """Handle a refresh interval occurrence."""
        # We need this private callback from parent class
        if self.config_entry:
            self.config_entry.async_create_background_task(
                self.hass,
                self._handle_refresh_interval(),
                name=f"{self.name} - {self.config_entry.title} - refresh",
                eager_start=True,
            )
        else:
            self.hass.async_create_background_task(
                self._handle_refresh_interval(),
                name=f"{self.name} - refresh",
                eager_start=True,
            )

    @property
    def device_id(self) -> str:
        """Device ID."""
        return self._device_id
