![version_badge](https://img.shields.io/badge/minimum%20HA%20version-2021.12-red)
# Yandex weather integration for Home Assistant 
This custom integration is providing weather component and set of sensors based on data from [yandex weather](https://weather.yadex.ru) service.

## Installation
### HACS
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration) [![HACS Action](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hacs.yml/badge.svg)](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hacs.yml) [![Validate with hassfest](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hassfest.yaml)
1. Go to HACS
2. Start typing "Yandex weather" in search field
3. Press "Download" button
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
    * Start typing "Yandex weather"
    * Add integration
    * Put API key into API key field

## Usage
### Weather
#### attributes
 * `entity_picture` -- native Yandex.Weather .svg picture for weather condition
### Sensors
Most sensors are disabled by default to not overload system. 
 
* ![added_in_version_badge](https://img.shields.io/badge/Since-v0.3.0-red) `data update time` -- when weather data was updated (at Yandex side).
* ![added_in_version_badge](https://img.shields.io/badge/Since-v0.4.0-red) `original_condition` -- native Yandex.Weather condition. Because Yandex weather conditions is richer than Home Assistant, some different Yandex.Weather conditions is mapped to same Home Assistant. This sensor will keep original condition.  
### Events
![added_in_version_badge](https://img.shields.io/badge/Since-v0.4.0-red) integration will fire events on weather condition changes. This events may be used for triggering automatizations.
