import logging
from typing import List

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ...api import PetkitAccount

_LOGGER = logging.getLogger(__name__)

class PetkitDevice:
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        self._coordinator = coordinator
        self._account = account
        self._id = data['id']
        self.listeners = {}
        self._detail = {}
        self._entities = {}
        self._build_entities_list()        

    @property
    def device_id(self):
        return self._id

    @property
    def device_type(self):
        return self._cache.get('type', '').lower()

    @property
    def device_name(self):
        return self._cache.get('name', '')

    @property
    def device_firmware(self):
        return self._cache.get('firmware', '')

    @property
    def status(self):
        return self._cache.get('status') or {}

    @property
    def state(self):
        sta = self._cache.get('state') or 0
        dic = {
            '1': 'online',
            '2': 'offline',
            '3': 'feeding',
            '4': 'mate_ota',
            '5': 'device_error',
            '6': 'battery_mode',
        }
        return dic.get(f'{sta}'.strip(), sta)

    def state_attrs(self):
        return {
            'state': self._cache.get('state'),
            'desc':  self._cache.get('desc'),
            'status': self.status,
            'shared': self._cache.get('deviceShared'),
        }        

    @property
    def battery(self):
        return self._cache.get('battery')

    @property
    def coordinator(self):
        return self._coordinator
    
    @property
    def account(self):
        return self._account

    @property
    def entities(self) -> list[Entity]:
        return list(self._entities.values())

    @property
    def _cache(self) -> dict:
        return self._coordinator.data.get(self.device_id)

    def _build_entities_list(self) -> dict[str, Entity]:
        """Build the entities list, adding anything new."""
        from ...entities import PetkitEntity
        entities = [
            e for e in self._get_all_entities()
            if isinstance(e, PetkitEntity)
        ]

        for entity in entities:
            if entity.unique_id not in self._entities:
                self._entities[entity.unique_id] = entity            

    def _get_all_entities(self) -> List[Entity]:
        #deal with circular imports by bringing in the sensors here
        from ...entities import (
            PetkitSensorEntity
        )
        entities = [
            PetkitSensorEntity('state', self, { 'icon': 'mdi:information', 'state_attrs': self.state_attrs })
        ]
        if 'battery' in self._cache:
            entities.extend([
                  PetkitSensorEntity('battery', self, { 'class': 'battery' })
            ])

        return entities

    async def update_device_detail(self):
        api = f'{self.device_type}/device_detail'
        pms = {
            'id': self.device_id,
        }
        rsp = None
        try:
            rsp = await self._account.request(api, pms)
            rdt = rsp.get('result') or {}
        except (TypeError, ValueError) as exc:
            rdt = {}
            _LOGGER.error('Got petkit device detail for %s failed: %s', self.device_name, exc)
        if not rdt:
            _LOGGER.warning('Got petkit device detail for %s failed: %s', self.device_name, rsp)
        self._detail = rdt
        return rdt