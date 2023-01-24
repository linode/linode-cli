#!/usr/local/bin/python3
"""
Unit tests for linodecli.configuration
"""

import unittest
from unittest.mock import patch, mock_open

from linodecli import configuration

class ConfigurationTests(unittest.TestCase):
    """
    Unit tests for linodecli.configuration
    """

    mock_config_file = """[DEFAULT]
default-user = cli-dev

[cli-dev]
token = cli-dev-token
region = us-east
type = g6-nanode-1
image = linode/alpine3.16
authorized_users = cli-dev"""

    base_url = ""

    def test_fish_completion(self):
        """
        Test if the fish completion renders correctly
        """
        conf = configuration.CLIConfig(self.base_url)
        m = mock_open(read_data=self.mock_config_file)
        with patch('linodecli.configuration.helpers.open', m, create=True):
            conf.used_env_token = False
            print(conf.get_token())
