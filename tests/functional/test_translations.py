import unittest
import sys
import os

sys.path.append(os.path.join(sys.path[0], "../../custom_components"))


class TranslationsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _translations_location = os.path.normpath(os.path.join(
            sys.path[0].replace('\\\\', '/'),
            "custom_components/yandex_weather/translations"
        ))
        cls._config = []
        cls._weather = []
        cls._sensor = []

        for i in os.listdir(_translations_location):
            if i.startswith('sensor'):
                cls._sensor.append(i)
            elif i.startswith('weather'):
                cls._weather.append(i)
            else:
                cls._config.append(i)

    def _have_en(self, where: []):
        """Make sure that we have English language file"""
        self.assertIn('en.json', where)

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



