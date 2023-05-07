"""Data update coordinator for Petkit devices"""

import asyncio
import async_timeout
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_REGION,
    CONF_SCAN_INTERVAL, 
    CONF_TIMEOUT
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    PetkitAccount, 
    PetkitError, 
    PetkitAuthFailedError, 
    PetkitServerError
)

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN
)
from .devices import PetkitDevice, get_device_type

PLATFORMS = ["sensor","switch","select","button","binary_sensor","number"]
_LOGGER = logging.getLogger(__name__)

class PetkitUpdateCoordinator(DataUpdateCoordinator):
    """Define a wrapper class to update Petkit API data."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Set up the PetkitUpdateCoordinator class."""
        self._hass = hass
        self._config_entry = config_entry 
        
        self._username = config_entry.data[CONF_USERNAME]
        self._password = config_entry.data[CONF_PASSWORD]
        self._region = config_entry.data[CONF_REGION]
        self._api = self._get_api_from_config(hass, config_entry)

        options = config_entry.options
        self._update_interval = options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self._timeout = options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        self._initialized = False
        self.devices: dict[str, PetkitDevice] = {}

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=self._update_interval))

    async def async_setup(self):
        """Setup a new coordinator"""
        _LOGGER.debug("Setting up coordinator")

        _LOGGER.debug("Getting first refresh")
        await self.async_config_entry_first_refresh()
        self._initialized = True

        _LOGGER.debug("Forwarding setup to platforms")
        for component in PLATFORMS:
            self.hass.async_create_task(
                self.hass.config_entries.async_forward_entry_setup(
                    self._config_entry, component
                )
            )

        return True

    async def async_reset(self):
        """Resets the coordinator."""
        _LOGGER.debug("resetting the coordinator")
        entry = self._config_entry
        unload_ok = all(
            await asyncio.gather(
                *[
                    self.hass.config_entries.async_forward_entry_unload(
                        entry, component
                    )
                    for component in PLATFORMS
                ]
            )
        )
        return unload_ok

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            data = {}

            #get the list of known appliances
            existing_devices: list[str] = self.devices.keys()
            
            async with async_timeout.timeout(self._timeout):
                data = { 
                    d["id"]: d
                    for x in await self._api.get_devices()
                    for d in x["data"] or {}
                    if d["id"] 
                }

            #build the device list if needed
            if not self._initialized:
                await self._build_devices(data)
            else:
                #detect new devices and notify the user
                await self._detect_new_devices(existing_devices, data)

                #get additional detail per device
                for dvc in self.devices.values():
                    await dvc.update_device_detail()

            return data
        except (PetkitAuthFailedError) as ex:
            raise ConfigEntryAuthFailed from ex            
        except PetkitError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def _build_devices(self, data: dict[str,Any]):
        for id in data.keys():
            _LOGGER.info(f"Found Petkit device with id={id}, setting up...")
            device_type = get_device_type(data["type"].lower())
            self.devices[id] = device_type(data, self, self._api)

    async def _detect_new_devices(self, old: list[str], new: dict[str,Any]):
        diff = set(new)-set(old)
        for id in diff:
            _LOGGER.info(
                f"New device with id={id} detected, reload the Petkit integration if you want to access it in Home Assistant"
            )

    def _get_api_from_config(self, hass: HomeAssistant, config_entry: ConfigEntry):
        return PetkitAccount(
            aiohttp_client.async_get_clientsession(self.hass),
            config_entry[CONF_USERNAME],
            config_entry[CONF_PASSWORD],
            config_entry[CONF_REGION]
        )

