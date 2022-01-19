![version_badge](https://img.shields.io/badge/minimum%20HA%20version-2021.12-red)
# Yandex weather integration for Home Assistant 
This custom integration is providing weather component and set of sensors based on data from [yandex weather](https://weather.yadex.ru) service.

## Installation
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration) [![HACS Action](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hacs.yml/badge.svg)](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hacs.yml) [![Validate with hassfest](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/IATkachenko/HA-YandexWeather/actions/workflows/hassfest.yaml)
1. Go to HACS
2. Three dots -> User repositories
   * **Repository**: https://github.com/IATkachenko/HA-YandexWeather.git
   * **Category**: Integration
   * Press "Add" button
3. At integrations press add
4. Start typing "Yandex weather" in search field
5. Click at repository
6. Press "Download with HACS" button
 
## Configuration
1. Go to Yandex [developer page](https://developer.tech.yandex.ru/services)
2. Add Weather API with "Test tariff" _(3000 requests for 30 days for free)_
3. Switch to "Weather for web-site tariff" _(50 requests per day for free)_
4. Save API key
5. Go to Home Assistant
    * Integrations
    * Add
    * Start typing "Yandex weather"
    * Add integration
    * Put API key into API key field
    * Select forecast type (hourly/daily)

## Usage
### Weather
#### attributes
 * `entity_picture` -- native Yandex.Weather .svg picture for weather condition
### Sensors
Most sensors are disabled by default to not overload system. 
 
* ![added_in_version_badge](https://img.shields.io/badge/Since-v0.3.0-red) `data update time` -- when weather data was updated (at Yandex side).