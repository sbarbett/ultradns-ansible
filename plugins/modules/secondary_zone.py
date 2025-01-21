#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: UltraDNS
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: secondary_zone
author: UltraDNS (@ultradns)
short_description: Manage secondary zones in UltraDNS
description:
    - Add or remove secondary zones in UltraDNS. A secondary zone is a copy of a zone that is transferred from an external nameserver.
version_added: 0.1.0
extends_documentation_fragment: ultradns.ultradns.ultra_provider
options:
    name:
        description:
            - The fully qualified (dot-terminated) name of the zone to transfer
        required: true
        type: str
    account:
        description:
            - The account name to which the zone belongs as shown in the UltraDNS portal.
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
seealso:
    - module: ultradns.ultradns.zone
notes:
    - When O(state=present) and the zone already exists, the module will call the UltraDNS API with PUT which will overwrite
      existing primary nameserver details.
    - If setting TSIG keys in the O(primary) section, all O(primary.tsigKey), O(primary.tsigKeyValue), and O(primary.tsigAlgorithm) must be set together.
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
    provider: "{{ ultra_provider }}"

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
    provider: "{{ ultra_provider }}"

- name: Configure a secondary zone on UltraDNS to transfer from a primary nameserver without TSIG keys
  ultradns.ultradns.zone:
    name: example.com
    account: example-account
    primary:
      ip: 10.0.0.1
    state: present
    provider: "{{ ultra_provider }}"

- name: Update the primary nameserver of a secondary zone
  ultradns.ultradns.zone:
    name: example.com
    account: example-account
    primary:
      ip: 100.10.10.100
    state: present
    provider: "{{ ultra_provider }}"

- name: Remove a secondary zone from UltraDNS
  ultradns.ultradns.zone:
    name: example.com
    account: example-account
    primary:
      ip: 10.0.0.1
    state: absent
    provider: "{{ ultra_provider }}"
'''
RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ..module_utils.ultraapi import ultra_connection_spec
from ..module_utils.ultraapi import UltraDNSModule

PRIMARY_NS_SPEC = {
    'ip': dict(required=True, type='str'),
    'tsigKey': dict(required=False, type='str', no_log=True),
    'tsigKeyValue': dict(required=False, type='str', no_log=True),
    'tsigAlgorithm': dict(required=False, type='str', no_log=True, choices=['hmac-md5', 'sha-256', 'sha-512'])
}


def main():
    # Arguments required for the primary zone
    argspec = {
        'name': dict(required=True, type='str'),
        'account': dict(required=True, type='str', fallback=(env_fallback, ['ULTRADNS_ACCOUNT'])),
        'primary': dict(required=True, type='dict', options=PRIMARY_NS_SPEC),
        'state': dict(required=True, type='str', choices=['present', 'absent'])
    }

    # Add the arguments required for connecting to UltraDNS API
    argspec.update(ultra_connection_spec())

    module = AnsibleModule(argument_spec=argspec)
    api = UltraDNSModule(module.params)

    result = api.secondary_zone()
    if 'failed' in result and result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
