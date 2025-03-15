"""Tests for updater."""
import pytest

from custom_components.yandex_weather.const import map_state
from custom_components.yandex_weather.updater import WIND_DIRECTION_MAPPING

testdata = [
    ("WEST", 270),
    ("CALM", 0),
]


@pytest.mark.parametrize("direction,expected", testdata)
@pytest.mark.asyncio
async def test_mapping(direction, expected):
    """Test mapping action."""
    assert expected == map_state(src=direction, mapping=WIND_DIRECTION_MAPPING)
