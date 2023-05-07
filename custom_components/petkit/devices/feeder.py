from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..api import PetkitAccount
from .common import PetkitFeederDevice

class FeederFeederDevice(PetkitFeederDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        super().__init__(data, coordinator, account)
        self._feed_now_endpoint = f'{self.device_type}/save_DailyFeed'
