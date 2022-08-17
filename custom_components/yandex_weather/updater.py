"""Weather data updater."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import cached_property
import json
import logging
import math

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
    ATTR_API_PRESSURE,
    ATTR_API_PRESSURE_MMHG,
    ATTR_API_TEMPERATURE,
    ATTR_API_WEATHER_TIME,
    ATTR_API_WIND_BEARING,
    ATTR_API_WIND_SPEED,
    ATTR_API_YA_CONDITION,
    ATTR_MIN_FORECAST_TEMPERATURE,
    CONDITION_ICONS,
    DOMAIN,
    MANUFACTURER,
    WEATHER_STATES_CONVERSION,
    map_state,
)
from .device_trigger import TRIGGERS

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


def translate_condition(value: str, _language: str) -> str:
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
        language: str = "en_US",
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

            server_utc_time = datetime.strptime(
                r["now_dt"], "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(microsecond=0)
            server_unix_time = datetime.fromtimestamp(r["now"])
            _tz = timezone(server_utc_time - server_unix_time)
            r["fact"][ATTR_API_WEATHER_TIME] = datetime.fromtimestamp(
                r["fact"][ATTR_API_WEATHER_TIME], tz=_tz
            )
            r["fact"][ATTR_API_WIND_BEARING] = map_state(
                src=r["fact"][ATTR_API_WIND_BEARING],
                mapping=WIND_DIRECTION_MAPPING,
            )
            r["fact"][ATTR_API_YA_CONDITION] = r["fact"][ATTR_API_CONDITION]
            r["fact"][f"{ATTR_API_YA_CONDITION}_icon"] = map_state(
                r["fact"][ATTR_API_YA_CONDITION],
                r["fact"]["daytime"] == "d",
                CONDITION_ICONS,
            )
            r["fact"][ATTR_API_YA_CONDITION] = translate_condition(
                value=r["fact"][ATTR_API_YA_CONDITION],
                _language=self._language,
            )
            r["fact"][ATTR_API_CONDITION] = map_state(
                r["fact"][ATTR_API_CONDITION],
                r["fact"]["daytime"] == "d",
                WEATHER_STATES_CONVERSION,
            )
            if (
                self.data
                and r["fact"][ATTR_API_CONDITION] != self.data[ATTR_API_CONDITION]
                and self.hass is not None
                and r["fact"][ATTR_API_CONDITION] in TRIGGERS
            ):

                self.hass.bus.async_fire(
                    DOMAIN + "_event",
                    {
                        "device_id": self._device_id,
                        "type": r["fact"][ATTR_API_CONDITION],
                    },
                )
            for i in [
                ATTR_API_CONDITION,
                ATTR_API_FEELS_LIKE_TEMPERATURE,
                ATTR_API_HUMIDITY,
                ATTR_API_IMAGE,
                ATTR_API_PRESSURE,
                ATTR_API_PRESSURE_MMHG,
                ATTR_API_TEMPERATURE,
                ATTR_API_WEATHER_TIME,
                ATTR_API_WIND_BEARING,
                ATTR_API_WIND_SPEED,
                ATTR_API_YA_CONDITION,
                "daytime",
            ]:
                result[i] = r["fact"][i]

            f_datetime = datetime.utcnow()
            for f in r["forecast"]["parts"]:
                result.setdefault(ATTR_FORECAST, [])
                forecast = Forecast()
                f_datetime += timedelta(hours=24 / 4)
                forecast[ATTR_FORECAST_TIME] = f_datetime.isoformat()  # type: ignore

                forecast[ATTR_FORECAST_WIND_BEARING] = map_state(  # type: ignore
                    src=f["wind_dir"],
                    mapping=WIND_DIRECTION_MAPPING,
                    is_day=f["daytime"] == "d",
                )
                forecast[ATTR_FORECAST_NATIVE_TEMP] = f["temp_avg"]  # type: ignore
                forecast[ATTR_FORECAST_NATIVE_TEMP_LOW] = f["temp_min"]  # type: ignore
                forecast[ATTR_FORECAST_NATIVE_PRESSURE] = f["pressure_pa"]  # type: ignore
                forecast[ATTR_FORECAST_NATIVE_WIND_SPEED] = f["wind_speed"]  # type: ignore
                forecast[ATTR_FORECAST_NATIVE_PRECIPITATION] = f["prec_mm"]  # type: ignore
                forecast[ATTR_FORECAST_CONDITION] = map_state(  # type: ignore
                    src=f["condition"],
                    mapping=WEATHER_STATES_CONVERSION,
                    is_day=f["daytime"] == "d",
                )
                forecast[ATTR_FORECAST_PRECIPITATION_PROBABILITY] = f["prec_prob"]  # type: ignore
                result.setdefault(ATTR_MIN_FORECAST_TEMPERATURE, forecast[ATTR_FORECAST_NATIVE_TEMP_LOW])  # type: ignore
                result[ATTR_MIN_FORECAST_TEMPERATURE] = min(
                    result[ATTR_MIN_FORECAST_TEMPERATURE],
                    forecast[ATTR_FORECAST_NATIVE_TEMP_LOW],  # type: ignore
                )
                result[ATTR_FORECAST].append(forecast)

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
            identifiers={(DOMAIN, self._device_id)},
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


