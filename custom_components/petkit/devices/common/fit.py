import datetime
import logging
from typing import List

from homeassistant.const import *
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ...api import PetkitAccount
from .base import PetkitDevice

_LOGGER = logging.getLogger(__name__)

class PetkitFitDevice(PetkitDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        super().__init__(data, coordinator, account)

    @property
    def state(self):
        return self._cache.get('syncTime')

    def state_attrs(self):
        return {
            **self._cache,
            'data24': self._detail.get('data24', []),
        }

    @property
    def activity(self):
        return self.activity_attrs().get('total')

    def activity_attrs(self):
        return self._detail.get('activityRecord') or {}

    @property
    def calorie(self):
        return self.calorie_attrs().get('total')

    def calorie_attrs(self):
        return self._detail.get('calorieRecord') or {}

    @property
    def sleep(self):
        return self.sleep_attrs().get('total')

    def sleep_attrs(self):
        return self._detail.get('sleepDetail') or {}

    def _get_all_entities(self) -> List[Entity]:
        from ...entities import PetkitSensorEntity
        base_entities = super()._get_all_entities()

        fit_entities = [
            PetkitSensorEntity('activity', self, {
                'icon': 'mdi:run',
                'state_attrs': self.activity_attrs,
            }),
            PetkitSensorEntity('calorie', self, {
                'icon': 'mdi:arm-flex',
                'state_attrs': self.calorie_attrs,
            }),
            PetkitSensorEntity('sleep', self, {
                'icon': 'mdi:sleep',
                'state_attrs': self.sleep_attrs,
            })
        ]

        return base_entities + fit_entities

    async def update_device_detail(self):
        api = f'{self.type}/deviceAllData'
        pms = {
            'deviceId': self.id,
            'day': datetime.datetime.today().strftime('%Y%m%d'),
        }
        rsp = None
        try:
            rsp = await self.account.request(api, pms)
            rdt = rsp.get('result') or {}
        except (TypeError, ValueError):
            rdt = {}
        if not rdt:
            _LOGGER.warning('Got petkit device detail for %s failed: %s', self.name, rsp)
        self._detail = rdt
        return rdt