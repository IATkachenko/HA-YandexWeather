"""Tests for updater."""
import pytest

from custom_components.yandex_weather.const import ATTR_MIN_FORECAST_TEMPERATURE
from custom_components.yandex_weather.updater import WeatherUpdater

testdata = [
    ("condition", "cloudy"),
    ("daytime", "d"),
    ("feels_like", -5),
    ("humidity", 89),
    ("icon", "bkn_d"),
    ("min_forecast_temperature", -1),
    ("original_condition", "cloudy"),
    ("pressure_mm", 723),
    ("pressure_pa", 963),
    ("temp", 1),
    ("wind_dir", 270),
    ("wind_gust", 13.9),
    ("wind_speed", 6.2),
    ("yandex_condition", "cloudy"),
    (ATTR_MIN_FORECAST_TEMPERATURE, -1)
]


@pytest.mark.parametrize("key,value", testdata)
@pytest.mark.asyncio
async def test_update(hass, key, value):
    """Test update action."""
    w = WeatherUpdater(0, 0, "", hass, "test_device")
    await w.async_request_refresh()

    assert w.data[key] == value
