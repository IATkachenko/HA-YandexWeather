from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)

from homeassistant.const import (
    PERCENTAGE,
    PRESSURE_HPA,
    SPEED_METERS_PER_SECOND,
    TEMP_CELSIUS,
    Platform,
)

DOMAIN = "yandex_weather"
DEFAULT_NAME = "Yandex Weather"
DEFAULT_UPDATES_PER_DAY = 50
ATTRIBUTION = "Data provided by Yandex Weather"
MANUFACTURER = "Yandex"
ENTRY_NAME = "name"
UPDATER = "updater"
UPDATES_PER_DAY = "updates_per_day"

ATTR_API_TEMPERATURE = "temp"
ATTR_API_FEELS_LIKE_TEMPERATURE = "feels_like"
ATTR_API_WIND_SPEED = "wind_speed"
ATTR_API_WIND_BEARING = "wind_dir"
ATTR_API_HUMIDITY = "humidity"
ATTR_API_PRESSURE = "pressure_pa"
ATTR_API_CONDITION = "condition"
ATTR_API_IMAGE = "icon"
ATTR_API_WEATHER_TIME = "obs_time"

CONF_UPDATES_PER_DAY = "updates_per_day"
UPDATE_LISTENER = "update_listener"
PLATFORMS = [Platform.SENSOR, Platform.WEATHER]


WEATHER_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=ATTR_API_TEMPERATURE,
        name="Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key=ATTR_API_FEELS_LIKE_TEMPERATURE,
        name="Feels like temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key=ATTR_API_WIND_SPEED,
        name="Wind speed",
        native_unit_of_measurement=SPEED_METERS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key=ATTR_API_WIND_BEARING,
        name="Wind bearing",
        native_unit_of_measurement="",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key=ATTR_API_HUMIDITY,
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key=ATTR_API_PRESSURE,
        name="Pressure",
        native_unit_of_measurement=PRESSURE_HPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key=ATTR_API_CONDITION,
        name="Condition",
        entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key=ATTR_API_WEATHER_TIME,
        name="Data update time",
        device_class=SensorDeviceClass.TIMESTAMP,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=True,
        entity_category="diagnostic"
    ),
)
