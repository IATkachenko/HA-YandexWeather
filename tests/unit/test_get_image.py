"""Tests for const::get_image."""
import pytest

from custom_components.yandex_weather.const import (
    ATTR_API_IMAGE,
    ATTR_API_ORIGINAL_CONDITION,
    get_image,
)
from custom_components.yandex_weather.updater import WeatherUpdater

none_testdata = [
    ("ThereIsNoSuchKey", "foo"),
    ("HomeAssistant", "any"),
]


yandex_testdata = [
    ("test_data.json", "https://yastatic.net/weather/i/icons/funky/dark/bkn_d.svg"),
]


@pytest.mark.parametrize("source,condition", none_testdata)
def test_get_none_image(source, condition):
    """Test get_image action."""
    assert get_image(source, condition, "some", False) is None


@pytest.mark.parametrize("_bypass_get_data, image", yandex_testdata, indirect=["_bypass_get_data"])
@pytest.mark.asyncio
async def test_yandex_image(hass, _bypass_get_data, image):
    """Test is image correct for Yandex image provider.

    Like in `weather` component.
    """

    w = WeatherUpdater(0, 0, "", hass, "test_device")
    await w.async_request_refresh()
    assert image == get_image(
        image_source="Yandex",
        condition=w.data.get(ATTR_API_ORIGINAL_CONDITION),
        is_day=w.data.get("daytime") == "d",
        image=w.data.get(ATTR_API_IMAGE),
    )
