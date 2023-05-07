from typing import Dict

from homeassistant.const import *
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..api import PetkitAccount
from ..entities import PetkitFeedAmountEntity
from .common import PetkitFeedStateFeederDevice

class D4sFeederDevice(PetkitFeedStateFeederDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        super().__init__(data, coordinator, account)

    @property
    def feed_amount(self):
        fas = self.feed_state_attrs()
        return fas.get('realAmountTotal1', 0) + fas.get('realAmountTotal2', 0)

    @property
    def feed_now_amount(self):
        return self.get_feed_now_amount(0) + self.get_feed_now_amount(1)

    def feed_now_attrs(self):
        return {
            'feeding_amount1': self.get_feed_now_amount(0),
            'feeding_amount2': self.get_feed_now_amount(1),
            'desc': self.data.get('desc'),
            'error': self.status.get('errorMsg'),
            **self.feed_state_attrs(),
        }

    def _init_feed_now_amount_entities(self):
        self._feed_now_amount_entities.append(PetkitFeedAmountEntity('feed_now_amount1', self))
        self._feed_now_amount_entities.append(PetkitFeedAmountEntity('feed_now_amount2', self))

    def _set_feed_now_amount_parameters(self, pms: Dict, **kwargs):
        pms.update({
            'amount1': kwargs.get('amount1', self.get_feed_now_amount(0)),
            'amount2': kwargs.get('amount2', self.get_feed_now_amount(1)),
        })