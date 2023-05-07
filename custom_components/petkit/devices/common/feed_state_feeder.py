import logging
from typing import List

from homeassistant.const import *
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ...api import PetkitAccount
from .feeder import PetkitFeederDevice

_LOGGER = logging.getLogger(__name__)

class PetkitFeedStateFeederDevice(PetkitFeederDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        super().__init__(data, coordinator, account)    

    @property
    def feed_times(self):
        return self.feed_state_attrs().get('times', 0)

    @property
    def feed_amount(self):
        fas = self.feed_state_attrs()
        return fas.get('realAmountTotal', 0)   

    def feed_state_attrs(self):
        return self._detail.get('state', {}).get('feedState') or {}

    def _get_all_entities(self) -> List[Entity]:
        #deal with circular imports by bringing in the sensors here
        from ...entities import (
            PetkitSensorEntity,
        )
        base_entities = super()._get_all_entities()

        feeder_entities = [
            PetkitSensorEntity('feed_times', self, {
                    'unit': 'times',
                    'icon': 'mdi:counter',
                    'state_attrs': self.feed_state_attrs,
                }),
            PetkitSensorEntity('feed_amount', self, {
                    'unit': MASS_GRAMS,
                    'icon': 'mdi:weight-gram',
                    'state_attrs': self.feed_state_attrs,
                })
        ]

        return base_entities + feeder_entities