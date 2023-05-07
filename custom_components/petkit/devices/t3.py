from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from ..api import PetkitAccount
from .common import PetkitLitterDevice

class T3LitterDevice(PetkitLitterDevice):
    def __init__(self, data: dict, coordinator: DataUpdateCoordinator, account: PetkitAccount):
        super().__init__(data, coordinator, account) 
