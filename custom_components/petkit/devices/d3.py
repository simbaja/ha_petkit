from typing import List

from homeassistant.const import *
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..api import PetkitAccount
from ..entities import PetkitSensorEntity
from .common import PetkitFeederDevice

class D3FeederDevice(PetkitFeederDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        super().__init__(data, coordinator, account)    
        
    @property
    def feed_times(self):
        times = self.feed_state_attrs().get('feedTimes', [])
        return len(times)

    def _get_all_entities(self) -> List[Entity]:
        base_entities = super()._get_all_entities()

        entities = [
            PetkitSensorEntity('eat_amount', self, {
                'unit': MASS_GRAMS,
                'icon': 'mdi:weight-gram',
            }),
            PetkitSensorEntity('eat_times', self, {
                'unit': 'times',
                'icon': 'mdi:counter',
            }),
            PetkitSensorEntity('bowl_weight', self, {
                'unit': MASS_GRAMS,
                'icon': 'mdi:weight-gram',
            })
        ]

        return base_entities + entities