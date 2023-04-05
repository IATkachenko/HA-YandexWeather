"""Weather data updater."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import cached_property
import json
import logging
import math
import os

import aiohttp
from homeassistant.components.weather import (
    ATTR_FORECAST,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_PRESSURE,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import event
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import utcnow

from .const import (
    ATTR_API_CONDITION,
    ATTR_API_FEELS_LIKE_TEMPERATURE,
    ATTR_API_HUMIDITY,
    ATTR_API_IMAGE,
    ATTR_API_ORIGINAL_CONDITION,
    ATTR_API_PRESSURE,
    ATTR_API_PRESSURE_MMHG,
    ATTR_API_TEMP_WATER,
    ATTR_API_TEMPERATURE,
    ATTR_API_WEATHER_TIME,
    ATTR_API_WIND_BEARING,
    ATTR_API_WIND_GUST,
    ATTR_API_WIND_SPEED,
    ATTR_API_YA_CONDITION,
    ATTR_MIN_FORECAST_TEMPERATURE,
    CONDITION_ICONS,
    DOMAIN,
    MANUFACTURER,
    WEATHER_STATES_CONVERSION,
    map_state,
)

API_URL = "https://api.weather.yandex.ru"
API_VERSION = "2"
_LOGGER = logging.getLogger(__name__)


WIND_DIRECTION_MAPPING: dict[str, int | None] = {
    "nw": 315,
    "n": 360,
    "ne": 45,
    "e": 90,
    "se": 135,
    "s": 180,
    "sw": 225,
    "w": 270,
    "c": 0,
}
"""Wind directions mapping."""


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
    AttributeMapper(ATTR_API_PRESSURE_MMHG),
    AttributeMapper(ATTR_API_TEMP_WATER),
    AttributeMapper(ATTR_API_TEMPERATURE),
    AttributeMapper(ATTR_API_WIND_GUST),
    AttributeMapper(ATTR_API_WIND_SPEED, default=0),
    AttributeMapper("daytime"),
]


FORECAST_ATTRIBUTE_TRANSLATION: list[AttributeMapper] = [
    AttributeMapper(
        "wind_dir", ATTR_FORECAST_WIND_BEARING, mapping=WIND_DIRECTION_MAPPING
    ),
    AttributeMapper("temp_avg", ATTR_FORECAST_NATIVE_TEMP),
    AttributeMapper("temp_min", ATTR_FORECAST_NATIVE_TEMP_LOW),
    AttributeMapper("pressure_pa", ATTR_FORECAST_NATIVE_PRESSURE),
    AttributeMapper("wind_speed", ATTR_FORECAST_NATIVE_WIND_SPEED, default=0),
    AttributeMapper("prec_mm", ATTR_FORECAST_NATIVE_PRECIPITATION, default=0),
    AttributeMapper("prec_prob", ATTR_FORECAST_PRECIPITATION_PROBABILITY, default=0),
    AttributeMapper(
        "condition", ATTR_FORECAST_CONDITION, mapping=WEATHER_STATES_CONVERSION
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
        self._updates_per_day = updates_per_day
        self._device_id = device_id
        self._name = name
        self._language = language

        if hass is not None:
            super().__init__(
                hass,
                _LOGGER,
                name=f"{self._name} updater",
                update_interval=self.update_interval,
                update_method=self.update,
            )
        self.data = {}

    @cached_property
    def update_interval(self) -> timedelta:
        """How often we may send requests.

        Site tariff have 50 free requests per day, but it may be changed
        """
        return timedelta(seconds=math.ceil((24 * 60 * 60) / self._updates_per_day))

    def process_fact_data(self, result: dict, fact_data: dict):
        """Convert Yandex API current weather state to HA friendly.

        :param result: weather data for HomeAssistant
        :param fact_data: weather data form Yandex
        """

        for attribute in CURRENT_WEATHER_ATTRIBUTE_TRANSLATION:
            value = fact_data.get(attribute.src, attribute.default)
            if attribute.mapping is not None and value is not None:
                value = map_state(
                    src=value,
                    mapping=attribute.mapping,
                    is_day=(fact_data["daytime"] == "d"),
                )
            if attribute.should_translate and value is not None:
                value = translate_condition(
                    value=value,
                    _language=self._language,
                )

            result[attribute.dst] = value

    def process_forecast_data(self, forecast: Forecast, f: dict):
        """Convert Yandex API forecast weather data to HA friendly.

        :param f: forecast weather data form Yandex
        :param forecast: instance of HA Forecast to fill
        """

        for attribute in FORECAST_ATTRIBUTE_TRANSLATION:
            value = f.get(attribute.src, attribute.default)
            if attribute.mapping is not None and value is not None:
                value = map_state(
                    src=value,
                    mapping=attribute.mapping,
                    is_day=(f["daytime"] == "d"),
                )
            if attribute.should_translate and value is not None:
                value = translate_condition(
                    value=value,
                    _language=self._language,
                )

            forecast[attribute.dst] = value  # type: ignore

    @staticmethod
    def get_min_forecast_temperature(forecasts: list[dict]) -> float | None:
        """Get minimum temperature from forecast data."""
        low_fc_temperatures: list[float] = []

        for f in forecasts:
            f_low_temperature: float = f.get(ATTR_FORECAST_NATIVE_TEMP_LOW, None)
            if f_low_temperature is not None:
                low_fc_temperatures.append(f_low_temperature)

        return min(low_fc_temperatures) if len(low_fc_temperatures) > 0 else None

    @staticmethod
    def get_timezone(nows: str, nowi: int) -> timezone:
        """Get API server timezone based on str and int time values."""
        server_utc_time = datetime.strptime(nows, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            microsecond=0
        )
        server_unix_time = datetime.fromtimestamp(nowi)
        return timezone(server_utc_time - server_unix_time)

    async def update(self):
        """Update weather information.

        :returns: dict with weather data.
        """
        result = {}
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            response = await self.request(
                session, self.__api_key, self._lat, self._lon, "en_US"
            )
            r = json.loads(response)

            _tz = self.get_timezone(r["now_dt"], r["now"])
            result = {
                ATTR_API_WEATHER_TIME: datetime.fromtimestamp(
                    r["fact"][ATTR_API_WEATHER_TIME], tz=_tz
                ),
            }
            self.process_fact_data(result, r["fact"])

            f_datetime = datetime.utcnow()
            for f in r["forecast"]["parts"]:
                result.setdefault(ATTR_FORECAST, [])
                f_datetime += timedelta(hours=24 / 4)
                forecast = Forecast()
                forecast[ATTR_FORECAST_TIME] = f_datetime.isoformat()  # type: ignore
                self.process_forecast_data(forecast, f)
                result[ATTR_FORECAST].append(forecast)
                forecast[ATTR_FORECAST_TIME] = f_datetime.isoformat()  # type: ignore
                try:
                    forecast[ATTR_FORECAST_WIND_BEARING] = map_state(  # type: ignore
                        src=f["wind_dir"],
                        mapping=WIND_DIRECTION_MAPPING,
                        is_day=f["daytime"] == "d",
                    )
                    forecast[ATTR_FORECAST_NATIVE_TEMP] = f["temp_avg"]  # type: ignore
                    forecast[ATTR_FORECAST_NATIVE_TEMP_LOW] = f["temp_min"]  # type: ignore
                    forecast[ATTR_FORECAST_NATIVE_PRESSURE] = f["pressure_pa"]  # type: ignore
                    forecast[ATTR_FORECAST_NATIVE_WIND_SPEED] = f.get("wind_speed", 0)  # type: ignore
                    forecast[ATTR_FORECAST_NATIVE_PRECIPITATION] = f.get("prec_mm", 0)  # type: ignore
                    forecast[ATTR_FORECAST_CONDITION] = map_state(  # type: ignore
                        src=f["condition"],
                        mapping=WEATHER_STATES_CONVERSION,
                        is_day=f["daytime"] == "d",
                    )
                    forecast[ATTR_FORECAST_PRECIPITATION_PROBABILITY] = f.get("prec_prob", 0)  # type: ignore
                    result[ATTR_FORECAST].append(forecast)
                except Exception as e:
                    _LOGGER.critical(
                        f"error while precessing forecast data {f}: {str(e)}"
                    )

            result[ATTR_MIN_FORECAST_TEMPERATURE] = self.get_min_forecast_temperature(
                result[ATTR_FORECAST]
            )

            return result

    @staticmethod
    async def request(
        session: aiohttp.ClientSession,
        api_key: str,
        lat: float,
        lon: float,
        lang: str = "en_US",
    ):
        """
        Make request to API endpoint.

        :param session: aiohttp.ClientSession: HTTP session for request
        :param api_key: str: API key
        :param lat: float: latitude of location where we are getting weather data
        :param lon: float: longitude of location where we ate getting weather data
        :param lang: str: Language for request, defaults to 'en_US'

        :returns: dict with response data
        :raises AssertionError: when response.status is not 200
        """
        headers = {"X-Yandex-API-Key": api_key}
        url = f"{API_URL}/v{API_VERSION}/informers?lat={lat}&lon={lon}&lang={lang}"
        _LOGGER.info("Sending API request")
        async with session.get(url, headers=headers) as response:
            try:
                assert response.status == 200
                _LOGGER.debug(f"{await response.text()}")
            except AssertionError as e:
                _LOGGER.error(f"Could not get data from API: {response}")
                raise aiohttp.ClientError(response.status, await response.text()) from e

            return await response.text()

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

        self._unsub_refresh = event.async_track_point_in_utc_time(
            self.hass,
            self._job,
            utcnow().replace(microsecond=0) + offset,
        )

    @property
    def device_id(self) -> str:
        """Device ID."""
        return self._device_id
