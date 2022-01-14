import aiohttp
import json
import logging
import math
from typing import Dict
from datetime import timedelta
from functools import cached_property
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN


API_URL = 'https://api.weather.yandex.ru'
API_VERSION = '2'
_LOGGER = logging.getLogger(__name__)


class WeatherUpdater(DataUpdateCoordinator):
    def __init__(self, latitude: float, longitude: float, api_key: str, hass: HomeAssistant, updates_per_day: int = 50):
        """
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
        self._result = {}
        if hass is not None:
            super().__init__(
                hass, _LOGGER, name=DOMAIN, update_interval=self.update_interval, update_method=self.update
            )

    @cached_property
    def update_interval(self) -> timedelta:
        """How often we may send requests?

        Site tariff have 50 free requests per day, but it may be changed
        """
        return timedelta(seconds=math.ceil((24 * 60 * 60) / self._updates_per_day))

    async def update(self):
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            response = await self.request(session, self.__api_key, self._lat, self._lon, 'en_US')
            self._result = json.loads(response)

    @staticmethod
    async def request(session: aiohttp.ClientSession, api_key: str, lat: float, lon: float, lang: str = 'en_US'):
        headers = {"X-Yandex-API-Key": api_key}
        url = f"{API_URL}/v{API_VERSION}/informers?lat={lat}&lon={lon}&lang={lang}"
        _LOGGER.info(f"Sending API request")
        async with session.get(url, headers=headers) as response:
            _LOGGER.debug(response)
            try:
                assert response.status == 200
            except AssertionError as e:
                raise aiohttp.ClientError(response.status, await response.text()) from e

            return await response.text()

    @property
    def weather_data(self) -> Dict:
        return self._result

    def __str__(self):
        return json.dumps(self.weather_data, indent=4, sort_keys=True)
