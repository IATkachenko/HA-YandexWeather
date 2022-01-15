from __future__ import annotations
import unittest
import sys
import os
import json

sys.path.append(os.path.join(sys.path[0], "../../custom_components"))


class TranslationsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:

        if sys.path[0].split("\\")[-1] == "functional":
            p = os.path.join(sys.path[0], '../..')
        else:
            p = sys.path[0]
        cls._translations_location = os.path.normpath(os.path.join(
            p,
            "custom_components/yandex_weather/translations"
        ))
        cls._config = []
        cls._weather = []
        cls._sensor = []

        for i in os.listdir(cls._translations_location):
            if i.startswith('sensor'):
                cls._sensor.append(i)
            elif i.startswith('weather'):
                cls._weather.append(i)
            else:
                cls._config.append(i)

    def _have_en(self, where: []):
        """Make sure that we have English language file"""
        self.assertIn('en.json', where)

    def _compare_keys(self, d1: {}, d2: {}) -> list[str] | None:
        """
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

    def test_config_all_defined(self):
        """Make sure thar translation have all fields like English version"""

        en_name = 'en.json'
        with open(f"{self._translations_location}/{en_name}") as en:
            en_json = json.load(en)
            for t in self._config:
                if t == en_name:  # skip English itself
                    continue
                with self.subTest(translation=t.removesuffix('.json')):
                    with open(f"{self._translations_location}/{t}") as tr:
                        tr_json = json.load(tr)

                        if (d := self._compare_keys(en_json, tr_json)) is not None:
                            self.fail(f"{d} is missed for {t}")

    def test_config_same_values(self):
        """Make sure that we have same description for config and options dialogs"""
        for i in self._config:
            with open(f"{self._translations_location}/{i}") as f:
                content = json.load(f)
                c_keys = content['config']['step']['user']['data'].keys()
                o_keys = content['options']['step']['init']['data'].keys()
                for k in set(c_keys).intersection(o_keys):
                    with self.subTest(translation=i.removesuffix('.json'), key=k):
                        config_value = content['config']['step']['user']['data'].get(k)
                        option_value = content['options']['step']['init']['data'].get(k)
                        self.assertEqual(config_value, option_value)

    def test_config_have_en(self):
        self._have_en(self._config)

    def test_weather_have_en(self):
        if len(self._weather) == 0:
            self.skipTest("Have no weather translations at all")
        self._have_en(self._weather)

    def test_sensor_have_en(self):
        if len(self._sensor) == 0:
            self.skipTest("Have no sensor translations at all")
        self._have_en(self._sensor)



