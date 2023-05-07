import aiohttp
from datetime import datetime, timedelta
import logging
import hashlib

from asyncio import TimeoutError
from aiohttp import ClientConnectorError, ContentTypeError

from .const import (
    DEFAULT_API_BASE, 
    DEVICE_ROSTER_ENDPOINT, 
    LOGIN_ENDPOINT, 
    PETKIT_API_VERSION, 
    REGION_URI_MAPPING
)
from .exceptions import *

_LOGGER = logging.getLogger(__name__)

class PetkitAccount:
    def __init__(self, session: aiohttp.ClientSession, username: str, password: str, region: str):
        self._username = username
        self._password = password
        self._password_md5 = hashlib.md5(f'{password}'.encode()).hexdigest()
        self._region = region
        self._session = session
        self._api_base_url = REGION_URI_MAPPING.get(region,DEFAULT_API_BASE)

        self._user_id = None
        self._token = None
        self._expiration_date = datetime.utcnow
        self._cache = []

    @property
    def user_id(self):
        return self._user_id

    @property
    def token(self):
        return self._token

    @property
    def device_data_cache(self):
        return self._cache

    @property
    def is_authorized(self):
        return self._expiration_date > datetime.utcnow()

    def _get_full_uri(self, endpoint=''):
        if endpoint[:6] == 'https:' or endpoint[:5] == 'http:':
            return endpoint

        base_url = self._api_base_url or DEFAULT_API_BASE
        return f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    async def request(self, api: str, pms:None, method='GET', **kwargs):
        await self._ensure_token()
        rsp = self._request(api, pms, method, kwargs)

        #try again if the request failed due to an auth issue
        eno = rsp.get('error', {}).get('code', 0)
        if eno in [5, 8]:
            try:
                await self.async_login()
                rsp = await self._request(api)
            except PetkitAuthFailedError as exc:
                _LOGGER.error('Request failed due to authentication error.', exc_info=exc)
                raise

        return rsp

    async def _ensure_token(self) -> None:
        cdt = datetime.now()
        if (self._token or self._expiration_date) is None:
            await self.async_login()
        elif (self.token_expiration-cdt).total_seconds() < 3600:
            await self.async_login()
        else:
            return None

    async def _request(self, api: str, pms=None, method='GET', **kwargs):
        method = method.upper()
        url = self._get_full_uri(api)

        kws = {
            'timeout': 30,
            'headers': self._get_custom_headers(),
        }

        kws.update(kwargs)
        
        if method in ['GET']:
            kws['params'] = pms
        elif method in ['POST_GET']:
            method = 'POST'
            kws['params'] = pms
        else:
            kws['data'] = pms
            kws['headers']['Content-Type'] = 'application/x-www-form-urlencoded'
        req = None

        try:
            req = await self.http.request(method, url, **kws)
            return await req.json() or {}
        except (ClientConnectorError, ContentTypeError, TimeoutError) as exc:
            lgs = [method, url, pms, exc]
            if req:
                lgs.extend([req.status, req.content])
            _LOGGER.error('Request Petkit api failed: %s', lgs)
        return {}

    def _get_custom_headers(self):
        #should be able to set the local and tz, but for now
        #that isn't implemented
        locale = 'en-US' if self._region == "US" else 'zh-CN'

        return {
                'User-Agent': 'okhttp/3.12.1',
                'X-Api-Version': PETKIT_API_VERSION,
                'X-Client': 'Android(7.1.1;Xiaomi)',
                'X-Locale': locale.replace("-", "_"),
                'X-Session': f'{self.token}',
            }

    async def async_login(self):
        pms = {
            'encrypt': 1,
            'username': self._username,
            'password': self._password_md5,
            'oldVersion': '',
        }

        try:
            response = await self.request(LOGIN_ENDPOINT, pms, 'POST_GET')
            session = response.get('result', {}).get('session') or {}
           
            createdAt = datetime.strptime(
                session["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            self._token = session["id"]
            self._expiration_date = createdAt + timedelta(
                seconds=session["expiresIn"]
            )
            self._user_id = session["userId"]

            _LOGGER.debug(
                "Obtained access token {} and expiration datetime {}".format(
                    self._token, self._expiration_date
                )
            )        
        except Exception as err:
            raise PetkitAuthFailedError(f'Petkit login {self._username} failed: {response}')

    async def get_devices(self):
        api = DEVICE_ROSTER_ENDPOINT
        rsp = await self.request(api)

        self._cache = rsp.get('result', {}).get('devices') or []
        if not self._cache:
            _LOGGER.warning(f'Could not retrieve Petkit device information: {self.username}, response={rsp}')

        return self._cache
