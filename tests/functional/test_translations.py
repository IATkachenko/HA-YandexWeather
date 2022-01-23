"""Tests for translations files."""

from __future__ import annotations

from functools import cache, cached_property
import json
import os
import sys

import pytest

sys.path.append(os.path.join(sys.path[0], "../../custom_components"))


class Translations:
    """Translations."""

    def __init__(self):
        """Initialize instance."""
        self.config: list[str] = []
        self.weather: list[str] = []
        self.sensor: list[str] = []

        for i in os.listdir(self.location):
            if i.startswith("sensor"):
                self.sensor.append(i)
            elif i.startswith("weather"):
                self.weather.append(i)
            else:
                self.config.append(i)

    @cached_property
    def location(self) -> str:
        """Location of the translations."""
        p = str(sys.path[0].replace("\\", "/"))

        if p.split("/")[-1] == "functional":
            p = os.path.join(sys.path[0], "../..")

        result = os.path.normpath(
            os.path.join(p, "custom_components/yandex_weather/translations")
        )

        return result

    @cached_property
    def en(self) -> str:
        """Name of English config flow strings file."""
        return f"{self.location}/en.json"


@cache
def get_translations() -> Translations:
    """Return Translations object."""
    return Translations()


@pytest.fixture()
def translations():
    """Fixture for Translations object."""
    return Translations()


class TestTranslations:
    """Tests for translations files."""

    def _have_en(self, where: []):
        """Make sure that we have English language file."""
        assert "en.json" in where

    def _compare_keys(self, d1: {}, d2: {}) -> list[str] | None:
        """Compare keys of two dicts.

        :returns: True if d1 and d2 have same keys
        """

        for k in d1.keys():
            d2_keys = d2.keys()
            if k not in d2_keys:
                return k
            if isinstance(d1[k], dict):
                s = self._compare_keys(d1[k], d2[k])
                if s is not None:
                    return f"{k}/{s}"
        return None

    @pytest.mark.parametrize("translation", get_translations().config)
    def test_config_all_defined(self, translations, translation):
        """Make sure thar translation have all fields like English version."""
        if translation == "en.json":
            pytest.skip(
                f"Skipping {translation} because we should compare it with itself"
            )

        with open(translations.en) as en:
            en_json = json.load(en)
            with open(f"{translations.location}/{translation}") as tr:
                tr_json = json.load(tr)
                if (d := self._compare_keys(en_json, tr_json)) is not None:
                    pytest.fail(f"{d} is missed for {t}")

    @pytest.mark.parametrize("translation", get_translations().config)
    def test_config_same_values(self, translations, translation):
        """Make sure that we have same description for config and options dialogs."""
        with open(f"{translations.location}/{translation}") as f:
            content = json.load(f)
            c_keys = content["config"]["step"]["user"]["data"].keys()
            o_keys = content["options"]["step"]["init"]["data"].keys()
            for k in set(c_keys).intersection(o_keys):
                config_value = content["config"]["step"]["user"]["data"].get(k)
                option_value = content["options"]["step"]["init"]["data"].get(k)
                assert config_value == option_value

    def test_config_have_en(self, translations):
        """Test if config flow have base (English) strings."""
        self._have_en(translations.config)

    def test_weather_have_en(self, translations):
        """Test if weather have base (English) strings."""
        if len(translations.weather) == 0:
            pytest.skip("Have no weather translations at all")
        self._have_en(translations.weather)

    def test_sensor_have_en(self, translations):
        """Test if sensor have base (English) strings."""
        if len(translations.sensor) == 0:
            pytest.skip("Have no sensor translations at all")
        self._have_en(translations.sensor)
