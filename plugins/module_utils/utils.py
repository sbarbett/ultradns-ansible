from __future__ import absolute_import, print_function

VERSION = "0.0.0"
PREFIX = "udns-ansible-"


def get_client_user_agent():
    return f"{PREFIX}{VERSION}"
