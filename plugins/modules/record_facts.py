#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, UltraDNS <info@ultradns.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: record_facts
short_description: Get facts about DNS records in a zone in UltraDNS
version_added: 1.1.0
description:
    - Retrieves DNS records for a specific zone from UltraDNS.
    - Uses the /v3/zones/{zoneName}/rrsets API endpoint with offset-based pagination.
    - Supports various filtering options (owner, ttl, value).
    - Returns facts about the records under the C(record_facts) key.
    - This module is idempotent and does not make any changes.
author:
    - "UltraDNS (@ultradns)"
options:
    zone:
        description:
            - Name of the zone for which to retrieve records.
        required: true
        type: str
    owner:
        description:
            - Filter records by owner name (partial match).
            - Applies to all RRSet types.
        required: false
        type: str
    ttl:
        description:
            - Filter records by TTL (exact match).
            - Only valid for RECORDS RRSet type; ignored for others.
        required: false
        type: int
    value:
        description:
            - Filter records by rdata value (partial match).
            - Only valid for RECORDS RRSet type; ignored for others.
        required: false
        type: str
    kind:
        description:
            - Type of RRSets to retrieve.
        required: false
        type: str
        choices: ['ALL', 'RECORDS', 'POOLS', 'RD_POOLS', 'DIR_POOLS', 'SB_POOLS', 'TC_POOLS']
        default: 'ALL'
    reverse:
        description:
            - If true, returns records in descending order.
        required: false
        type: bool
        default: false
    sys_generated:
        description:
            - If true, includes system-generated status information in the response.
            - This does not filter to show only system-generated records; it adds an indicator to all records.
            - When enabled, each RRSet will include a 'systemGenerated' array that indicates if each rdata entry was system-generated.
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
    - Uses offset-based pagination to automatically retrieve all records.
    - The API may return an error code 70002 (Data not found) if no records match the filters.
    - In such cases, an empty list is returned rather than failing the play.
    - Record types (rrtype) in the API response include type numbers, e.g., 'A (1)', 'AAAA (28)'.
'''

EXAMPLES = '''
- name: Gather all records for a zone
  ultradns.ultradns.record_facts:
    zone: example.com
    provider: "{{ ultra_provider }}"
  register: record_data

- name: Display records
  ansible.builtin.debug:
    msg: "Found record: {{ item }}"
  loop: "{{ record_data.ansible_facts.record_facts }}"

- name: Gather A records with a specific owner
  ultradns.ultradns.record_facts:
    zone: example.com
    owner: www        # partial match for owner name
    provider: "{{ ultra_provider }}"
  register: www_records

- name: Gather records with specific TTL
  ultradns.ultradns.record_facts:
    zone: example.com
    ttl: 300          # exact match for TTL
    kind: RECORDS     # TTL filter only applies to RECORDS
    provider: "{{ ultra_provider }}"
  register: ttl_records

- name: Gather records with specific value
  ultradns.ultradns.record_facts:
    zone: example.com
    value: 192.168    # partial match for rdata value
    provider: "{{ ultra_provider }}"
  register: ip_records

- name: Gather only pool records in reverse order
  ultradns.ultradns.record_facts:
    zone: example.com
    kind: POOLS       # get only pool records
    reverse: true     # reverse the sort order
    provider: "{{ ultra_provider }}"
  register: pool_records

- name: Include system-generated status information
  ultradns.ultradns.record_facts:
    zone: example.com
    sys_generated: true  # adds system-generated status indicators to records
    provider: "{{ ultra_provider }}"
  register: system_records

- name: Display records with system-generated status
  ansible.builtin.debug:
    msg: "Record {{ item.ownerName }} ({{ item.rrtype }}) is {{ 'system-generated' if item.systemGenerated[0] else 'user-created' }}"
  loop: "{{ system_records.ansible_facts.record_facts }}"
  when: "'systemGenerated' in item"
'''

RETURN = '''
ansible_facts:
    description: Facts about the requested DNS records
    returned: always
    type: complex
    contains:
        record_facts:
            description: List of RRSet records returned by the API
            type: list
            returned: always
            sample:
                - ownerName: "www.example.com."
                  rrtype: "A (1)"  # Note the type number in parentheses
                  ttl: 300
                  rdata: ["192.168.1.1"]
                  systemGenerated: [false]  # Array indicating if each rdata entry was system-generated
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ultraapi import ultra_connection_spec
from ..module_utils.ultraapi import UltraDNSModule


def main():
    # Arguments for record facts
    argspec = {
        'zone': dict(required=True, type='str'),
        'owner': dict(required=False, type='str'),
        'ttl': dict(required=False, type='int'),
        'value': dict(required=False, type='str'),
        'kind': dict(required=False, type='str',
                     choices=['ALL', 'RECORDS', 'POOLS', 'RD_POOLS', 'DIR_POOLS', 'SB_POOLS', 'TC_POOLS'],
                     default='ALL'),
        'reverse': dict(required=False, type='bool', default=False),
        'sys_generated': dict(required=False, type='bool', default=False),
    }

    # Add the arguments required for connecting to UltraDNS API
    argspec.update(ultra_connection_spec())

    module = AnsibleModule(argument_spec=argspec, supports_check_mode=True)
    api = UltraDNSModule(module.params)

    # Get records with pagination
    records, result = api.get_records()

    # Check if there was an error
    if 'failed' in result and result['failed']:
        module.fail_json(**result)
    else:
        # Return the records as ansible_facts
        module.exit_json(changed=False, ansible_facts={'record_facts': records})


if __name__ == '__main__':
    main()
