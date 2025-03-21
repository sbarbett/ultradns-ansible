#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, UltraDNS <info@ultradns.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: zone_meta_facts
short_description: Get metadata for specific zones in UltraDNS
version_added: 1.1.0
description:
    - Retrieves detailed metadata for specified zone names from UltraDNS.
    - Uses the /v3/zones/{zone_name} API endpoint for each zone.
    - Returns facts about the zones under the C(zone_meta) key.
    - This module is idempotent and does not make any changes.
    - When a zone does not exist, the API returns an error code 1801 with message "Zone does not exist in the system."
    - By default, these errors are handled gracefully (zones are skipped) and do not cause the module to fail.
author:
    - "UltraDNS (@ultradns)"
options:
    zones:
        description:
            - List of zone names for which to retrieve metadata.
            - Each zone name will be used in an individual API call.
        required: true
        type: list
        elements: str
    fail_on_error:
        description:
            - If true, the module will fail if any zone metadata cannot be retrieved.
            - If false, zones that cause errors (like non-existent zones) will be skipped and noted in the return message.
            - Common error is code 1801 "Zone does not exist in the system" for non-existent zones.
        required: false
        type: bool
        default: false
    provider:
        description:
            - Dictionary containing connection details.
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
    - For a more general zone listing with filtering, use the C(zone_facts) module.
'''

EXAMPLES = '''
- name: Gather specific zones metadata
  ultradns.ultradns.zone_meta_facts:
    provider: "{{ ultra_provider }}"
    zones:
      - example1.com
      - example2.com
      - example3.com
  register: specific_zones

- name: Display specific zone metadata
  ansible.builtin.debug:
    msg: "Metadata for zone {{ item.key }}: {{ item.value }}"
  loop: "{{ specific_zones.ansible_facts.zone_meta | dict2items }}"

- name: Fail if any zone can't be retrieved
  ultradns.ultradns.zone_meta_facts:
    provider: "{{ ultra_provider }}"
    zones:
      - example1.com
      - example2.com
    fail_on_error: true
  register: critical_zones

- name: Handle non-existent zones gracefully
  ultradns.ultradns.zone_meta_facts:
    provider: "{{ ultra_provider }}"
    zones:
      - existing-zone.com
      - non-existent-zone.com
    # fail_on_error defaults to false, so non-existent zones are simply skipped
  register: mixed_zones

- name: Check which zones were successfully retrieved
  ansible.builtin.debug:
    msg: "Successfully retrieved {{ mixed_zones.ansible_facts.zone_meta | length }} zones: {{ mixed_zones.ansible_facts.zone_meta.keys() | list }}"
'''

RETURN = '''
ansible_facts:
    description: Facts about the requested zones
    returned: always
    type: complex
    contains:
        zone_meta:
            description: Dictionary of zone names with their corresponding metadata
            type: dict
            returned: always
            sample:
                example.com:
                    properties:
                        name: example.com.
                        accountName: example
                        type: PRIMARY
                        status: ACTIVE
                        lastModifiedDateTime: "2023-08-01T12:34:56Z"
                    primaryCreateInfo:
                        createType: NEW
                        forceImport: true
                    resourceRecordCount: 12
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ultraapi import ultra_connection_spec
from ..module_utils.ultraapi import UltraDNSModule


def main():
    # Arguments for zone meta facts
    argspec = {
        'zones': dict(required=True, type='list', elements='str'),
        'fail_on_error': dict(required=False, type='bool', default=False),
    }

    # Add the arguments required for connecting to UltraDNS API
    argspec.update(ultra_connection_spec())

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)
    api = UltraDNSModule(module.params)

    # Get metadata for the specified zones
    zone_metadata, result = api.get_zone_metadata()

    # Check if there was an error
    if 'failed' in result and result['failed']:
        module.fail_json(**result)
    else:
        # Return the zone metadata as ansible_facts
        module.exit_json(changed=False, ansible_facts={'zone_meta': zone_metadata})


if __name__ == '__main__':
    main()
