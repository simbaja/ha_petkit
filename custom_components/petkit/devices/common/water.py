import logging
from typing import List

from homeassistant.const import *
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ...api import PetkitAccount
from .base import PetkitDevice

_LOGGER = logging.getLogger(__name__)

class PetkitWaterDevice(PetkitDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        super().__init__(data, coordinator, account)

    @property
    def state(self):
        dat = self.status or {}
        if dat.get('lackWarning'):
            return 'water_lack'
        if dat.get('breakdownWarning'):
            return 'breakdown'
        if dat.get('runStatus'):
            return 'working'
        if dat.get('powerStatus'):
            return 'idle'
        return None

    def state_attrs(self):
        return self._cache

    @property
    def filter_level(self):
        return self._cache.get('filterPercent')

    @property
    def filter_days(self):
        return self._cache.get('filterExpectedDays')

    def _get_all_entities(self) -> List[Entity]:
        from ...entities import PetkitSensorEntity
        base_entities = super()._get_all_entities()

        water_entities = [
            PetkitSensorEntity('filter_days', self, {'unit': 'days', 'icon': 'mdi:air-filter' }),
            PetkitSensorEntity('filter_level', self, {})
        ]

        entities = base_entities + water_entities
        
        return entities
