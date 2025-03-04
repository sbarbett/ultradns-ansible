from __future__ import absolute_import, division, print_function
__metaclass__ = type
import json

VERSION = "1.0.0"
PREFIX = "udns-ansible-"


# Define mock classes first, outside the try block
class MockAuthError(Exception):
    """Mock AuthError for when ultra_rest_client is not available"""
    pass


class MockRestApiConnection:
    """Mock RestApiConnection for when ultra_rest_client is not available"""
    def __init__(self, host=None, custom_headers=None):
        self.host = host
        self.custom_headers = custom_headers or {}

    def auth(self, username, password):
        pass

    def get(self, uri, params=None):
        return {}

    def post(self, uri, body=None):
        return {}

    def put(self, uri, body):
        return {}

    def patch(self, uri, body):
        return {}

    def delete(self, uri):
        return {}


# Set default implementations
RestApiConnection = MockRestApiConnection
UltraAuthError = MockAuthError
HAS_SDK = False

# Try to import the real implementations
try:
    from ultra_rest_client import RestApiConnection, AuthError as UltraAuthError
    HAS_SDK = True
except ImportError:
    # Keep using the mock classes defined above
    pass


class UltraConnection(RestApiConnection):
    def __init__(self, host='api.ultradns.com'):
        custom_headers = {'User-Agent': f'{PREFIX}{VERSION}'}
        super().__init__(host=host, custom_headers=custom_headers)

    def _authenticate(self, **kwargs):
        if not HAS_SDK:
            raise Exception('ultra_rest_client library is required for this module')

        if 'username' in kwargs and 'password' in kwargs:
            self.auth(kwargs['username'], kwargs['password'])
        elif 'refresh_token' in kwargs:
            self._refresh()
        else:
            raise UltraAuthError('Missing authentication credentials')

    def get(self, uri, params=None):
        result = super().get(uri, params)
        return self._ensure_response_format(result)

    def post(self, uri, body=None):
        if body is not None:
            body = json.dumps(body) if isinstance(body, (dict, list)) else body
        result = super().post(uri, body)
        return self._ensure_response_format(result)

    def put(self, uri, body):
        body = json.dumps(body) if isinstance(body, (dict, list)) else body
        result = super().put(uri, body)
        return self._ensure_response_format(result)

    def patch(self, uri, body):
        body = json.dumps(body) if isinstance(body, (dict, list)) else body
        result = super().patch(uri, body)
        return self._ensure_response_format(result)

    def delete(self, uri):
        result = super().delete(uri)
        return self._ensure_response_format(result)

    def _ensure_response_format(self, result):
        # Ensure result is a dict
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                return result

        # Handle list responses
        if isinstance(result, list):
            if result and isinstance(result[0], dict) and 'errorCode' in result[0]:
                return {
                    'errorCode': result[0]['errorCode'],
                    'errorMessage': result[0].get('errorMessage', ''),
                    'statusCode': 400
                }
            return {'rrSets': result} if result and isinstance(result[0], dict) and 'rdata' in result[0] else result

        # Handle dict responses
        if isinstance(result, dict):
            if 'errorCode' in result:
                return {
                    'errorCode': result['errorCode'],
                    'errorMessage': result.get('errorMessage', ''),
                    'statusCode': result.get('statusCode', 400)
                }

        return result
