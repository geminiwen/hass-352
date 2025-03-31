"""352 Air Purifier integration."""
import logging
import requests
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from datetime import timedelta

from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import Throttle
from homeassistant.components.sensor import PLATFORM_SCHEMA


_LOGGER = logging.getLogger(__name__)

DOMAIN = "352"
SCAN_INTERVAL = timedelta(minutes=5)
API_ENDPOINT = "https://app.352air.com/api"  # 替换为实际的API地址

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string
})

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the 352 Air Purifier sensor."""
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    name = "Air Purifier"

    try:
        token = await hass.async_add_executor_job(
            get_auth_token, username, password
        )
        if not token:
            _LOGGER.error("Failed to get auth token")
            return

        sensor = AirPurifierSensor(name, token)
        add_entities([sensor], True)

    except Exception as ex:
        _LOGGER.error("Failed to set up 352 sensor: %s", str(ex))

def get_auth_token(username: str, password: str) -> str:
    """Get authentication token from API."""
    try:
        response = requests.post(
            f"{API_ENDPOINT}/v1/enduser/login",
            json={
                "account": username, 
                "password": password,
                "area": "86"
            }
        )
        response.raise_for_status()
        return response.json().get("data").get("access_token")
    except requests.RequestException as ex:
        _LOGGER.error("Error getting auth token: %s", str(ex))
        return None

class AirPurifierSensor(SensorEntity):
    """Representation of a 352 Air Purifier sensor."""

    def __init__(self, name: str, token: str):
        """Initialize the sensor."""
        self._name = name
        self._token = token
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "µg/m³"

    @property
    def device_class(self):
        """Return the device class."""
        return "pm25"

    @property
    def unique_id(self):
        return "sensor.352_air_4F1Dlq5rooAZmvzbu0xU000000"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @Throttle(SCAN_INTERVAL)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            response = requests.get(
                f"{API_ENDPOINT}/device/info/4F1Dlq5rooAZmvzbu0xU000000",
                headers={"Authorization": f"Token {self._token}"}
            )
            response.raise_for_status()
            data = response.json()

            self._state = data["data"]["property"]["PM25"]["value"]  # 假设API返回PM2.5数据
            self._attributes = {
                "value": data["data"]["property"]["PM25"]["value"],
                # 添加更多属性
            }
        except requests.RequestException as ex:
            _LOGGER.error("Error updating sensor: %s", str(ex))
