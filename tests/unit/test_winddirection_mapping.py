"""Tests for updater."""

from custom_components.yandex_weather.const import map_state
from custom_components.yandex_weather.updater import WIND_DIRECTION_MAPPING


async def test_mapping():
    """Test mapping action."""
    assert 270 == map_state(src="w", mapping=WIND_DIRECTION_MAPPING)
    assert map_state(src="c", mapping=WIND_DIRECTION_MAPPING) is None
