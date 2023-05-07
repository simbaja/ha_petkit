import datetime
import logging
from typing import List, Dict

from homeassistant.const import *
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ...api import PetkitAccount
from .base import PetkitDevice

_LOGGER = logging.getLogger(__name__)

class PetkitFeederDevice(PetkitDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        from ...entities import PetkitNumberEntity
        self._feed_now_amount_entities: List[PetkitNumberEntity] = []
        super().__init__(data, coordinator, account)

        self._feed_now_endpoint = f'{data["type"]}/saveDailyFeed'

    @property
    def desiccant(self):
        return self.status.get('desiccantLeftDays') or 0

    @property
    def food_state(self):
        return self.status.get('food', 0) == 0

    def food_state_attrs(self):
        return {
            'state': self.status.get('food'),
            'desc': 'normal' if not self.food_state else 'low',
        }

    @property
    def feed_now_amount(self):
        return self.get_feed_now_amount()

    def get_feed_now_amount(self, index=0):
        num = self._feed_now_amount_entities[index].state

        try:
            num = int(float(num))
        except (TypeError, ValueError):
            num = 10
        return num

    def feed_now_attrs(self):
        return {
            'feeding_amount': self.feed_now_amount,
            'desc': self._cache.get('desc'),
            'error': self.status.get('errorMsg')
        }

    def _get_all_entities(self) -> List[Entity]:
        #deal with circular imports by bringing in the sensors here
        from ...entities import (
            PetkitSensorEntity,
            PetkitBinarySensorEntity,
            PetkitButtonEntity
        )
        base_entities = super()._get_all_entities()

        self._init_feed_now_amount_entities()

        feeder_entities = [
            PetkitSensorEntity('desiccant', self, {'unit': 'days', 'icon': 'mdi:air-filter' }),
            PetkitBinarySensorEntity('food_state', self, {
                'icon': 'mdi:food-drumstick-outline',
                'class': 'problem',
                'state_attrs': self.food_state_attrs,
            }),
            PetkitButtonEntity('feed_now', self, {
                'icon': 'mdi:shaker',
                'state_attrs': self.feed_now_attrs,
                'async_press': self.async_feed_now,
            })
        ]

        entities = base_entities + \
            feeder_entities + \
            self._feed_now_amount_entities
        
        return entities

    def _init_feed_now_amount_entities(self):
        from ...entities import PetkitFeedAmountEntity
        self._feed_now_amount_entities.append(PetkitFeedAmountEntity('feed_now_amount', self))

    def _set_feed_now_amount_parameters(self, pms: Dict, **kwargs):
        pms.update(
            {
                'amount': kwargs.get('amount', self.feed_now_amount)
            })

    async def async_feed_now(self, **kwargs):
        pms = {
            'deviceId': self.id,
            'day': datetime.datetime.today().strftime('%Y%m%d'),
            'time': -1,
        }
        self._set_feed_now_amount_parameters(pms, **kwargs)
        rdt = await self.account.request(self._feed_now_endpoint, pms)
        eno = rdt.get('error', {}).get('code', 0)
        if eno:
            _LOGGER.error('Petkit feeding failed: %s', rdt)
            return False
            
        #await self.update_device_detail()
        await self._coordinator.async_request_refresh()
        
        _LOGGER.info('Petkit feeding now: %s', rdt)  
        return rdt