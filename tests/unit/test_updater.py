"""Tests for updater."""

from custom_components.yandex_weather.updater import WeatherUpdater


async def test_update(hass):
    """Test update action."""
    w = WeatherUpdater(0, 0, "", hass, "test_device")
    await w.async_request_refresh()
    print(w)
