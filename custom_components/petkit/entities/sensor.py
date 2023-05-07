from homeassistant.components.sensor import SensorEntity

from .base import PetkitEntity

class PetkitSensorEntity(PetkitEntity, SensorEntity):
    """ PetkitSensorEntity """
