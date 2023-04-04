"""Tests for updater."""
from homeassistant.components.weather import ATTR_FORECAST_NATIVE_TEMP_LOW
import pytest

from custom_components.yandex_weather.const import ATTR_MIN_FORECAST_TEMPERATURE
from custom_components.yandex_weather.updater import WeatherUpdater

scenarios = {
    "test_data.json": [
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
        (ATTR_MIN_FORECAST_TEMPERATURE, -1),
    ],
}


forecasts_data = [
    ([{ATTR_FORECAST_NATIVE_TEMP_LOW: 10}], 10),
    (
        [
            {ATTR_FORECAST_NATIVE_TEMP_LOW: 10},
            {ATTR_FORECAST_NATIVE_TEMP_LOW: 5},
        ],
        5,
    ),
    (
        [
            {ATTR_FORECAST_NATIVE_TEMP_LOW: 5},
            {ATTR_FORECAST_NATIVE_TEMP_LOW: 10},
        ],
        5,
    ),
    ([], None),
]


def pytest_generate_tests(metafunc):
    tests = []
    for data, _tests in scenarios.items():
        tests += ((data, *t) for t in _tests)
    if "_bypass_get_data" in metafunc.fixturenames:
        metafunc.parametrize("_bypass_get_data, key, value", tests, indirect=["_bypass_get_data"])


@pytest.mark.asyncio
async def test_update(hass, key, value, _bypass_get_data):
    """Test update action."""
    w = WeatherUpdater(0, 0, "", hass, "test_device")
    await w.async_request_refresh()

    assert w.data[key] == value


@pytest.mark.parametrize("forecasts, expected", forecasts_data)
def test_min_forecast_temperature(hass, forecasts, expected):
    """Test min forecast temperature getter."""
    assert WeatherUpdater.get_min_forecast_temperature(forecasts) == expected
