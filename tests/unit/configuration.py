#!/usr/local/bin/python3
"""
Unit tests for linodecli.configuration
"""
import argparse
import contextlib
import io
import os
import sys
import unittest
from unittest.mock import call, mock_open, patch

import requests_mock

from linodecli import configuration


class ConfigurationTests(unittest.TestCase):
    """
    Unit tests for linodecli.configuration
    """

    base_url = "https://linode-test.com"
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
mysql_engine = mysql/8.0.26

[cli-dev2]
token = {test_token}2
region = us-east
type = g6-nanode-1
image = linode/alpine3.16
authorized_users = cli-dev2
mysql_engine = mysql/8.0.26"""

    def _build_test_config(self, config=mock_config_file, base_url=base_url):
        """
        Helper to generate config with mock data
        """
        conf = None
        with patch(
            "linodecli.configuration.helpers.configparser.open",
            mock_open(read_data=config),
        ):
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

        with patch("linodecli.configuration.open", mock_open()):
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

        with patch("linodecli.configuration.open", mock_open()):
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

    def test_update(self):
        """
        Test CLIConfig.update({namespace}, {allowed_defaults})
        """
        conf = self._build_test_config()

        parser = argparse.ArgumentParser()
        parser.add_argument("--newkey")
        parser.add_argument("--testkey")
        parser.add_argument("--authorized_users")
        parser.add_argument("--plugin-testplugin-testkey")
        parser.add_argument("--engine")
        ns = parser.parse_args(
            ["--testkey", "testvalue", "--engine", "mysql/new-test-engine"]
        )

        conf.username = "tester"
        conf.config.add_section("tester")
        conf.config.set("tester", "token", "testtoken")
        conf.config.set("tester", "newkey", "newvalue")
        conf.config.set("tester", "authorized_users", "tester")
        conf.config.set("tester", "plugin-testplugin-testkey", "plugin-value")
        conf.config.set("tester", "mysql_engine", "mysql/default-test-engine")
        allowed_defaults = [
            "newkey",
            "authorized_users",
            "plugin-testplugin-testkey",
            "engine",
        ]

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            result = vars(conf.update(ns, allowed_defaults))

        self.assertTrue("--no-defaults" in f.getvalue())
        self.assertEqual(result.get("newkey"), "newvalue")
        self.assertEqual(result.get("testkey"), "testvalue")
        self.assertTrue(isinstance(result.get("authorized_users"), list))
        self.assertFalse(result.get("plugin-testplugin-testkey"))

        f = io.StringIO()
        sys.argv.append("--suppress-warnings")
        with contextlib.redirect_stdout(f):
            result = vars(conf.update(ns, None))
        sys.argv.remove("--suppress-warnings")

        self.assertFalse("--no-defaults" in f.getvalue())

        # test that update default engine value correctly when creating database
        create_db_action = "mysql-create"
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            result = vars(conf.update(ns, allowed_defaults, create_db_action))
        self.assertEqual(result.get("engine"), "mysql/new-test-engine")

    def test_write_config(self):
        """
        Test CLIConfig.write_config()
        """
        conf = self._build_test_config()

        conf.config.set("cli-dev", "type", "newvalue")
        m = mock_open()
        with patch("builtins.open", m):
            conf.write_config()
        self.assertIn(call("type = newvalue\n"), m().write.call_args_list)

    def test_configure_no_default_terminal(self):
        """
        Test CLIConfig.configure() with
        no default user, no environment variables, and no browser
        """
        conf = configuration.CLIConfig(self.base_url, skip_config=True)

        def mock_input(prompt):
            answers = (a for a in ["1", "1", "1", "1"])
            if "token" in prompt.lower():
                return "test-token"
            return next(answers)

        with (
            patch("os.chmod", lambda a, b: None),
            patch("linodecli.configuration.open", mock_open()),
            patch("builtins.input", mock_input),
            contextlib.redirect_stdout(io.StringIO()),
            patch("linodecli.configuration._check_browsers", lambda: False),
            patch.dict(os.environ, {}, clear=True),
            requests_mock.Mocker() as m,
        ):
            m.get(f"{self.base_url}/profile", json={"username": "cli-dev"})
            m.get(f"{self.base_url}/profile/grants", status_code=204)
            m.get(
                f"{self.base_url}/regions",
                json={"data": [{"id": "test-region"}]},
            )
            m.get(
                f"{self.base_url}/linode/types",
                json={"data": [{"id": "test-type"}]},
            )
            m.get(
                f"{self.base_url}/images", json={"data": [{"id": "test-image"}]}
            )
            m.get(
                f"{self.base_url}/databases/engines",
                json={
                    "data": [
                        {"id": "mysql/test-engine", "engine": "mysql"},
                        {
                            "id": "postgresql/test-engine",
                            "engine": "postgresql",
                        },
                    ]
                },
            )
            m.get(
                f"{self.base_url}/account/users",
                json={"data": [{"username": "cli-dev", "ssh_keys": "testkey"}]},
            )
            conf.configure()

        self.assertEqual(conf.get_value("type"), "test-type")
        self.assertEqual(conf.get_value("token"), "test-token")
        self.assertEqual(conf.get_value("image"), "test-image")
        self.assertEqual(conf.get_value("region"), "test-region")
        self.assertEqual(conf.get_value("authorized_users"), "cli-dev")
        # make sure that we set the default engine value according to type of database
        self.assertEqual(conf.get_value("mysql_engine"), "mysql/test-engine")
        self.assertEqual(
            conf.get_value("postgresql_engine"), "postgresql/test-engine"
        )

    def test_configure_default_terminal(self):
        """
        Test CLIConfig.configure() with
        a default user, token in environment, and no browser
        """
        conf = configuration.CLIConfig(self.base_url, skip_config=True)

        def mock_input(prompt):
            if not prompt:
                return None
            answers = (a for a in ["1", "1", "1", "1"])
            return next(answers)

        with (
            patch("linodecli.configuration.open", mock_open()),
            patch("os.chmod", lambda a, b: None),
            patch("builtins.input", mock_input),
            contextlib.redirect_stdout(io.StringIO()),
            patch("linodecli.configuration._check_browsers", lambda: False),
            patch.dict(os.environ, {"LINODE_CLI_TOKEN": "test-token"}),
            requests_mock.Mocker() as m,
        ):
            m.get(f"{self.base_url}/profile", json={"username": "cli-dev"})
            m.get(f"{self.base_url}/profile/grants", status_code=204)
            m.get(
                f"{self.base_url}/regions",
                json={"data": [{"id": "test-region"}]},
            )
            m.get(
                f"{self.base_url}/linode/types",
                json={"data": [{"id": "test-type"}]},
            )
            m.get(
                f"{self.base_url}/images", json={"data": [{"id": "test-image"}]}
            )
            m.get(
                f"{self.base_url}/databases/engines",
                json={
                    "data": [
                        {"id": "mysql/test-engine", "engine": "mysql"},
                        {
                            "id": "postgresql/test-engine",
                            "engine": "postgresql",
                        },
                    ]
                },
            )
            m.get(
                f"{self.base_url}/account/users",
                json={"data": [{"username": "cli-dev", "ssh_keys": "testkey"}]},
            )
            conf.configure()

        self.assertEqual(conf.get_value("type"), "test-type")
        self.assertEqual(conf.get_value("image"), "test-image")
        self.assertEqual(conf.get_value("region"), "test-region")
        self.assertEqual(conf.get_value("authorized_users"), "cli-dev")
        self.assertEqual(conf.config.get("DEFAULT", "default-user"), "DEFAULT")
        # make sure that we set the default engine value according to type of database
        self.assertEqual(conf.get_value("mysql_engine"), "mysql/test-engine")
        self.assertEqual(
            conf.get_value("postgresql_engine"), "postgresql/test-engine"
        )
