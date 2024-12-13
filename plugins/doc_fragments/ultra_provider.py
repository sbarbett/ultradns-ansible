#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: UltraDNS
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
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
requirements:
    - L(requests,https://pypi.org/project/requests/)
notes:
    - "This module must be run locally which can be achieved by specifying C(connection: local)"
    - Refer to the L(UltraDNS API documentation,https://docs.ultradns.com/submenu.html) for more information.

'''
