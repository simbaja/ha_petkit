import asyncio

from homeassistant.components.select import SelectEntity

from ..devices import PetkitDevice
from .base import PetkitEntity

class PetkitSelectEntity(PetkitEntity, SelectEntity):
    def __init__(self, name, device: PetkitDevice, option=None):
        super().__init__(name, device, option)
        self._attr_current_option = None
        self._attr_options = self._option.get('options')

    def update(self):
        super().update()
        self._attr_current_option = self._attr_state

    async def async_select_option(self, option: str):
        """Change the selected option."""
        ret = False
        fun = self._option.get('async_select')

        if callable(fun):
            kws = {
                'entity': self,
            }
            ret = await fun(option, **kws)

        if ret:
            self._attr_current_option = option
            self.async_write_ha_state()
            if dly := self._option.get('delay_update'):
                await asyncio.sleep(dly)
                self._handle_coordinator_update()
        return ret
