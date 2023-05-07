from homeassistant.components.binary_sensor import BinarySensorEntity
from .base import PetkitBinaryEntity

class PetkitBinarySensorEntity(PetkitBinaryEntity, BinarySensorEntity):
    pass