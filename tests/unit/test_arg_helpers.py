#!/usr/local/bin/python3
import pytest

from linodecli import arg_helpers


class TestArgParsing:
    # arg_helpers.register_plugin(module, config, ops)
    def test_register_plugin_success(
        self, mocker, module_mocker, mocked_config
    ):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch(
            "linodecli.arg_helpers.import_module", return_value=module_mocker
        )
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "successfully!" in msg
        assert code == 0

    def test_register_plugin_no_mod(self, mocker, mocked_config):
        mocker.patch(
            "linodecli.arg_helpers.import_module", side_effect=ImportError()
        )
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "not installed" in msg
        assert code == 10

    def test_register_plugin_no_name(
        self, mocker, module_mocker, mocked_config
    ):
        del module_mocker.PLUGIN_NAME
        mocker.patch(
            "linodecli.arg_helpers.import_module", return_value=module_mocker
        )
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "missing PLUGIN_NAME" in msg
        assert code == 11

    def test_register_plugin_no_call(
        self, mocker, module_mocker, mocked_config
    ):
        del module_mocker.call
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch(
            "linodecli.arg_helpers.import_module", return_value=module_mocker
        )
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "missing call" in msg
        assert code == 11

    def test_register_plugin_in_ops(self, mocker, module_mocker, mocked_config):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch(
            "linodecli.arg_helpers.import_module", return_value=module_mocker
        )
        msg, code = arg_helpers.register_plugin(
            "a", mocked_config, ["testing.plugin"]
        )
        assert "conflicts with CLI operation" in msg
        assert code == 12

    def test_register_plugin_in_available_local(
        self, mocker, module_mocker, mocked_config
    ):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch(
            "linodecli.arg_helpers.import_module", return_value=module_mocker
        )
        mocker.patch(
            "linodecli.arg_helpers.plugins.AVAILABLE_LOCAL", ["testing.plugin"]
        )
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "conflicts with internal CLI plugin" in msg
        assert code == 13

    def test_register_plugin_re_register(
        self, mocker, module_mocker, mocked_config
    ):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch(
            "linodecli.arg_helpers.import_module", return_value=module_mocker
        )
        mocker.patch(
            "linodecli.arg_helpers.plugins.available",
            return_value=["testing.plugin"],
        )
        mocker.patch("linodecli.arg_helpers.input", lambda _: "y")
        mocked_config.config.set(
            "DEFAULT", "plugin-name-testing.plugin", "temp"
        )
        mocked_config.config.set(
            "DEFAULT", "registered-plugins", "testing.plugin"
        )
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "successfully!" in msg
        assert code == 0

    def test_register_plugin_re_register_no(
        self, mocker, module_mocker, mocked_config
    ):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch(
            "linodecli.arg_helpers.import_module", return_value=module_mocker
        )
        mocker.patch(
            "linodecli.arg_helpers.plugins.available",
            return_value=["testing.plugin"],
        )
        mocker.patch("linodecli.arg_helpers.input", lambda _: "n")
        mocked_config.config.set(
            "DEFAULT", "plugin-name-testing.plugin", "temp"
        )
        mocked_config.config.set(
            "DEFAULT", "registered-plugins", "testing.plugin"
        )
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "Registration aborted." in msg
        assert code == 0

    # arg_helpers.remove_plugin(plugin_name, config)
    def test_remove_plugin_success(self, mocker, mocked_config):
        mocker.patch(
            "linodecli.arg_helpers.plugins.available",
            return_value=["testing.plugin"],
        )
        mocked_config.config.set(
            "DEFAULT", "registered-plugins", "testing.plugin"
        )
        mocked_config.config.set(
            "DEFAULT", "plugin-name-testing.plugin", "temp"
        )
        msg, code = arg_helpers.remove_plugin("testing.plugin", mocked_config)
        assert "removed" in msg
        assert code == 0

    def test_remove_plugin_in_available_local(self, mocker, mocked_config):
        mocker.patch(
            "linodecli.arg_helpers.plugins.AVAILABLE_LOCAL", ["testing.plugin"]
        )
        msg, code = arg_helpers.remove_plugin("testing.plugin", mocked_config)
        assert "cannot be removed" in msg
        assert code == 13

    def test_remove_plugin_not_available(self, mocked_config):
        msg, code = arg_helpers.remove_plugin("testing.plugin", mocked_config)
        assert "not a registered plugin" in msg
        assert code == 14

    def test_bake_command_bad_website(self, capsys, mock_cli):
        with pytest.raises(SystemExit) as ex:
            arg_helpers.bake_command(mock_cli, "https://website.com")
        captured = capsys.readouterr()
        assert ex.value.code == 2
        assert "Request failed to https://website.com" in captured.out
