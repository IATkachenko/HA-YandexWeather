"""Tests for const::get_image."""
import pytest

from custom_components.yandex_weather.const import get_image

none_testdata = [
    ("ThereIsNoSuchKey", "foo"),
    ("HomeAssistant", "any"),
]


@pytest.mark.parametrize("source,condition", none_testdata)
def test_get_none_image(source, condition):
    """Test get_image action."""
    assert get_image(source, condition, "some", False) is None
