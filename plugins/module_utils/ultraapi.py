from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.basic import env_fallback
from .connection import UltraConnection

PROD = 'api.ultradns.com'
TEST = 'test-api.ultradns.com'
CONNECTION_SPEC = {
    'use_test': dict(required=False, type='bool', default=False),
    'username': dict(required=False, type='str', fallback=(env_fallback, ['ULTRADNS_USERNAME'])),
    'password': dict(required=False, type='str', fallback=(env_fallback, ['ULTRADNS_PASSWORD']), no_log=True),
}


def ultra_connection_spec():
    return {'provider': dict(required=False, type='dict', options=CONNECTION_SPEC)}


class UltraDNSModule:
    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.connection = None

    def connect(self):
        if self.connection:
            return True, 'connected'

        connspec = self.params['provider']
        if not connspec['username'] or not connspec['password']:
            return False, 'Missing UltraDNS API credentials'

        passwd = connspec['password']
        if passwd == '********':
            try:
                passwd = env_fallback('ULTRADNS_PASSWORD')
            except Exception:
                passwd = ''

        self.connection = UltraConnection(host=TEST if connspec['use_test'] else PROD)
        try:
            self.connection.auth(username=connspec['username'], password=passwd)
        except Exception as exc:
            return (False, str(exc))

        return True, 'connected'

    def _check_params(self, required,):
        conn = ['username', 'password']
        missing = list(k for k in required if k not in self.params or not self.params[k])

        if 'provider' not in self.params or not isinstance(self.params['provider'], dict):
            try:
                use_test = True if env_fallback('ULTRADNS_USE_TEST') else False
            except Exception:
                use_test = False
            self.params.update({
                'provider': {'use_test': use_test,
                             'username': env_fallback('ULTRADNS_USERNAME'),
                             'password': '********'}})
        else:
            d = self.params['provider']
            missing += list(f'provider.{k}' for k in conn if k not in d or not d[k])

        return missing

    def create_zone(self, data):
        result = self.connection.post('/zones', data)
        if 'errorCode' in result:
            return False, True, result['errorMessage']
        else:
            return True, False, 'Success'

    def update_zone(self, name, data):
        result = self.connection.put(f'/zones/{name}', data)
        if 'errorCode' in result:
            return False, True, result['errorMessage']
        else:
            return True, False, 'Success'

    def delete_zone(self, zone_name):
        result = self.connection.delete(f'/zones/{zone_name}')
        # 8001 is insufficient permissions any other error indicates the zone doesn't exist
        if 'errorCode' in result:
            if result['errorCode'] == 8001:
                return False, True, result['errorMessage']
            else:
                return False, False, result['errorMessage']
        else:
            return True, False, 'Success'

    def create_record(self, zone, owner, rtype, data):
        result = self.connection.post(f'/zones/{zone}/rrsets/{rtype}/{owner}', data)
        if 'errorCode' in result:
            return False, True, result['errorMessage']
        else:
            return True, False, 'Success'

    def update_record(self, zone, owner, rtype, data):
        result = self.connection.put(f'/zones/{zone}/rrsets/{rtype}/{owner}', data)
        if 'errorCode' in result:
            return False, True, result['errorMessage']
        else:
            return True, False, 'Success'

    def delete_record(self, zone, owner, rtype):
        result = self.connection.delete(f'/zones/{zone}/rrsets/{rtype}/{owner}')
        if 'errorCode' in result:
            if result['errorCode'] == 8001:
                return False, True, result['errorMessage']
            else:
                return False, False, result['errorMessage']
        else:
            return True, False, 'Success'

    def primary_zone(self):
        res = {'changed': False, 'failed': False, 'msg': ''}

        # check for required fields
        required = ['name', 'account', 'state']
        missing = self._check_params(required)

        if missing:
            res['failed'] = True
            res['msg'] = f"Missing required fields: {', '.join(missing)}"
            return res

        # connect to the API
        connected, msg = self.connect()
        if not connected:
            res['failed'] = True
            res['msg'] = msg
            return res

        if self.params['state'] == 'present':
            result = self.connection.get(f"/zones/{self.params['name']}")
            if 'errorCode' in result:
                # 8001 is insufficient permissions
                if result['errorCode'] == 8001:
                    res['failed'] = True
                    res['msg'] = result['errorMessage']
                else:
                    # zone probably doesn't exist. ok to create
                    primary_data = {
                        'properties': {
                            'name': self.params['name'],
                            'accountName': self.params['account'],
                            'type': 'PRIMARY'
                        },
                        'primaryCreateInfo': {
                            'forceImport': 'True',
                            'createType': 'NEW'
                        }}
                    res['changed'], res['failed'], res['msg'] = self.create_zone(primary_data)
            else:
                # zone exists, show its details
                res['msg'] = f"zone: {result['properties']['name']} type: {result['properties']['type']}"
        elif self.params['state'] == 'absent':
            res['changed'], res['failed'], res['msg'] = self.delete_zone(self.params['name'])
        else:
            res['failed'] = True
            res['msg'] = f"Unsupported state {self.params['state']}"

        return res

    def secondary_zone(self):
        res = {'changed': False, 'failed': False, 'msg': ''}

        # check for required fields
        required = ['name', 'account', 'state']
        tsig = ['tsigKey', 'tsigKeyValue', 'tsigAlgorithm']
        missing = self._check_params(required)

        if 'primary' not in self.params or not isinstance(self.params['primary'], dict):
            missing.append('primary')
        else:
            d = self.params['primary']
            missing += list(f'primary.{k}' for k in ['ip'] if k not in d or not d[k])
            # if there is one tsig field, they all must be present
            tlist = list(k for k in tsig if k in d and d[k])
            if tlist and len(tlist) != len(tsig):
                missing += list(f'primary.{k}' for k in tsig if k not in tlist)
            # if tsigAlgorithm is present, it must be a valid choice
            if 'tsigAlgorithm' in d and d['tsigAlgorithm'] not in ['hmac-md5', 'sha-256', 'sha-512']:
                missing.append('primary.tsigAlgorithm')

        if missing:
            res['failed'] = True
            res['msg'] = f"Missing required fields: {', '.join(missing)}"
            return res

        # connect to the API
        connected, msg = self.connect()
        if not connected:
            res['failed'] = True
            res['msg'] = msg
            return res

        primaryns = {'ip': self.params['primary']['ip']}
        if 'tsigKey' in self.params['primary']:
            primaryns.update({
                'tsigKey': self.params['primary']['tsigKey'],
                'tsigKeyValue': self.params['primary']['tsigKeyValue'],
                'tsigAlgorithm': self.params['primary']['tsigAlgorithm']})

        secondary_info = {
            'secondaryCreateInfo': {
                'primaryNameServers': {
                    'nameServerIpList': {
                        'nameServerIp1': primaryns}}}}

        if self.params['state'] == 'present':
            result = self.connection.get(f"/zones/{self.params['name']}")
            if 'errorCode' in result:
                # 8001 is insufficient permissions
                if result['errorCode'] == 8001:
                    res['failed'] = True
                    res['msg'] = result['errorMessage']
                else:
                    # ok to create secondary zone
                    data = {
                        'properties': {
                            'name': self.params['name'],
                            'accountName': self.params['account'],
                            'type': 'SECONDARY'}}
                    data.update(secondary_info)
                    res['changed'], res['failed'], res['msg'] = self.create_zone(data)
            else:
                # zone exists
                # may need to update things like the primary nameserver
                if result['properties']['type'] != 'SECONDARY':
                    res['msg'] = f"zone: {result['properties']['name']} type: {result['properties']['type']}"
                    res['failed'] = True
                    res['changed'] = False
                else:
                    # check if the primary nameserver is different
                    if result['primaryNameServers']['nameServerIpList']['nameServerIp1'] != primaryns:
                        res['changed'], res['failed'], res['msg'] = self.update_zone(result['properties']['name'], secondary_info)
                    else:
                        res['msg'] = f"Success! zone: {result['properties']['name']} type: {result['properties']['type']}"
        elif self.params['state'] == 'absent':
            res['changed'], res['failed'], res['msg'] = self.delete_zone(self.params['name'])
        else:
            res['failed'] = True
            res['msg'] = f"Unsupported state {self.params['state']}"

        return res

    def record(self):
        res = {'changed': False, 'failed': False, 'msg': ''}

        # check for required fields
        # missing the `data` field is ok for certain delete actions. check on that later
        required = ['zone', 'name', 'type', 'state']
        missing = self._check_params(required)

        if missing:
            res['failed'] = True
            res['msg'] = f"Missing required fields: {', '.join(missing)}"
            return res

        if not self.params['type'] in ['A', 'AAAA', 'CNAME', 'TXT', 'MX', 'NS', 'CAA', 'HTTPS', 'SVCB', 'PTR', 'SOA', 'SRV', 'SSHFP']:
            res['failed'] = True
            res['msg'] = f"Unsupported record type {self.params['type']}"
            return res

        if self.params['name'] == '@':
            self.params['name'] = self.params['zone']

        # connect to the API
        connected, msg = self.connect()
        if not connected:
            res['failed'] = True
            res['msg'] = msg
            return res

        # for records, the first thing to do it try to get the record by owner and type.
        # records can be simple records, multiple records with rdata in a list or pools.
        result = self.connection.get(f"/zones/{self.params['zone']}/rrsets/{self.params['type']}/{self.params['name']}")
        if 'errorCode' in result:
            # 8001 is insufficient permissions
            if result['errorCode'] == 8001:
                res['failed'] = True
                res['msg'] = result['errorMessage']
                return res
            else:
                result = {}
        else:
            if 'profile' in result['rrSets'][0]:
                if result['rrSets'][0]['profile']['@context'] != 'http://schemas.ultradns.com/RDPool.jsonschema':
                    res['failed'] = True
                    res['msg'] = 'Advanced traffic management records are not supported'
                    return res

        if self.params['state'] == 'present':
            # check for presence of the `data`
            if 'data' not in self.params or not self.params['data']:
                res['failed'] = True
                res['msg'] = 'Missing required field: data'
                return res

            if not result:
                # record probably doesn't exist. ok to create
                data = {
                    'rdata': [self.params['data']]
                }
                if self.params['ttl']:
                    data.update({'ttl': self.params['ttl']})

                res['changed'], res['failed'], res['msg'] = self.create_record(
                        self.params['zone'],
                        self.params['name'],
                        self.params['type'],
                        data)
            else:
                # record exists.  check its properties (pools, etc)
                # if data is already in the rdata list, return  no change
                # for CNAME, SOA:
                #   rdata is always a list of 1, replace
                # for type in A, AAAA:
                #   when do i create an rdpool vs replace existing? need some flag for that
                # for others:
                #   add to the rdata list or replace the entire list
                if self.params['data'] in result['rrSets'][0]['rdata']:
                    return res
                if self.params['solo'] or self.params['type'] in ['CNAME', 'SOA']:
                    data = {'rdata': [self.params['data']]}
                    if self.params['ttl']:
                        data.update({'ttl': self.params['ttl']})
                else:
                    data = {'rdata': result['rrSets'][0]['rdata']}
                    data['rdata'].append(self.params['data'])
                    if self.params['ttl']:
                        data.update({'ttl': self.params['ttl']})
                    else:
                        data.update({'ttl': result['rrSets'][0]['ttl']})

                    if self.params['type'] in ['A', 'AAAA'] and len(data['rdata']) > 1:
                        if 'profile' in result['rrSets'][0] and isinstance(result['rrSets'][0]['profile'], dict):
                            data.update({'profile': result['rrSets'][0]['profile']})
                        else:
                            data.update({'profile': {'@context': 'http://schemas.ultradns.com/RDPool.jsonschema', 'order': 'ROUND_ROBIN'}})

            res['changed'], res['failed'], res['msg'] = self.update_record(
                    self.params['zone'],
                    self.params['name'],
                    self.params['type'],
                    data)
            return res
        elif self.params['state'] == 'absent':
            # if the type is SOA, fail
            # if the record does not exist or data is not in the rdata simply return
            # if the data is in the rdata list and the length of the rdata list is 1
            #   delete the record  -- simple records and rdpools are the same call
            # if the data is in the rdata list and the length of the rdata list greater than 1
            #   build an update payload with the data removed from the rdata list
            #   if the record is an rdpool and the remaining rdata list is greater than 1
            #     add a `profile` payload
            #   update the record with PUT
            if self.params['type'] == 'SOA':
                res['failed'] = True
                res['msg'] = 'Cannot delete SOA record'
                return res
            elif not result:
                return res
            elif 'data' not in self.params or not self.params['data']:
                res['changed'], res['failed'], res['msg'] = self.delete_record(self.params['zone'], self.params['name'], self.params['type'])
                return res
            elif self.params['data'] not in result['rrSets'][0]['rdata']:
                return res
            else:
                if len(result['rrSets'][0]['rdata']) == 1:
                    res['changed'], res['failed'], res['msg'] = self.delete_record(self.params['zone'], self.params['name'], self.params['type'])
                else:
                    data = {
                        'ttl': result['rrSets'][0]['ttl'],
                        'rdata': list(r for r in result['rrSets'][0]['rdata'] if r != self.params['data'])}
                    if 'profile' in result['rrSets'][0] and isinstance(result['rrSets'][0]['profile'], dict) and len(data['rdata']) > 1:
                        data.update({'profile': result['rrSets'][0]['profile']})
                    res['changed'], res['failed'], res['msg'] = self.update_record(self.params['zone'], self.params['name'], self.params['type'], data)
                    return res
        else:
            res['failed'] = True
            res['msg'] = f"Unsupported state {self.params['state']}"

        return res
