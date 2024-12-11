from __future__ import absolute_import, print_function
import json
import time
from .utils import get_client_user_agent

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

class UltraAuthError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
  
    def __str__(self):
        return str(self.message)

class UltraConnection:
    def __init__(self, host='api.ultradns.com'):
        self.host = host
        self.access_token = None
        self.refresh_token = None

    def _get_connection(self):
        if self.host.startswith('https://'):
            return self.host
        else:
            return f'https://{self.host}'

    def _authenticate(self, **kwargs):
        if not HAS_REQUESTS:
            raise Exception('requests library is required for this module')

        url = f'{self._get_connection()}/v1/authorization/token'
        headers = {
            'User-Agent': get_client_user_agent(),
        }

        if 'username' in kwargs and 'password' in kwargs:
            payload = {
              'grant_type': 'password',
              'username': kwargs['username'],
              'password': kwargs['password']
            }
        elif 'refresh_token' in kwargs:
            payload = {
              'grant_type': 'refresh_token',
              'refresh_token': kwargs['refresh_token']
            }
        else:
            raise UltraAuthError('Missing authentication credentials')

        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == requests.codes.OK:
            response_data = response.json()
            self.access_token = response_data['access_token']
            self.refresh_token = response_data['refresh_token']
        else:
            raise UltraAuthError(f'Failed to authenticate: {response.text}')

    def auth(self, username: str, password: str):
        self._authenticate(username=username, password=password)

    def _refresh(self):
        self._authenticate(refresh_token=self.refresh_token)

    def _headers(self, content_type='application/json'):
        headers = {
            'User-Agent': get_client_user_agent(),
            'Accept': 'application/json',
            'Authorization  ': f'Bearer {self.access_token}'
        }
        if content_type:
            headers['Content-Type'] = content_type
        return headers

    def get(self, uri, params=None):
        params = params or {}
        return self._do_call("GET", uri, params=params)

    def post(self, uri, body=None):
        return self._do_call("POST", uri, body=json.dumps(body)) if body is not None else self._do_call("POST", uri)

    def put(self, uri, body):
        return self._do_call("PUT", uri, body=json.dumps(body))

    def patch(self, uri, body):
        return self._do_call("PATCH", uri, body=json.dumps(body))

    def delete(self, uri):
        return self._do_call("DELETE", uri)

    def _do_call(self, method, path, **kwargs):
        retry = False
        url = f'{self._get_connection()}/{path}'
        params = kwargs['params'] if 'params' in kwargs else None
        data = kwargs['body'] if 'body' in kwargs else None
        response = requests.request(method, url,
                                headers=self._headers(),
                                params=params,
                                data=data)

        if response.status_code == requests.codes.UNAUTHORIZED:
            retry = True
            self._refresh()

        if response.status_code == requests.codes.TOO_MANY:
            retry = True
            time.sleep(1)

        if retry:
            response = requests.request(method, url,
                                  headers=self._headers(),
                                  params=params,
                                  data=data)

        if response.status_code == requests.codes.NO_CONTENT:
            return {}
        if 'content-type' not in response.headers:
            response.headers['content-type'] = 'none'

        # if the content-type is text/plain just return the text
        if response.headers.get('content-type') == 'text/plain':
            return response.text

        try:
            payload = response.json()
            if isinstance(payload, list) and 'errorCode' in payload[0]:
                return {'errorCode': payload[0]['errorCode'],
                  'errorMessage': payload[0]['errorMessage'],
                  'statusCode': response.status_code}
        except requests.exceptions.JSONDecodeError:
            payload = {}

        return payload
