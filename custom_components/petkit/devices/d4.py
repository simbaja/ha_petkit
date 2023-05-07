from homeassistant.const import *
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..api import PetkitAccount
from .common import PetkitFeedStateFeederDevice

class D4FeederDevice(PetkitFeedStateFeederDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        super().__init__(data, coordinator, account)    