"""
This is an enumeration of the various exit codes in Linode CLI
"""

from enum import Enum

class ExitCodes(Enum):
    SUCCESS = 0
    UNRECOGNIZED_COMMAND = 1
    REQUEST_FAILED = 2
    OAUTH_ERROR = 3
    USERNAME_ERROR = 4
    FIREWALL_ERROR = 5
    KUBECONFIG_ERROR = 6
    ARGUMENT_ERROR = 7
    FILE_ERROR = 8