import aiohttp
import logging
import hashlib

from asyncio import TimeoutError
from aiohttp import ClientConnectorError, ContentTypeError

from .const import DEFAULT_API_BASE, REGION_URI_MAPPING
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

    def get_full_uri(self, endpoint=''):
        if endpoint[:6] == 'https:' or endpoint[:5] == 'http:':
            return endpoint

        base_url = self._api_base_url or DEFAULT_API_BASE
        return f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    async def request(self, api: str, pms:None, method='GET', **kwargs):
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

    async def _request(self, api: str, pms=None, method='GET', **kwargs):
        method = method.upper()
        url = self.get_full_uri(api)

        kws = {
            'timeout': 30,
            'headers': {
                'User-Agent': 'okhttp/3.12.1',
                'X-Api-Version': '7.29.1',
                'X-Client': 'Android(7.1.1;Xiaomi)',
                'X-Session': f'{self.token}',
            },
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

    async def async_login(self):
        pms = {
            'encrypt': 1,
            'username': self._username,
            'password': self._password_md5,
            'oldVersion': '',
        }

        rsp = await self.request(f'user/login', pms, 'POST_GET')
        ssn = rsp.get('result', {}).get('session') or {}
        sid = ssn.get('id')

        if not sid:
            raise PetkitAuthFailedError(f'Petkit login {self._username} failed: {rsp}')

        self._token = sid
        self._user_id = ssn.get('userId')

    async def get_devices(self):
        api = 'discovery/device_roster'
        rsp = await self.request(api)

        self._cache = rsp.get('result', {}).get('devices') or []
        if not self._cache:
            _LOGGER.warning(f'Could not retrieve Petkit device information: {self.username}, response={rsp}')

        return self._cache
