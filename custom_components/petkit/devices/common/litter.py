import copy
import datetime
import logging
from typing import List, Dict

from homeassistant.const import *
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ...api import PetkitAccount

from ...entities import (
    PetkitSensorEntity,
    PetkitBinarySensorEntity,
    PetkitSwitchEntity,
    PetkitButtonEntity,
    PetkitSelectEntity
)
from .base import PetkitDevice

_LOGGER = logging.getLogger(__name__)

class PetkitLitterDevice(PetkitDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        super().__init__(data, coordinator, account)

    @property
    def power(self):
        return not not self.status.get('power')

    @property
    def box_full(self):
        return self.status.get('boxFull')

    @property
    def sand_percent(self):
        return self.status.get('sandPercent')

    def sand_attrs(self):
        return {
            'sand_lack': self.status.get('sandLack'),
            'sand_weight': self.status.get('sandWeight'),
        }

    @property
    def liquid(self):
        return self.status.get('liquid')

    def liquid_attrs(self):
        return {
            'liquid': self.status.get('liquid'),
            'liquid_empty': self.status.get('liquidEmpty'),
            'liquid_lack': self.status.get('liquidLack'),
        }

    @property
    def work_mode(self):
        return self.status.get('workState', {}).get('workMode', -1)

    @property
    def action(self):
        return {
            0: 'cleanup',
            2: 'deodorize',
            9: 'maintain',
        }.get(self.work_mode, None)

    @property
    def in_times(self):
        return self.detail.get('inTimes')

    @property
    def pet_weight(self):
        evt = self.pet_weight_attrs()
        return evt.get('petWeight')

    def pet_weight_attrs(self):
        return self.last_record_attrs(only_event=10)

    @property
    def records(self):
        return self.detail.get('records') or []

    @property
    def last_record(self):
        evt = self.last_record_attrs().get('eventType') or 0
        dic = {
            5: 'cleaned',
            6: 'dumped',
            7: 'reset',
            8: 'deodorized',
            10: 'occupied',
        }
        return dic.get(evt, evt)

    def last_record_attrs(self, only_event=None):
        rls = copy.deepcopy(self.records)
        if not rls:
            return {}
        lst = rls[-1] or {}
        if only_event:
            rls.reverse()
            for v in rls:
                if only_event == v.get('eventType') and v.get('content'):
                    lst = v
                    break
        ctx = lst.pop('content', None) or {}
        return {**lst, **ctx}

    @property
    def manual_lock(self):
        return True if self.detail.get('settings', {}).get('manualLock') else False

    def _get_all_entities(self) -> List[Entity]:
        base_entities = super()._get_all_entities()

        litter_entities = [         
            PetkitSensorEntity('sand_percent', self, {
                'icon': 'mdi:percent-outline',
                'state_attrs': self.sand_attrs,
                'unit': PERCENTAGE,
            }),
            PetkitSensorEntity('liquid', self, {
                'icon': 'mdi:water-percent',
                'state_attrs': self.liquid_attrs,
                'unit': PERCENTAGE,
            }),
            PetkitSensorEntity('sand_percent', self, {
                'icon': 'mdi:percent-outline',
                'state_attrs': self.sand_attrs,
                'unit': PERCENTAGE,
            }),            
            PetkitSensorEntity('pet_weight', self, {
                'icon': 'mdi:weight',
                'state_attrs': self.pet_weight_attrs,
                'unit': MASS_GRAMS,
            }), 
            PetkitSensorEntity('in_times', self, {
                'icon': 'mdi:location-enter',
                'unit': 'times',
            }),
            PetkitSensorEntity('last_record', self, {
                'icon': 'mdi:history',
                'state_attrs': self.last_record_attrs,
            }),
            PetkitBinarySensorEntity('box_full', self, {
                'icon': 'mdi:tray-full',
                'class': 'problem',
            }),
            PetkitButtonEntity('cleanup', self, {
                'icon': 'mdi:broom',
                'async_press': self.async_press_cleanup
            }),
            PetkitButtonEntity('deodorize', self, {
                'icon': 'mdi:broom',
                'async_press': self.async_press_deodorize
            }),
            PetkitSwitchEntity('power', self, {
                'icon': 'mdi:power',
                'async_turn_on': self.async_turn_on,
                'async_turn_off': self.async_turn_off,
            }),
            PetkitSwitchEntity('manual_lock', self, {
                'icon': 'mdi:lock',
                'async_turn_on': self.async_manual_lock_on,
                'async_turn_off': self.async_manual_lock_off,
            }),
            PetkitSelectEntity('action', self, {
                'icon': 'mdi:play-box',
                'options': list(self._actions.keys()),
                'async_select': self.async_select_action,
                'delay_update': 5,
            })
        ]

        entities = base_entities + litter_entities
        
        return entities

    def _set_device_detail_parameters(self, pms: Dict):
        pass

    async def update_device_detail(self):
        await super().update_device_detail()

        api = f'{self.device_type}/getDeviceRecord'
        pms = {
            'deviceId': self.device_id,
        }
        self._set_device_detail_parameters(pms)

        rsp = None
        try:
            rsp = await self.account.request(api, pms)
            rdt = rsp.get('result') or {}
        except (TypeError, ValueError):
            rdt = {}
        if not rdt:
            _LOGGER.warning('Got petkit device records for %s failed: %s', self.device_name, rsp)
        self.detail['records'] = rdt
        return rdt

    async def async_turn_on(self, **kwargs):
        return await self.async_set_power(True)

    async def async_turn_off(self, **kwargs):
        return await self.async_set_power(False)

    async def async_set_power(self, on=True):
        val = 1 if on else 0
        dat = '{"power_action":%s}' % val
        return await self.async_control_device(type='power', kv=dat)

    async def async_press_cleanup(self, **kwargs):
        return await self.async_select_action('cleanup')

    async def async_press_deodorize(self, **kwargs):
        return await self.async_select_action('deodorize')

    @property
    def _actions(self):
        return {
            'cleanup':   ['start', 0],
            'pause':     ['stop', self.work_mode],
            'end':       ['end', self.work_mode],
            'continue':  ['continue', self.work_mode],
            'deodorize': ['start', 2],
            'maintain':  ['start', 9],
        }

    async def async_select_action(self, action, **kwargs):
        act, val = self._actions.get(action, [None, 0])
        if not act:
            return False
        dat = '{"%s_action":%s}' % (act, val)
        return await self.async_control_device(type=act, kv=dat)

    async def async_manual_lock_on(self, **kwargs):
        return await self.async_set_manual_lock(True)

    async def async_manual_lock_off(self, **kwargs):
        return await self.async_set_manual_lock(False)

    async def async_set_manual_lock(self, on=True):
        val = 1 if on else 0
        dat = '{"manualLock":%s}' % val
        return await self.async_control_device(kv=dat, api='updateSettings')

    async def async_control_device(self, api='controlDevice', **kwargs):
        typ = self.device_type
        api = f'{typ}/{api}'
        pms = {
            'id': self.device_id,
            **kwargs,
        }
        rdt = await self.account.request(api, pms)
        eno = rdt.get('error', {}).get('code', 0)
        if eno:
            _LOGGER.error('Petkit device control failed: %s', [pms, rdt])
            return False

        #await self.update_device_detail()
        await self._coordinator.async_request_refresh()
        
        _LOGGER.info('Petkit device control: %s', [pms, rdt])
        return rdt
