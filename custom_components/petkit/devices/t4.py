import datetime
from typing import List, Dict
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..api import PetkitAccount
from .common import PetkitLitterDevice

class T4LitterDevice(PetkitLitterDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        super().__init__(data, coordinator, account) 

    def _set_device_detail_parameters(self, pms: Dict):
        pms.update(
            {
               'date': datetime.datetime.today().strftime('%Y%m%d')
            })      