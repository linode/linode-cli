#!/usr/local/bin/python3
"""
Unit tests for linodecli.configuration
"""
import io
import sys
import argparse
import contextlib

import unittest
from unittest.mock import patch, mock_open

from linodecli import configuration

class ConfigurationTests(unittest.TestCase):
    """
    Unit tests for linodecli.configuration
    """

    base_url = ""
    test_token = "cli-dev-token"
    mock_config_file = f"""[DEFAULT]
default-user = cli-dev

[cli-dev]
token = {test_token}
region = us-east
type = g6-nanode-1
image = linode/alpine3.16
plugin-testplugin-testkey = plugin-test-value
authorized_users = cli-dev

[cli-dev2]
token = {test_token}2
region = us-east
type = g6-nanode-1
image = linode/alpine3.16
authorized_users = cli-dev2"""

    def _build_test_config(self, config=mock_config_file, base_url=base_url):
        """
        Helper to generate config with mock data
        """
        conf = None
        with patch('linodecli.configuration.helpers.configparser.open',
                   mock_open(read_data=config)):
            conf = configuration.CLIConfig(base_url)
        return conf

    def test_default_username(self):
        """
        Test CLIConfig.default_username() with no default user
        """
        conf = self._build_test_config()

        self.assertEqual(conf.default_username(), "cli-dev")

        conf.config.remove_option("DEFAULT", "default-user")
        self.assertEqual(conf.default_username(), "")

    def test_set_user(self):
        """
        Test CLIConfig.set_user({username})
        """
        conf = self._build_test_config()

        f = io.StringIO()
        with self.assertRaises(SystemExit) as cm, contextlib.redirect_stdout(f):
            conf.set_user("bad_user")
        self.assertEqual(cm.exception.code, 1)
        self.assertTrue("not configured" in f.getvalue())

        conf.set_user("cli-dev2")
        self.assertEqual(conf.username, "cli-dev2")

    def test_remove_user(self):
        """
        Test CLIConfig.remove_user({username}) with default username
        """
        conf = self._build_test_config()

        f = io.StringIO()
        with self.assertRaises(SystemExit) as cm, contextlib.redirect_stdout(f):
            conf.remove_user("cli-dev")
        self.assertEqual(cm.exception.code, 1)
        self.assertTrue("default user!" in f.getvalue())

        with patch('linodecli.configuration.open', mock_open()):
            conf.remove_user("cli-dev2")
        self.assertFalse(conf.config.has_section("cli-dev2"))

    def test_print_users(self):
        """
        Test CLIConfig.print_users()
        """
        conf = self._build_test_config()

        f = io.StringIO()
        with self.assertRaises(SystemExit) as cm, contextlib.redirect_stdout(f):
            conf.print_users()
        self.assertEqual(cm.exception.code, 0)
        self.assertTrue("*  cli-dev" in f.getvalue())

    def test_set_default_user(self):
        """
        Test CLIConfig.set_default_user({username})
        """
        conf = self._build_test_config()

        f = io.StringIO()
        with self.assertRaises(SystemExit) as cm, contextlib.redirect_stdout(f):
            conf.set_default_user("bad_user")
        self.assertEqual(cm.exception.code, 1)
        self.assertTrue("not configured!" in f.getvalue())

        with patch('linodecli.configuration.open', mock_open()):
            conf.set_default_user("cli-dev2")
        self.assertEqual(conf.config.get("DEFAULT", "default-user"), "cli-dev2")

    def test_get_token(self):
        """
        Test CLIConfig.get_token()
        """
        conf = self._build_test_config()
        conf.used_env_token = False
        self.assertEqual(conf.get_token(), self.test_token)

    def test_get_value(self):
        """
        Test CLIConfig.get_value({key})
        """
        conf = self._build_test_config()
        self.assertEqual(conf.get_value("notakey"), None)
        self.assertEqual(conf.get_value("region"), "us-east")

    def test_plugin_set_value(self):
        """
        Test CLIConfig.plugin_set_value({key}, {value})
        """
        conf = self._build_test_config()
        with self.assertRaises(RuntimeError):
            conf.plugin_set_value("anykey", "anyvalue")

        conf.running_plugin = "testplugin"

        conf.plugin_set_value("testkey", "newvalue")
        actual = conf.config.get("cli-dev", "plugin-testplugin-testkey")
        self.assertEqual(actual, "newvalue")

    def test_plugin_get_value(self):
        """
        Test CLIConfig.plugin_get_value({key})
        """
        conf = self._build_test_config()
        with self.assertRaises(RuntimeError):
            conf.plugin_get_value("anykey")

        conf.running_plugin = "testplugin"

        actual = conf.plugin_get_value("badkey")
        self.assertEqual(actual, None)

        actual = conf.plugin_get_value("testkey")
        self.assertEqual(actual, "plugin-test-value")

    def test_update_namespace(self):
        """
        Test CLIConfig.update_namespace({namespace}, {new_dict})
        """
        conf = self._build_test_config()

        parser = argparse.ArgumentParser()
        parser.add_argument('--newkey')
        parser.add_argument('--testkey')
        parser.add_argument('--listkey')
        parser.add_argument('--plugin-testplugin-testkey')
        ns = parser.parse_args(['--testkey', 'testvalue'])

        update_dict = {
            'newkey': 'newvalue',
            'listkey': ['listvalue'],
            'plugin-testplugin-testkey': 'plugin-value',
        }

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            result = vars(conf.update_namespace(ns, update_dict))

        self.assertTrue("--no-defaults" in f.getvalue())
        self.assertEqual(result.get("newkey"), "newvalue")
        self.assertEqual(result.get("testkey"), "testvalue")
        self.assertTrue(isinstance(result.get("listkey"), list))
        self.assertFalse(result.get("plugin-testplugin-testkey"))

        f = io.StringIO()
        sys.argv.append("--suppress-warnings")
        with contextlib.redirect_stdout(f):
            result = vars(conf.update_namespace(ns, update_dict))
        sys.argv.remove("--suppress-warnings")

        self.assertFalse("--no-defaults" in f.getvalue())
