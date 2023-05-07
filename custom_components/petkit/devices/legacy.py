from typing import List

from homeassistant.const import *
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..api import PetkitAccount
from .common import PetkitFeederDevice

class LegacyFeederDevice(PetkitFeederDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        super().__init__(data, coordinator, account)
        self._feed_now_endpoint = f'{self.type}/save_DailyFeed'

    @property
    def scheduled_amount(self):
        fas = self.daily_feed_attrs()
        return fas.get('amount', 0)   

    @property
    def feed_amount(self):
        fas = self.daily_feed_attrs()
        return fas.get('realAmount', 0)           

    def daily_feed_attrs(self):
        return self._cache.get('dailyFeed') or {}

    def _get_all_entities(self) -> List[Entity]:
        #deal with circular imports by bringing in the sensors here
        from ..entities import (
            PetkitSensorEntity,
        )
        base_entities = super()._get_all_entities()

        feeder_entities = [
            PetkitSensorEntity('scheduled_amount', self, {
                    'unit': MASS_GRAMS,
                    'icon': 'mdi:weight-gram',
                    'state_attrs': self.daily_feed_attrs,
                }),
            PetkitSensorEntity('feed_amount', self, {
                    'unit': MASS_GRAMS,
                    'icon': 'mdi:weight-gram',
                    'state_attrs': self.daily_feed_attrs,
                })
        ]

        return base_entities + feeder_entities