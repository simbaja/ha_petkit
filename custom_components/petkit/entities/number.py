from homeassistant.components.number import RestoreNumber

from ..devices import PetkitDevice
from .base import PetkitEntity

class PetkitNumberEntity(PetkitEntity, RestoreNumber):
    def __init__(self, name, device: PetkitDevice, option=None):
        super().__init__(name, device, option)

class PetkitFeedAmountEntity(PetkitNumberEntity):
    def __init__(self, name, device: PetkitDevice, option=None):
        super().__init__(name, device, option)
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_value = 10
