#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: UltraDNS
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
---
module: secondary_zone
author: UltraDNS (@ultradns)
short_description: Manage secondary zones in UltraDNS
description:
    - Add or remove secondary zones in UltraDNS
version_added: 1.0.0
options:
    name:
        description:
            - The name of the primary zone to manage
        required: true
        type: str
    account:
        description:
            - The account name to which the primary zone belongs
        required: true
        type: str
    primary:
        description:
            - The primary nameserver information.
        required: true
        type: dict
        suboptions:
            ip:
                description:
                    - The IP address of the primary nameserver.
                required: true
                type: str
            tsigKey:
                description:
                    - The TSIG key name.
                required: false
                type: str
            tsigKeyValue:
                description:
                    - The TSIG key value.
                required: false
                type: str
            tsigAlgorithm:
                description:
                    - The TSIG algorithm.
                required: false
                type: str
                choices: ['hmac-md5', 'sha-256', 'sha-512']
    state:
        description:
            - The desired state of the primary zone
        required: true
        type: str
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
seealso:
    - module: M(ultradns.ultradns.zone)
requirements:
    - L(requests,https://pypi.org/project/requests/)
notes:
    - "This module must be run locally, which can be achieved by specifying C(connection: local)"
    - When O(state=present) and the zone already exists, the module will call the UltraDNS API with PUT which will overwrite
      existing primary nameserver details.
    - If setting TSIG keys in the O(primary) section, all O(tsigKey), O(tsigKeyValue), and O(tsigAlgorithm) must be set together.
    - Refer to the L(UltraDNS API documentation,https://docs.ultradns.com/submenu.html) for more information.
'''

EXAMPLES = '''
- name: Configure a secondary zone on UltraDNS to transfer from a primary nameserver with TSIG keys
  ultradns.ultradns.zone:
    name: secondary.com
    account: example-account
    primary:
      ip: 10.0.0.1
      tsigKey: keyname
      tsigKeyValue: keyvalue
      tsigAlgorithm: sha-256
    state: present
    provider:
      username: myuser
      password: mypass
    connection: local

- name: Update TSIG key for primary nameserver of a secondary zone
  ultradns.ultradns.zone:
    name: secondary.com
    account: example-account
    primary:
      ip: 10.0.0.1
      tsigKey: keyname
      tsigKeyValue: new-keydata
      tsigAlgorithm: sha-256
    state: present
    provider:
      username: myuser
      password: mypass
    connection: local

- name: Configure a secondary zone on UltraDNS to transfer from a primary nameserver without TSIG keys
  ultradns.ultradns.zone:
    name: example.com
    account: example-account
    primary:
      ip: 10.0.0.1
    state: present
    provider:
      username: myuser
      password: mypass
    connection: local

- name: Update the primary nameserver of a secondary zone
  ultradns.ultradns.zone:
    name: example.com
    account: example-account
    primary:
      ip: 100.10.10.100
    state: present
    provider:
      username: myuser
      password: mypass
    connection: local

- name: Remove a secondary zone from UltraDNS
  ultradns.ultradns.zone:
    name: example.com
    account: example-account
    primary:
      ip: 10.0.0.1
    state: absent
    provider:
      username: myuser
      password: mypass
    connection: local
'''
RETURN = ''' # '''

from __future__ import absolute_import, print_function
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ..module_utils.ultraapi import ultra_connection_spec
from ..module_utils.ultraapi import UltraDNSModule

PRIMARY_NS_SPEC = {
  'ip': dict(required=True, type='str'),
  'tsigKey': dict(required=False, type='str'),
  'tsigKeyValue': dict(required=False, type='str'),
  'tsigAlgorithm': dict(required=False, type='str', choices=['hmac-md5', 'sha-256', 'sha-512'])
}

def main (): 
  # Arguments required for the primary zone
  argspec = {
    'name': dict(required=True, type='str'),
    'account': dict(required=True, type='str', fallback=(env_fallback, ['ULTRADNS_ACCOUNT'])),
    'primary': dict(required=True, type='str', options=PRIMARY_NS_SPEC),
    'state': dict(required=True, type='str', choices=['present', 'absent'])
  }

  # Add the arguments required for connecting to UltraDNS API
  argspec.update(ultra_connection_spec())

  module = AnsibleModule(argument_spec=argspec)
  api = UltraDNSModule(module)

  result = api.secondary_zone()
  if 'failed' in result and result['failed']:
    module.fail_json(**result)
  else:
    module.exit_json(**result)


if __name__ == '__main__':
    main()