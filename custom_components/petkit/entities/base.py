import logging

from homeassistant.const import *
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

from ..devices import PetkitDevice

class PetkitEntity(CoordinatorEntity):
    def __init__(self, name, device: PetkitDevice, option=None):
        CoordinatorEntity.__init__(self, device.coordinator)
        
        self._coordinator = device.coordinator
        self._name = name
        self._device = device
        self._option = option or {}      

        self._attr_name = f'{device.name} {name}'.strip()
        self._attr_device_id = device.id
        self._attr_unique_id = f'{self._attr_device_id}-{name}'
        self._attr_icon = self._option.get('icon')
        self._attr_device_class = self._option.get('class')
        self._attr_unit_of_measurement = self._option.get('unit')

        self._attr_device_info = {
            'identifiers': device.id,
            'name': device.name,
            'model': device.type,
            'manufacturer': 'Petkit',
            'sw_version': device.firmware_version
        }

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    def _handle_coordinator_update(self):
        self.update()
        self.async_write_ha_state()

    def update(self):
        if hasattr(self._device, self._name):
            self._attr_state = getattr(self._device, self._name)
            _LOGGER.debug('Petkit entity update: %s', [self.entity_id, self._name, self._attr_state])

        fun = self._option.get('state_attrs')
        if callable(fun):
            self._attr_extra_state_attributes = fun()

    @property
    def state(self):
        return self._attr_state

    @property
    def unit_of_measurement(self):
        return self._attr_unit_of_measurement

    @property
    def device_info(self):
        return self._device.device_info

class PetkitBinaryEntity(PetkitEntity):
    def __init__(self, name, device: PetkitDevice, option=None):
        super().__init__(name, device, option)
        self._attr_is_on = False

    def update(self):
        super().update()
        if hasattr(self._device, self._name):
            self._attr_is_on = not not getattr(self._device, self._name)
        else:
            self._attr_is_on = False

    @property
    def state(self):
        return STATE_ON if self._attr_is_on else STATE_OFF
