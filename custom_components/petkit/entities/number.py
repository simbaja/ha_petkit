from homeassistant.components.number import RestoreNumber

from ..devices import PetkitDevice
from .base import PetkitEntity

class PetkitNumberEntity(PetkitEntity, RestoreNumber):
    def __init__(self, name, device: PetkitDevice, option=None):
        super().__init__(name, device, option)