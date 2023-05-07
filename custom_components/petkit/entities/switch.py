import asyncio

from homeassistant.components.switch import SwitchEntity

from .base import PetkitBinaryEntity

class PetkitSwitchEntity(PetkitBinaryEntity, SwitchEntity):

    async def async_turn_switch(self, on=True, **kwargs):
        """Turn the entity on/off."""
        ret = False
        fun = self._option.get('async_turn_on' if on else 'async_turn_off')
        if callable(fun):
            kwargs['entity'] = self
            ret = await fun(**kwargs)
        if ret:
            self._attr_is_on = not not on
            self.async_write_ha_state()
            await asyncio.sleep(1)
            self._handle_coordinator_update()
        return ret

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        return await self.async_turn_switch(True)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        return await self.async_turn_switch(False)
