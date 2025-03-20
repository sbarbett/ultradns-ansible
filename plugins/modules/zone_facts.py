#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: UltraDNS
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: zone_facts
author: UltraDNS (@ultradns)
short_description: Retrieve DNS zone facts from UltraDNS
description:
    - Retrieve information about DNS zones from UltraDNS without making any changes.
    - Returns the zones as Ansible facts for use in subsequent plays.
    - Supports cursor-based pagination and various filtering options.
version_added: 0.1.0
extends_documentation_fragment: ultradns.ultradns.ultra_provider
options:
    name:
        description:
            - Filter zones by this name (partial match).
        required: false
        type: str
    type:
        description:
            - Filter zones by this type.
        required: false
        choices: ['PRIMARY', 'SECONDARY', 'ALIAS']
        type: str
    status:
        description:
            - Filter zones by this status.
            - Defaults to 'ACTIVE' if not specified.
        required: false
        choices: ['ACTIVE', 'SUSPENDED', 'ALL']
        type: str
    account:
        description:
            - Filter zones by this account name.
            - Spaces in the account name will be URL-encoded automatically.
        required: false
        type: str
    network:
        description:
            - Filter zones by this network.
            - Defaults to 'ultra1' if not specified.
        required: false
        choices: ['ultra1', 'ultra2']
        type: str
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
from ansible.module_utils.basic import env_fallback
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

    module = AnsibleModule(argument_spec=argspec)
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