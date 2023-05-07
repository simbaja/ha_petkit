import logging
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entities import PetkitSelectEntity
from .update_coordinator import PetkitUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable):
    _LOGGER.debug('Adding Petkit selects')
    coordinator: PetkitUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    devices = list(coordinator.devices.values())
    _LOGGER.debug(f'Found {len(devices):d} devices')
    entities = [
        entity
        for device in devices
        for entity in device.entities
        if isinstance(entity, PetkitSelectEntity)
    ]
    _LOGGER.debug(f'Found {len(entities):d} selects')
    async_add_entities(entities)
