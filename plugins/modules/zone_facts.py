#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, UltraDNS <info@ultradns.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: zone_facts
short_description: Get facts about zones in UltraDNS
version_added: 1.1.0
description:
    - Retrieves DNS zones from UltraDNS with pagination support.
    - Supports various filtering options (name, type, status, account).
    - Returns facts about the zones under the C(zones) key.
    - This module is idempotent and does not make any changes.
author:
    - "UltraDNS (@ultradns)"
options:
    name:
        description:
            - Filter zones by name (partial match).
        required: false
        type: str
    type:
        description:
            - Filter zones by type.
        required: false
        type: str
        choices: ['PRIMARY', 'SECONDARY', 'ALIAS']
    status:
        description:
            - Filter zones by status.
        required: false
        type: str
        choices: ['ACTIVE', 'SUSPENDED', 'ALL']
    account:
        description:
            - Filter zones by account name.
        required: false
        type: str
    network:
        description:
            - Filter zones by network.
        required: false
        type: str
        choices: ['ultra1', 'ultra2']
    provider:
        description:
            - Dictionary containing connection details.
        required: false
        type: dict
        suboptions:
            username:
                description:
                    - UltraDNS username for API authentication.
                    - If not set, the ULTRADNS_USERNAME environment variable will be used.
                required: false
                type: str
            password:
                description:
                    - UltraDNS password for API authentication.
                    - If not set, the ULTRADNS_PASSWORD environment variable will be used.
                required: false
                type: str
            use_test:
                description:
                    - If set to true, use the UltraDNS test environment.
                    - If not set, the ULTRADNS_USE_TEST environment variable will be used.
                required: false
                type: bool
                default: false
notes:
    - This module returns facts only, not state changes.
'''

EXAMPLES = '''
- name: Gather zone facts
  ultradns.ultradns.zone_facts:
    name: example        # optional filter
    type: PRIMARY        # optional filter
    status: ALL          # optional filter
    account: myaccount   # optional filter
    provider: "{{ ultra_provider }}"
  register: zone_data

- name: Display zones
  ansible.builtin.debug:
    msg: "Found zone: {{ item.properties.name }}"
  loop: "{{ zone_data.ansible_facts.zones }}"
'''

RETURN = '''
ansible_facts:
    description: Facts about the zones
    returned: always
    type: complex
    contains:
        zones:
            description: List of zones returned by the API
            type: list
            returned: always
            sample:
                - properties:
                    name: example.com.
                    accountName: example
                    type: PRIMARY
                    status: ACTIVE
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ultraapi import ultra_connection_spec
from ..module_utils.ultraapi import UltraDNSModule


def main():
    # Arguments for zone facts
    argspec = {
        'name': dict(required=False, type='str'),
        'type': dict(required=False, type='str', choices=['PRIMARY', 'SECONDARY', 'ALIAS']),
        'status': dict(required=False, type='str', choices=['ACTIVE', 'SUSPENDED', 'ALL']),
        'account': dict(required=False, type='str'),
        'network': dict(required=False, type='str', choices=['ultra1', 'ultra2']),
    }

    # Add the arguments required for connecting to UltraDNS API
    argspec.update(ultra_connection_spec())

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)
    api = UltraDNSModule(module.params)

    # Get zones with pagination
    zones, result = api.get_zones()

    # Check if there was an error
    if 'failed' in result and result['failed']:
        module.fail_json(**result)
    else:
        # Return the zones as ansible_facts
        module.exit_json(changed=False, ansible_facts={'zones': zones})


if __name__ == '__main__':
    main()
