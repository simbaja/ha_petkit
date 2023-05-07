import logging
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entities import PetkitNumberEntity
from .update_coordinator import PetkitUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable):
    _LOGGER.debug('Adding Petkit numbers')
    coordinator: PetkitUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    devices = list(coordinator.devices.values())
    _LOGGER.debug(f'Found {len(devices):d} devices')
    entities = [
        entity
        for device in devices
        for entity in device.entities
        if isinstance(entity, PetkitNumberEntity)
    ]
    _LOGGER.debug(f'Found {len(entities):d} numbers')

    #restore their last state
    for e in entities:
        await e.async_get_last_number_data()

    async_add_entities(entities)
