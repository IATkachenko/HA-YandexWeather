![version_badge](https://img.shields.io/badge/minimum%20HA%20version-2021.12-red)
# Yandex weather data provider for Home Assistant
This custom integration is providing weather component and set of sensors based on data from [yandex weather](https://weather.yandex.ru) service.

## Installation
### HACS
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration) [![HACS Action](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hacs.yml/badge.svg)](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hacs.yml) [![Validate with hassfest](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hassfest.yaml)
1. Go to HACS
2. Start typing "Yandex weather" in search field
3. Press "Download" button
4. Restart Home Assistant
### Manual
1. Download [yandex_weather.zip](https://github.com/IATkachenko/HA-YandexWeather/releases/download/latest/yandex_weather.zip) from the latest release
2. Unpack to `cunstom_components` folder _(it should look like `custom_componets/yandex_weather/<files>`)_
3. Restart Home Assistant

## Configuration
1. Go to Yandex [developer page](https://developer.tech.yandex.ru/services)
2. Add Weather API with "Test tariff" _(3000 requests for 30 days for free)_
3. Switch to "Weather for web-site tariff" _(50 requests per day for free)_. It may require up to 30 minutes for activating key.
4. Save API key
5. Go to Home Assistant settings
    * Integrations
    * Add
    * Start typing "Yandex weather" _(clean browser cache if nothing found)_
    * Add integration
    * Put API key into API key field

## Usage
### Weather
 * ![added_in_version_badge](https://img.shields.io/badge/Since-v1.0.0-red) pressure, wind speed and other unit may be customized
 * ![added_in_version_badge](https://img.shields.io/badge/Since-v0.8.0-red) forecast data is available for next two periods (morning/day/evening/night) 
#### attributes
 * `entity_picture`:
   * ![added_in_version_badge](https://img.shields.io/badge/Before-v0.10.0-gray) native Yandex.Weather .svg picture for weather condition 
   * ![added_in_version_badge](https://img.shields.io/badge/Since-v0.10.0-red) picture based on one of selected source  (see [#30](https://github.com/IATkachenko/HA-YandexWeather/issues/30) for details):
     * native Home Assistant, based on condition
     * native Yandex (like before v0.10.0)
     * animated from [Custom weather card](https://github.com/bramkragten/weather-card)
     * static from [Custom weather card](https://github.com/bramkragten/weather-card)
 
### Sensors
Most sensors are disabled by default to not overload system. 
 
* ![added_in_version_badge](https://img.shields.io/badge/Since-v0.3.0-red) `data update time` -- when weather data was updated (at Yandex side).
* ![added_in_version_badge](https://img.shields.io/badge/Since-v0.4.0-red) `original_condition` -- native Yandex.Weather condition. Because Yandex weather conditions is richer than Home Assistant, some different Yandex.Weather conditions is mapped to same Home Assistant. This sensor will keep original condition.
* ![added_in_version_badge](https://img.shields.io/badge/Since-v0.6.0-red) `pressure_mmhg` -- pressure in mmHg units. Home Asistant is prefer Pa as pressure units, but mmHg is more familiar for some countries. This sensor is enabled by default.
* ![added_in_version_badge](https://img.shields.io/badge/Since-v0.9.0-red) `minimal_forecast_temperature` -- minimal temperature for all forecast periods.
### Events
![added_in_version_badge](https://img.shields.io/badge/Since-v0.4.0-red) integration will fire events on weather condition changes. This events may be used for triggering automatizations.
