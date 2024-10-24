"""
This is an enumeration of the various exit codes in Linode CLI

"""

from enum import IntEnum


class ExitCodes(IntEnum):
    """
    An enumeration of the various exit codes in Linode CLI
    """

    SUCCESS = 0
    UNRECOGNIZED_COMMAND = 1
    REQUEST_FAILED = 2
    OAUTH_ERROR = 3
    USERNAME_ERROR = 4
    FIREWALL_ERROR = 5
    KUBECONFIG_ERROR = 6
    ARGUMENT_ERROR = 7
    FILE_ERROR = 8
    UNRECOGNIZED_ACTION = 9
