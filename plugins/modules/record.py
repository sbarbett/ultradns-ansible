#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: UltraDNS
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, print_function

DOCUMENTATION = '''
---
module: record
author: UltraDNS (@ultradns)
short_description: Manage zone resource records in UltraDNS
description:
    - Add or remove common zone resource records in UltraDNS
version_added: 1.0.0
options:
    zone:
        description:
            - The zone containing the record
            - Must be a fully qualified domain name (FQDN)
        type: str
        required: true
    name:
        description:
            - The record owner name
            - May be relative to the zone (e.g. 'www') or fully qualified (e.g. 'www.example.com.')
            - V("@") may be used to for records at the zone apex
        type: str
        required: true
    type:
        description:
            - The record type by common name
        required: true
        type: str
        choices: ['A', 'AAAA', 'CNAME', 'TXT', 'MX', 'NS', 'CAA', 'HTTPS', 'SVCB', 'PTR', 'SOA', 'SRV', 'SSHFP']
    ttl:
        description:
            - The record time-to-live (TTL) in seconds
            - Defaults to UltraDNS account default if not specified
        type: int
        required: false
    data:
        description:
            - The complete rdata of the record as a string
            - Required for O(state=present)
            - If not specified for O(state=absent), all records in the rrset will be removed
        type: str
        required: false
    solo:
        description:
            - Determines the behavior when adding a record to an existing rrset.
            - O(solo=true) will replace the existing rrset with the new record, removing any existing records.
            - O(solo=false) will add the new record to the existing rrset.
            - Ignored if O(type=CNAME) or O(type=SOA)
            - Ignored when O(state=absent)
            - Defaults to O(solo=false)
        required: false
        type: bool
    state:
        description:
            - The desired state of the record
        required: true
        choices: ['present', 'absent']
    provider:
        description:
            - Connection information for the UltraDNS API
        required: false
        type: dict
        suboptions:
            use_test:
                description:
                    - Whether to use the test API endpoint
                required: false
                type: bool
                default: false
            username:
                description:
                    - The UltraDNS username. Set the E(ULTRADNS_USERNAME) environment variable to avoid exposing this in your playbook
                required: false
                type: str
            password:
                description:
                    - The UltraDNS password. Set the E(ULTRADNS_PASSWORD) environment variable to avoid exposing this in your playbook
                required: false
                type: str
                no_log: true
requirements:
    - L(requests,https://pypi.org/project/requests/)
notes:
    - "This module must be run locally which can be achieved by specifying C(connection: local)"
    - Refer to the L(UltraDNS API documentation,https://docs.ultradns.com/submenu.html) for more information.
'''

EXAMPLES = '''
- name: Create test.example.com A record with default TTL
  ultradns.ultradns.record:
    zone: example.com.
    name: test
    type: A
    data: 127.0.0.1
    state: present
    provider:
      username: myuser
      password: mypass
    connection: local

- name: Create a null MX record for example.com
  ultradns.ultradns.record:
    zone: example.com.
    name: "@"
    type: MX
    data: 0 .
    state: present
    provider:
      username: myuser
      password: mypass
    connection: local

- name: Add a TXT record to test.example.com
  ultradns.ultradns.record:
    zone: example.com.
    name: test
    type: TXT
    ttl: 3600
    data: "txt example"
    state: present
    connection: local

- name: Add a second TXT record to test.example.com
  ultradns.ultradns.record:
    zone: example.com.
    name: test
    type: TXT
    ttl: 3600
    data: "asdfghjkl"
    solo: false
    state: present
    connection: local

- name: Remove the first TXT record from test.example.com
  ultradns.ultradns.record:
    zone: example.com.
    name: test
    type: TXT
    data: "txt example"
    state: absent
    connection: local

- name: Remove all MX records from the apex of example.com
  ultradns.ultradns.record:
    zone: example.com.
    name: "@"
    type: MX
    state: absent
    connection: local
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ultraapi import ultra_connection_spec
from ..module_utils.ultraapi import UltraDNSModule

def main():
    # Arguments required for the primary zone
    argspec = {
        'zone': dict(required=True, type='str'),
        'name': dict(required=True, type='str'),
        'type': dict(required=True, type='str', choices=['A', 'AAAA', 'CNAME', 'TXT', 'MX', 'NS', 'CAA', 'HTTPS', 'SVCB', 'PTR', 'SOA', 'SRV', 'SSHFP']),
        'ttl': dict(required=False, type='int'),
        'data': dict(required=False, type='str'),
        'solo': dict(required=False, type='bool', default=False),
        'state': dict(required=True, type='str', choices=['present', 'absent'])
    }

    # Add the arguments required for connecting to UltraDNS API
    argspec.update(ultra_connection_spec())

    module = AnsibleModule(argument_spec=argspec)
    api = UltraDNSModule(module)

    result = api.record()
    if 'failed' in result and result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
