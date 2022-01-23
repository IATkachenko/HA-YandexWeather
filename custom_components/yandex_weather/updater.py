"""Weather data updater."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import IntEnum
from functools import cached_property
import json
import logging
import math

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    ATTR_API_CONDITION,
    ATTR_API_WEATHER_TIME,
    ATTR_API_WIND_BEARING,
    DOMAIN,
)

API_URL = "https://api.weather.yandex.ru"
API_VERSION = "2"
_LOGGER = logging.getLogger(__name__)


class WindDirection(IntEnum):
    """Wind directions mapping."""

    nw = 315
    n = 360
    ne = 45
    e = 90
    se = 135
    s = 180
    sw = 225
    w = 270

    @classmethod
    def _missing_(cls, value):
        return 0


WEATHER_STATES_CONVERSION = {
    # "clear": "clear-night or sunny",
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


def map_state(state: str, is_day: bool = True) -> str:
    """
    Map weather condition based on WEATHER_STATES_CONVERSION.

    :param state: str: Yandex weather state
    :param is_day: bool: Is it day? Used for 'clear' state
    :return: str: Home Assistant weather state
    """
    try:
        state = WEATHER_STATES_CONVERSION[state]
    except KeyError:
        pass
    if state == "clear":
        state = "sunny" if is_day else "clear-night"

    return state


class WeatherUpdater(DataUpdateCoordinator):
    """Weather data updater for interaction with Yandex.Weather API."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        api_key: str,
        hass: HomeAssistant,
        updates_per_day: int = 50,
    ):
        """Initialize updater.

        :param latitude: latitude of location for weather data
        :param longitude: longitude of location for weather data
        :param api_key: Yandex weather API. MUST be weather for site tariff plan
        :param hass: Home Assistant object
        :param updates_per_day: int: how many updates per day we should do?
        """

        self.__api_key = api_key
        self._lat = latitude
        self._lon = longitude
        self._updates_per_day = updates_per_day

        if hass is not None:
            super().__init__(
                hass,
                _LOGGER,
                name=DOMAIN,
                update_interval=self.update_interval,
                update_method=self.update,
            )

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
            r["fact"][ATTR_API_WIND_BEARING] = WindDirection[
                r["fact"][ATTR_API_WIND_BEARING]
            ]
            r["fact"][ATTR_API_CONDITION] = map_state(
                r["fact"][ATTR_API_CONDITION], r["fact"]["daytime"] == "d"
            )

            return r

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
        :param lat: float: latitude of location where we getting weather data
        :param lon: float: longitude of location where we getting weather data
        :param lang: str: Language for request, defaults to 'en_US'

        :returns: dict with response data
        :raises AssertionError: when response.status is not 200
        """
        headers = {"X-Yandex-API-Key": api_key}
        url = f"{API_URL}/v{API_VERSION}/informers?lat={lat}&lon={lon}&lang={lang}"
        _LOGGER.info("Sending API request")
        async with session.get(url, headers=headers) as response:
            _LOGGER.debug(response)
            try:
                assert response.status == 200
            except AssertionError as e:
                raise aiohttp.ClientError(response.status, await response.text()) from e

            return await response.text()

    @property
    def weather_data(self) -> dict:
        """Weather data."""
        return self.data

    def __str__(self):
        """Show as pretty look data json."""
        _d = self.weather_data
        _d["fact"][ATTR_API_WEATHER_TIME] = str(_d["fact"][ATTR_API_WEATHER_TIME])
        return json.dumps(self.weather_data, indent=4, sort_keys=True)
