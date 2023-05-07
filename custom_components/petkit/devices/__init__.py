import logging
from typing import Type

from .common import PetkitDevice
from .feeder import FeederFeederDevice
from .d3 import D3FeederDevice
from .d4 import D4FeederDevice
from .d4s import D4sFeederDevice
from .w5 import W5WaterDevice
from .p3 import P3FitDevice
from .t3 import T3LitterDevice
from .t4 import T4LitterDevice

_LOGGER = logging.getLogger(__name__)

def get_device_type(device_type: str) -> Type:
    """Get the appropriate device type"""
    _LOGGER.debug(f"Found device type: {device_type}")

    return {
        'feeder': FeederFeederDevice,
        'feedermini': FeederFeederDevice,
        'd3': D3FeederDevice,
        'd4': D4FeederDevice,
        'd4s': D4sFeederDevice,
        'w5': W5WaterDevice,
        'p3': P3FitDevice,
        't3': T3LitterDevice,
        't4': T4LitterDevice
    }.get(device_type.lower(), PetkitDevice)
