"""Tests for updater."""
import pytest

from custom_components.yandex_weather.const import map_state
from custom_components.yandex_weather.updater import WIND_DIRECTION_MAPPING


@pytest.mark.asyncio
async def test_mapping():
    """Test mapping action."""
    assert 270 == map_state(src="w", mapping=WIND_DIRECTION_MAPPING)
    assert 0 == map_state(src="c", mapping=WIND_DIRECTION_MAPPING)
