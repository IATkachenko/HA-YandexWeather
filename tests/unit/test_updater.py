import pytest
from custom_components.yandex_weather.updater import WeatherUpdater


class TestWeatherUpdater:
    async def test_update(self, hass, bypass_get_data):
        w = WeatherUpdater(0, 0, "", hass)
        await w.async_request_refresh()
        print(w)
