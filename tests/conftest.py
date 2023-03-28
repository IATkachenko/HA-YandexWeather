"""Global fixtures."""

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import load_fixture


@pytest.fixture(name="_bypass_get_data", autouse=True)
def bypass_get_data_fixture():
    """Skip calls to get data from API."""
    with patch(
        "custom_components.yandex_weather.updater.WeatherUpdater.request",
        AsyncMock(return_value=load_fixture("test_data.json")),
    ):
        yield
