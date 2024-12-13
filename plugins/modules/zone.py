#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: UltraDNS
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: zone
author: UltraDNS (@ultradns)
short_description: Manage primary zones in UltraDNS
description:
    - Add or remove primary zones in UltraDNS
version_added: 0.1.0
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
    state:
        description:
            - The desired state of the primary zone
        required: true
        choices: ['present', 'absent']
        type: str
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
seealso:
    - module: M(ultradns.ultradns.secondary_zone)
requirements:
    - L(requests,https://pypi.org/project/requests/)
notes:
    - "This module must be run locally which can be achieved by specifying C(connection: local)"
    - Refer to the L(UltraDNS API documentation,https://docs.ultradns.com/submenu.html) for more information.
'''

EXAMPLES = '''
- name: Configure a zone on UltraDNS
  ultradns.ultradns.zone:
    name: example.com
    account: example-account
    state: present
    provider:
      username: myuser
      password: mypass
    connection: local

- name: Remove a zone from UltraDNS
  ultradns.ultradns.zone:
    name: example.com
    account: example-account
    state: absent
    provider:
      username: myuser
      password: mypass
    connection: local
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ..module_utils.ultraapi import ultra_connection_spec
from ..module_utils.ultraapi import UltraDNSModule


def main():
    # Arguments required for the primary zone
    argspec = {
        'name': dict(required=True, type='str'),
        'account': dict(required=True, type='str', fallback=(env_fallback, ['ULTRADNS_ACCOUNT'])),
        'state': dict(required=True, type='str', choices=['present', 'absent'])
    }

    # Add the arguments required for connecting to UltraDNS API
    argspec.update(ultra_connection_spec())

    module = AnsibleModule(argument_spec=argspec)
    api = UltraDNSModule(module)

    result = api.primary_zone()
    if 'failed' in result and result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
