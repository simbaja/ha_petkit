"""Adds config flow for Petkit integration."""

from asyncio.log import logger
import logging
from typing import Any, Mapping, Optional
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow, CONN_CLASS_CLOUD_POLL
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_USERNAME, CONF_PASSWORD, CONF_REGION
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .api import PetkitAccount, REGION_URI_MAPPING
from .const import (
    CONF_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    VALUES_SCAN_INTERVAL,
    VALUES_TIMEOUT
)

CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_REGION): vol.In(REGION_URI_MAPPING.keys())
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.In(VALUES_SCAN_INTERVAL),
        vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.In(VALUES_TIMEOUT)
    }
)

class PetkitConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Petkit integration."""

    VERSION = 1
    DOMAIN = DOMAIN
    CONNECTION_CLASS = CONN_CLASS_CLOUD_POLL

    def __init__(self):
        self._existing_entry = None
        self._user_input = {}
        self._description_placeholders = None
        super().__init__()

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    def _get_schema(self, step_id: str):
        if step_id == "user":
            return CREDENTIALS_SCHEMA
        else:
            return vol.Schema({vol.Required(CONF_PASSWORD): str})

    async def _test_connection(self):
        session = aiohttp_client.async_get_clientsession(self.hass)
 
        api = PetkitAccount(
            session,
            self._user_input[CONF_USERNAME],
            self._user_input[CONF_PASSWORD],
            self._user_input[CONF_REGION]
        )

        #try to get account information, if we do, we're good
        await api.async_login()
        self.logger.info("Successfully authenticated")
               
    def _show_setup_form(self, user_input=None, errors=None, step_id="user"):
        """Show the setup form to the user."""

        if user_input is None:
            user_input = {}

        return self.async_show_form(
            step_id=step_id,
            data_schema=self._get_schema(step_id),
            errors=errors or {},
            description_placeholders=self._description_placeholders,
        ) 

    async def _validate_and_create_entry(self, user_input, step_id):
        """Check if config is valid and create entry if so."""

        self._user_input[CONF_PASSWORD] = user_input[CONF_PASSWORD]
        self._user_input[CONF_REGION] = user_input[CONF_REGION]

        extra_inputs = user_input

        if self._existing_entry:
            extra_inputs = self._existing_entry
        self._user_input[CONF_USERNAME] = extra_inputs[CONF_USERNAME]

        if self.unique_id is None:
            await self.async_set_unique_id(self._user_input[CONF_USERNAME])
            self._abort_if_unique_id_configured()

        try:
            #test the connection and set the token
            await self._test_connection()                         
        except Exception as ex:
            logger.exception(ex)
            return self.async_show_form(
                step_id=step_id,
                data_schema=self._get_schema(step_id),
                errors={"base": "invalid_auth"}
            )

        if step_id == "user":
            #if we didn't have an entry, create one
            return self.async_create_entry(
                title=self._user_input[CONF_USERNAME],
                data=self._user_input
            )   

        #if we have an entry, assume that we want to update it (treat as re-auth)
        entry = await self.async_set_unique_id(self.unique_id)
        self.hass.config_entries.async_update_entry(entry, data=self._user_input)
        await self.hass.config_entries.async_reload(entry.entry_id)
        return self.async_abort(reason="reauth_successful")
       
    async def async_step_user(self, user_input=None):
        """ Handle a flow initiated by a user """
        errors = {}

        if user_input is None:
            return self._show_setup_form(user_input, errors)

        return await self._validate_and_create_entry(user_input, "user")

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Handle configuration by re-auth."""
        await self.async_set_unique_id(entry_data[CONF_USERNAME])
        self._existing_entry = {**entry_data}
        self._description_placeholders = {CONF_USERNAME: entry_data[CONF_USERNAME]}
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: Optional[dict[str, str]] = None
    ) -> FlowResult:
        """Handle re-auth completion."""
        if user_input is None:
            return self._show_setup_form(step_id="reauth_confirm")

        return await self._validate_and_create_entry(user_input, "reauth_confirm")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Define the config flow to handle options."""
        return PetkitOptionsFlowHandler(config_entry) 

class PetkitOptionsFlowHandler(OptionsFlow):
    """Handle an Petkit options flow."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry

    async def async_step_init(
        self, user_input: Optional[dict[str, str]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=OPTIONS_SCHEMA
        )