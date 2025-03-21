from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.basic import env_fallback
from ipaddress import ip_address
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
    def __init__(self, spec):
        self.params = spec
        self.connection = None
        self.msg = ''

    def _fail_no_change(self, msg=''):
        return {'changed': False, 'failed': True, 'msg': msg if msg else self.msg}

    def _no_change(self, msg=''):
        return {'changed': False, 'failed': False, 'msg': msg if msg else self.msg}

    def _success(self):
        return {'changed': True, 'failed': False, 'msg': 'Success'}

    def _check_params(self, required,):
        conn = ['username', 'password']
        missing = list(k for k in required if k not in self.params or not self.params[k])

        if 'provider' not in self.params or not isinstance(self.params['provider'], dict):
            self.params.update({
                'provider': {'username': env_fallback('ULTRADNS_USERNAME'),
                             'password': '********'}})
        else:
            d = self.params['provider']
            missing += list(f'provider.{k}' for k in conn if k not in d or not d[k])

        try:
            if env_fallback('ULTRADNS_USE_TEST'):
                self.params['provider']['use_test'] = True
        except Exception:
            pass

        return missing

    def connect(self):
        if self.connection:
            self.msg = 'connected'
            return True

        connspec = self.params['provider']
        if not connspec['username'] or not connspec['password']:
            self.msg = 'Missing UltraDNS API credentials'
            return False

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
            self.msg = str(exc)
            return False

        self.msg = 'connected'
        return True

    def _check_result(self, result):
        if 'errorCode' in result:
            return self._fail_no_change(result['errorMessage'])
        else:
            return self._success()

    def data_in_record(self, data, rrset, type):
        if not isinstance(rrset, list) or not isinstance(data, str):
            return False

        if type not in ['A', 'AAAA']:
            return data in rrset
        else:
            ipdata = ip_address(data)
            iplist = list(ip_address(ip) for ip in rrset)
            return ipdata in iplist

    def remove_from_record(self, data, rrset, type):
        if not isinstance(rrset, list) or not isinstance(data, str):
            return rrset

        if type not in ['A', 'AAAA']:
            return list(r for r in rrset if r != data)
        else:
            ipdata = ip_address(data)
            return list(r for r in rrset if ip_address(r) != ipdata)

    def create(self, path, data):
        if self.connection:
            return self._check_result(self.connection.post(path, data))
        else:
            return self._fail_no_change(msg='Not connected to UltraDNS API')

    def update(self, path, data):
        if self.connection:
            return self._check_result(self.connection.put(path, data))
        else:
            return self._fail_no_change(msg='Not connected to UltraDNS API')

    def patch(self, path, data):
        if self.connection:
            return self._check_result(self.connection.patch(path, data))
        else:
            return self._fail_no_change(msg='Not connected to UltraDNS API')

    def delete(self, path):
        if self.connection:
            return self._check_result(self.connection.delete(path))
        else:
            return self._fail_no_change(msg='Not connected to UltraDNS API')

    def primary_zone(self):
        # check for required fields
        required = ['name', 'account', 'state']
        missing = self._check_params(required)

        if missing:
            return self._fail_no_change(f"Missing required fields: {', '.join(missing)}")

        # connect to the API
        if not self.connect():
            return self._fail_no_change()

        res = {}
        if self.params['state'] == 'present':
            result = self.connection.get(f"/zones/{self.params['name']}")
            if 'errorCode' in result:
                # 8001 is insufficient permissions
                if result['errorCode'] == 8001:
                    res = self._fail_no_change(result['errorMessage'])
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
                    res = self.create('/zones', primary_data)
            else:
                # zone exists, show its details
                res = self._no_change(f"zone: {result['properties']['name']} type: {result['properties']['type']}")
        elif self.params['state'] == 'absent':
            res = self.delete(f"/zones/{self.params['name']}")
        else:
            res = self._fail_no_change(f"Unsupported state {self.params['state']}")
        return res

    def secondary_zone(self):
        # check for required fields
        required = ['name', 'account', 'state']
        missing = self._check_params(required)

        # secondary zone requires primary nameserver info
        tsig = ['tsigKey', 'tsigKeyValue', 'tsigAlgorithm']
        if 'primary' not in self.params or not isinstance(self.params['primary'], dict):
            missing.append('primary')
        else:
            d = self.params['primary']
            if 'ip' not in d or not d['ip']:
                missing.append('primary.ip')
            # if there is one tsig field, they all must be present
            tlist = list(k for k in tsig if k in d and d[k])
            if tlist and len(tlist) != len(tsig):
                missing += list(f'primary.{k}' for k in tsig if k not in tlist)
            # if tsigAlgorithm is present, it must be a valid choice
            if 'tsigAlgorithm' in d and d['tsigAlgorithm'] not in ['hmac-md5', 'sha-256', 'sha-512']:
                missing.append('primary.tsigAlgorithm')

        if missing:
            return self._fail_no_change(f"Missing required fields: {', '.join(missing)}")

        # connect to the API
        if not self.connect():
            return self._fail_no_change()

        res = {}
        if self.params['state'] == 'present':
            # build the secondary zone data used for creating or updating
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

            result = self.connection.get(f"/zones/{self.params['name']}")
            if 'errorCode' in result:
                # 8001 is insufficient permissions
                if result['errorCode'] == 8001:
                    res = self._fail_no_change(result['errorMessage'])
                else:
                    # ok to create secondary zone
                    data = {
                        'properties': {
                            'name': self.params['name'],
                            'accountName': self.params['account'],
                            'type': 'SECONDARY'}}
                    data.update(secondary_info)
                    res = self.create('/zones', data)
            else:
                # zone exists
                # may need to update things like the primary nameserver
                if result['properties']['type'] != 'SECONDARY':
                    res = self._no_change(f"zone: {result['properties']['name']} type: {result['properties']['type']}")
                else:
                    # check if the primary nameserver is different
                    if result['primaryNameServers']['nameServerIpList']['nameServerIp1'] != primaryns:
                        res = self.update(f"/zones/{result['properties']['name']}", secondary_info)
                    else:
                        res = self._success()
        elif self.params['state'] == 'absent':
            res = self.delete(f"/zones/{self.params['name']}")
        else:
            res = self._fail_no_change(f"Unsupported state {self.params['state']}")
        return res

    def record(self):
        # check for required fields
        # missing the `data` field is ok for certain delete actions and TTL-only updates. check on that later
        required = ['zone', 'name', 'type', 'state']
        missing = self._check_params(required)

        if missing:
            return self._fail_no_change(f"Missing required fields: {', '.join(missing)}")

        if not self.params['type'] in ['A', 'AAAA', 'CNAME', 'TXT', 'MX', 'NS', 'CAA', 'HTTPS', 'SVCB', 'PTR', 'SOA', 'SRV', 'SSHFP']:
            return self._fail_no_change(f"Unsupported record type {self.params['type']}")

        if self.params['name'] == '@':
            self.params['name'] = self.params['zone']

        # connect to the API
        if not self.connect():
            return self._fail_no_change()

        # make a path to the record. going to need it a few times
        path = f"/zones/{self.params['zone']}/rrsets/{self.params['type']}"
        # for records, the first thing to do it try to get the record by owner and type.
        # records can be simple records, multiple records with rdata in a list or pools.
        result = self.connection.get(f"{path}/{self.params['name']}")
        if 'errorCode' in result:
            # 8001 is insufficient permissions
            if result['errorCode'] == 8001:
                return self._fail_no_change(result['errorMessage'])
            else:
                result = {}
        else:
            # if the record is a pool, check the profile context, if it's not an rdpool, fail
            if 'profile' in result['rrSets'][0]:
                if result['rrSets'][0]['profile']['@context'] != 'http://schemas.ultradns.com/RDPool.jsonschema':
                    return self._fail_no_change('Advanced traffic management records are not supported')

        res = {}
        if self.params['state'] == 'present':
            # Check if this is a TTL-only update (data not provided but ttl is)
            if ('data' not in self.params or not self.params['data']) and 'ttl' in self.params and self.params['ttl']:
                if not result:
                    return self._fail_no_change('Record does not exist. Cannot update TTL only.')

                # Check if TTL is already set to the requested value
                if self.params['ttl'] == result['rrSets'][0]['ttl']:
                    return self._no_change('TTL already set to requested value')

                # Use PATCH to update only the TTL
                data = {'ttl': self.params['ttl']}
                return self.patch(f"{path}/{self.params['name']}", data)

            # Regular record update with data
            if 'data' not in self.params or not self.params['data']:
                return self._fail_no_change('Missing required field: data')

            if not result:
                # record probably doesn't exist. ok to create
                data = {'rdata': [self.params['data']]}
                if self.params['ttl']:
                    data.update({'ttl': self.params['ttl']})

                res = self.create(f"{path}/{self.params['name']}", data)
            else:
                # record exists.  check its properties (pools, etc)
                # if data is already in the rdata list, return  no change
                # for CNAME, SOA:
                #   rdata is always a list of 1, replace
                # for solo=True:
                #   rdata is always a list of 1, replace
                # for type in A, AAAA:
                #   when do i create an rdpool vs replace existing? need some flag for that
                # for others:
                #   add to the rdata list or replace the entire list
                data = {}
                if self.params['solo'] or self.params['type'] in ['CNAME', 'SOA']:
                    if len(result['rrSets'][0]['rdata']) == 1:
                        if result['rrSets'][0]['rdata'][0] != self.params['data']:
                            data = {'rdata': [self.params['data']]}
                    else:
                        data = {'rdata': [self.params['data']]}

                    # Only add TTL if we're already making a change or if TTL is different
                    if data or (self.params['ttl'] and self.params['ttl'] != result['rrSets'][0]['ttl']):
                        if self.params['ttl']:
                            data.update({'ttl': self.params['ttl']})
                        elif data:  # If making rdata change but no TTL specified, preserve existing TTL
                            data.update({'ttl': result['rrSets'][0]['ttl']})

                    if not data:
                        return self._no_change()
                elif self.data_in_record(self.params['data'], result['rrSets'][0]['rdata'], self.params['type']):
                    if self.params['ttl'] and self.params['ttl'] != result['rrSets'][0]['ttl']:
                        data = {'ttl': self.params['ttl'], 'rdata': result['rrSets'][0]['rdata']}
                    else:
                        return self._no_change()
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

                res = self.update(f"{path}/{self.params['name']}", data)
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
                res = self._fail_no_change('Cannot delete SOA record')
            elif not result:
                res = self._no_change()
            elif 'data' not in self.params or not self.params['data']:
                res = self.delete(f"{path}/{self.params['name']}")
            elif not self.data_in_record(self.params['data'], result['rrSets'][0]['rdata'], self.params['type']):
                res = self._no_change()
            else:
                if len(result['rrSets'][0]['rdata']) == 1:
                    res = self.delete(f"{path}/{self.params['name']}")
                else:
                    data = {
                        'ttl': result['rrSets'][0]['ttl'],
                        'rdata': self.remove_from_record(self.params['data'], result['rrSets'][0]['rdata'], self.params['type'])}
                    if 'profile' in result['rrSets'][0] and isinstance(result['rrSets'][0]['profile'], dict) and len(data['rdata']) > 1:
                        data.update({'profile': result['rrSets'][0]['profile']})
                    res = self.update(f"{path}/{self.params['name']}", data)
        else:
            res = self._fail_no_change(f"Unsupported state {self.params['state']}")
        return res

    def get_zones(self):
        """
        Retrieve all zones from the UltraDNS API with pagination support.
        
        This function handles cursor-based pagination automatically, making multiple
        requests as needed to retrieve all zones. The default limit is set to 1000 
        zones per request, and filtering is done based on provided parameters.
        
        Returns:
            A list of zone objects from the API response
        """
        # Connect to the API
        if not self.connect():
            return [], self._fail_no_change()
        
        # Initialize empty zones list and base URL
        all_zones = []
        base_path = '/v3/zones'
        
        # Build the query string for filters
        query_parts = []
        
        # Add limit parameter
        query_parts.append('limit=1000')
        
        # Filter by name (partial match)
        if 'name' in self.params and self.params['name']:
            query_parts.append(f"q=name:{self.params['name']}")
        
        # Filter by zone type
        if 'type' in self.params and self.params['type']:
            zone_type = self.params['type']
            if zone_type in ['PRIMARY', 'SECONDARY', 'ALIAS']:
                if 'q=' in ' '.join(query_parts):
                    # Append to existing q parameter
                    q_index = next(i for i, part in enumerate(query_parts) if part.startswith('q='))
                    query_parts[q_index] = f"{query_parts[q_index]}+zone_type:{zone_type}"
                else:
                    query_parts.append(f"q=zone_type:{zone_type}")
        
        # Filter by status
        if 'status' in self.params and self.params['status']:
            status = self.params['status']
            if status in ['ACTIVE', 'SUSPENDED', 'ALL']:
                if 'q=' in ' '.join(query_parts):
                    # Append to existing q parameter
                    q_index = next(i for i, part in enumerate(query_parts) if part.startswith('q='))
                    query_parts[q_index] = f"{query_parts[q_index]}+zone_status:{status}"
                else:
                    query_parts.append(f"q=zone_status:{status}")
        
        # Filter by account name
        if 'account' in self.params and self.params['account']:
            # URL-encode spaces in account name
            account = self.params['account'].replace(' ', '%20')
            if 'q=' in ' '.join(query_parts):
                # Append to existing q parameter
                q_index = next(i for i, part in enumerate(query_parts) if part.startswith('q='))
                query_parts[q_index] = f"{query_parts[q_index]}+account_name:{account}"
            else:
                query_parts.append(f"q=account_name:{account}")
        
        # Filter by network
        if 'network' in self.params and self.params['network']:
            network = self.params['network']
            if network in ['ultra1', 'ultra2']:
                if 'q=' in ' '.join(query_parts):
                    # Append to existing q parameter
                    q_index = next(i for i, part in enumerate(query_parts) if part.startswith('q='))
                    query_parts[q_index] = f"{query_parts[q_index]}+network:{network}"
                else:
                    query_parts.append(f"q=network:{network}")
        
        # Build initial path with query parameters
        path = base_path
        if query_parts:
            path = f"{base_path}?{'&'.join(query_parts)}"
        
        # Track if we have more data to fetch
        has_more = True
        next_path = path
        
        while has_more:
            # Get zones with current path
            result = self.connection.get(next_path)
            
            # Check if response has an error
            if 'errorCode' in result:
                return [], self._fail_no_change(result['errorMessage'])
            
            # Add zones from current response to our collection
            if 'zones' in result and isinstance(result['zones'], list):
                all_zones.extend(result['zones'])
            
            # Check for cursorInfo to determine if more data is available
            if 'cursorInfo' in result and result['cursorInfo'].get('next'):
                cursor = result['cursorInfo']['next']
                # Determine if the path already has query parameters
                if '?' in next_path:
                    if 'cursor=' in next_path:
                        # Replace existing cursor parameter
                        next_path = next_path.split('cursor=')[0] + f"cursor={cursor}"
                    else:
                        # Add cursor parameter
                        next_path = f"{next_path}&cursor={cursor}"
                else:
                    # Add cursor as first parameter
                    next_path = f"{next_path}?cursor={cursor}"
            else:
                has_more = False
        
        return all_zones, self._no_change(f"Retrieved {len(all_zones)} zones")

    def get_zone_metadata(self):
        """
        Retrieve metadata for a list of specific zones from the UltraDNS API.
        
        This function sends a GET request to /v3/zones/{zone_name} for each zone
        in the provided list and collects the results. If a zone doesn't exist
        or there's an error retrieving it, the function handles this gracefully
        without failing the entire operation.
        
        Returns:
            A dictionary with zone names as keys and their metadata as values,
            plus a result object indicating success or failure
        """
        # Check for required fields
        required = ['zones']
        missing = self._check_params(required)
        
        if missing:
            return {}, self._fail_no_change(f"Missing required fields: {', '.join(missing)}")
            
        # Connect to the API
        if not self.connect():
            return {}, self._fail_no_change()
            
        # Get the list of zones to fetch
        zone_names = self.params['zones']
        if not isinstance(zone_names, list):
            return {}, self._fail_no_change("The 'zones' parameter must be a list of zone names")
            
        # Initialize dictionary to store zone metadata
        zone_metadata = {}
        
        # Determine if we should fail on error
        fail_on_error = self.params.get('fail_on_error', False)
        
        # Fetch metadata for each zone
        for zone_name in zone_names:
            result = self.connection.get(f"/v3/zones/{zone_name}")
            
            # Check if response has an error - might be a dict with errorCode or a list with error object
            if isinstance(result, list) and result and 'errorCode' in result[0]:
                if fail_on_error:
                    return zone_metadata, self._fail_no_change(
                        f"Error retrieving zone '{zone_name}': {result[0].get('errorMessage', 'Unknown error')}"
                    )
                # If we're not failing on error, log the error and continue
                continue
            elif isinstance(result, dict) and 'errorCode' in result:
                if fail_on_error:
                    return zone_metadata, self._fail_no_change(
                        f"Error retrieving zone '{zone_name}': {result.get('errorMessage', 'Unknown error')}"
                    )
                # If we're not failing on error, log the error and continue
                continue
                
            # Store the zone metadata
            zone_metadata[zone_name] = result
            
        return zone_metadata, self._no_change(f"Retrieved metadata for {len(zone_metadata)} out of {len(zone_names)} requested zones")
