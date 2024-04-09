#!/usr/local/bin/python3
"""
Unit tests for linodecli.configuration
"""
import argparse
import contextlib
import io
import os
import sys
from unittest.mock import call, mock_open, patch

import pytest
import requests_mock

from linodecli import configuration
from linodecli.configuration import (
    _bool_input,
    _default_text_input,
    _default_thing_input,
)


class TestConfiguration:
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

        assert conf.default_username() == "cli-dev"

        conf.config.remove_option("DEFAULT", "default-user")
        assert conf.default_username() == ""

    def test_set_user(self):
        """
        Test CLIConfig.set_user({username})
        """
        conf = self._build_test_config()

        f = io.StringIO()

        with pytest.raises(SystemExit) as err:
            with contextlib.redirect_stdout(f):
                conf.set_user("bad_user")

        assert err.value.code == 1
        assert "not configured" in f.getvalue()

        conf.set_user("cli-dev2")
        assert conf.username == "cli-dev2"

    def test_remove_user(self):
        """
        Test CLIConfig.remove_user({username}) with default username
        """
        conf = self._build_test_config()

        f = io.StringIO()

        with pytest.raises(SystemExit) as err:
            with contextlib.redirect_stdout(f):
                conf.remove_user("cli-dev")

        assert "default user!" in f.getvalue()
        assert err.value.code == 1

        with patch("linodecli.configuration.open", mock_open()):
            conf.remove_user("cli-dev2")
        assert conf.config.has_section("cli-dev2") is False

    def test_print_users(self):
        """
        Test CLIConfig.print_users()
        """
        conf = self._build_test_config()

        f = io.StringIO()

        with pytest.raises(SystemExit) as err:
            with contextlib.redirect_stdout(f):
                conf.print_users()

        assert err.value.code == 0
        assert "*  cli-dev" in f.getvalue()

    def test_set_default_user(self):
        """
        Test CLIConfig.set_default_user({username})
        """
        conf = self._build_test_config()

        f = io.StringIO()
        with pytest.raises(SystemExit) as err:
            with contextlib.redirect_stdout(f):
                conf.set_default_user("bad_user")

        assert err.value.code == 1
        assert "not configured" in f.getvalue()

        with patch("linodecli.configuration.open", mock_open()):
            conf.set_default_user("cli-dev2")
        assert conf.config.get("DEFAULT", "default-user") == "cli-dev2"

    def test_get_token(self):
        """
        Test CLIConfig.get_token()
        """
        conf = self._build_test_config()
        conf.used_env_token = False
        assert conf.get_token() == self.test_token

    def test_get_value(self):
        """
        Test CLIConfig.get_value({key})
        """
        conf = self._build_test_config()
        assert conf.get_value("notakey") == None
        assert conf.get_value("region") == "us-east"

    def test_plugin_set_value(self):
        """
        Test CLIConfig.plugin_set_value({key}, {value})
        """
        conf = self._build_test_config()
        with pytest.raises(RuntimeError):
            conf.plugin_set_value("anykey", "anyvalue")

        conf.running_plugin = "testplugin"

        conf.plugin_set_value("testkey", "newvalue")
        actual = conf.config.get("cli-dev", "plugin-testplugin-testkey")
        assert actual == "newvalue"

    def test_plugin_get_value(self):
        """
        Test CLIConfig.plugin_get_value({key})
        """
        conf = self._build_test_config()
        with pytest.raises(RuntimeError):
            conf.plugin_get_value("anykey")

        conf.running_plugin = "testplugin"

        actual = conf.plugin_get_value("badkey")
        assert actual == None

        actual = conf.plugin_get_value("testkey")
        assert actual == "plugin-test-value"

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

        assert "--no-defaults" in f.getvalue()
        assert result.get("newkey") == "newvalue"
        assert result.get("testkey") == "testvalue"
        assert isinstance(result.get("authorized_users"), list)
        assert result.get("plugin-testplugin-testkey") is None

        f = io.StringIO()
        sys.argv.append("--suppress-warnings")
        with contextlib.redirect_stdout(f):
            result = vars(conf.update(ns, None))
        sys.argv.remove("--suppress-warnings")

        assert "--no-defaults" not in f.getvalue()

    def test_write_config(self):
        """
        Test CLIConfig.write_config()
        """
        conf = self._build_test_config()

        conf.config.set("cli-dev", "type", "newvalue")
        m = mock_open()
        with patch("builtins.open", m):
            conf.write_config()
        assert call("type = newvalue\n") in m().write.call_args_list

    def test_configure_no_default_terminal(self):
        """
        Test CLIConfig.configure() with
        no default user, no environment variables, and no browser
        """
        conf = configuration.CLIConfig(self.base_url, skip_config=True)

        answers = iter(
            [
                "1",
                "1",
                "1",
                "1",
                "1",
                "1",
                "y",
                "foobar.linode.com",
                "v4beta",
                "https",
            ]
        )

        def mock_input(prompt):
            if "token" in prompt.lower():
                return "test-token"
            return next(answers)

        with (
            patch("os.chmod", lambda a, b: None),
            patch("linodecli.configuration.open", mock_open()),
            patch("builtins.input", mock_input),
            contextlib.redirect_stdout(io.StringIO()),
            patch(
                "linodecli.configuration.config._check_browsers", lambda: False
            ),
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
                f"{self.base_url}/account/users",
                json={"data": [{"username": "cli-dev", "ssh_keys": "testkey"}]},
            )
            conf.configure()

        assert conf.get_value("type") == "test-type"
        assert conf.get_value("token") == "test-token"
        assert conf.get_value("image") == "test-image"
        assert conf.get_value("region") == "test-region"
        assert conf.get_value("authorized_users") == "cli-dev"
        assert conf.get_value("api_host") == "foobar.linode.com"
        assert conf.get_value("api_version") == "v4beta"
        assert conf.get_value("api_scheme") == "https"

    def test_configure_default_terminal(self):
        """
        Test CLIConfig.configure() with
        a default user, token in environment, and no browser
        """
        conf = configuration.CLIConfig(self.base_url, skip_config=True)

        answers = iter(["1", "1", "1", "1", "1", "1", "n"])

        def mock_input(prompt):
            if not prompt:
                return None
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
                f"{self.base_url}/account/users",
                json={"data": [{"username": "cli-dev", "ssh_keys": "testkey"}]},
            )
            conf.configure()

        assert conf.get_value("type") == "test-type"
        assert conf.get_value("image") == "test-image"
        assert conf.get_value("region") == "test-region"
        assert conf.get_value("authorized_users") == "cli-dev"
        assert conf.config.get("DEFAULT", "default-user") == "DEFAULT"

    def test_default_thing_input_no_current(self, monkeypatch):
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("1\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _default_thing_input(
                "foo\n", ["foo", "bar"], "prompt text", "error text"
            )

        output_lines = stdout_buf.getvalue().splitlines()

        assert output_lines == [
            "",
            "foo",
            "  Choices are:",
            " 1 - foo",
            " 2 - bar",
            "",
            "prompt text",
        ]

        assert result == "foo"

    def test_default_thing_input_skip(self, monkeypatch):
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _default_thing_input(
                "foo\n",
                ["foo", "bar"],
                "prompt text",
                "error text",
                current_value="foo",
            )

        output_lines = stdout_buf.getvalue().splitlines()

        print(output_lines)

        assert output_lines == [
            "",
            "foo",
            "  Choices are:",
            " 1 - No Default",
            " 2 - foo",
            " 3 - bar",
            "",
            "prompt text",
        ]

        assert result == "foo"

    def test_default_thing_input_no_default(self, monkeypatch):
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("1\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _default_thing_input(
                "foo\n",
                ["foo", "bar"],
                "prompt text",
                "error text",
                current_value="foo",
            )

        output_lines = stdout_buf.getvalue().splitlines()

        print(output_lines)

        assert output_lines == [
            "",
            "foo",
            "  Choices are:",
            " 1 - No Default",
            " 2 - foo",
            " 3 - bar",
            "",
            "prompt text",
        ]

        assert result is None

    def test_default_thing_input_valid(self, monkeypatch):
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("3\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _default_thing_input(
                "foo\n",
                ["foo", "bar"],
                "prompt text",
                "error text",
                current_value="foo",
            )

        output_lines = stdout_buf.getvalue().splitlines()

        print(output_lines)

        assert output_lines == [
            "",
            "foo",
            "  Choices are:",
            " 1 - No Default",
            " 2 - foo",
            " 3 - bar",
            "",
            "prompt text",
        ]

        assert result == "bar"

    def test_default_thing_input_valid_no_current(self, monkeypatch):
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("3\n1\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _default_thing_input(
                "foo\n",
                ["foo", "bar"],
                "prompt text",
                "error text",
            )

        output = stdout_buf.getvalue()

        assert "error text" in output

        assert result == "foo"

    def test_default_thing_input_out_of_range(self, monkeypatch):
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("4\n2\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _default_thing_input(
                "foo\n",
                ["foo", "bar"],
                "prompt text",
                "error text",
                current_value="foo",
            )

        output = stdout_buf.getvalue()
        assert "error text" in output

        assert result == "foo"

    def test_default_text_input_optional(self, monkeypatch):
        # No value specified
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _default_text_input(
                "foo",
                optional=True,
            )

        assert "foo (Optional)" in stdout_buf.getvalue()
        assert result is None

        # Value specified
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("foobar\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _default_text_input(
                "foo",
                optional=True,
            )

        assert "foo (Optional)" in stdout_buf.getvalue()
        assert result == "foobar"

    def test_default_text_input_default(self, monkeypatch):
        # No value specified
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _default_text_input(
                "foo",
                default="barfoo",
            )

        assert "foo (Default barfoo)" in stdout_buf.getvalue()
        assert result == "barfoo"

        # Value specified
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("foobar\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _default_text_input(
                "foo",
                default="barfoo",
                optional=True,
            )

        assert "foo (Default barfoo)" in stdout_buf.getvalue()
        assert result == "foobar"

    def test_default_text_input_validation(self, monkeypatch):
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("foo\nbar\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _default_text_input(
                "foo",
                validator=lambda v: None if v == "bar" else "error text",
            )

        assert "error text" in stdout_buf.getvalue()
        assert result == "bar"

    def test_bool_input(self, monkeypatch):
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("w\nn\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _bool_input("foo", default=True)

        output = stdout_buf.getvalue()
        assert "foo [y/N]: " in output
        assert "Invalid input. Please input either y or n." in output
        assert not result

    def test_bool_input_default(self, monkeypatch):
        stdout_buf = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO("\n"))

        with contextlib.redirect_stdout(stdout_buf):
            result = _bool_input("foo", default=True)

        output = stdout_buf.getvalue()
        assert "foo [y/N]: " in output
        assert result
