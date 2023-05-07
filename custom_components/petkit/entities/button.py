from homeassistant.components.button import ButtonEntity

from ..devices import PetkitDevice
from .base import PetkitEntity

class PetkitButtonEntity(PetkitEntity, ButtonEntity):
    def __init__(self, name, device: PetkitDevice, option=None):
        super().__init__(name, device, option)

    async def async_press(self):
        """Press the button."""
        ret = False
        fun = self._option.get('async_press')
        if callable(fun):
            kws = {
                'entity': self,
            }
            ret = await fun(**kws)
        return ret
