#!/usr/local/bin/python3
import pytest

from linodecli import arg_helpers

class TestArgParsing:

    # arg_helpers.register_plugin(module, config, ops)
    def test_register_plugin_success(self, mocker, module_mocker, mocked_config):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "successfully!" in msg
        assert code == 0

    def test_register_plugin_no_mod(self, mocker, mocked_config):
        mocker.patch("linodecli.args.import_module", side_effect=ImportError())
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "not installed" in msg
        assert code == 10

    def test_register_plugin_no_name(self, mocker, module_mocker, mocked_config):
        del module_mocker.PLUGIN_NAME
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "missing PLUGIN_NAME" in msg
        assert code == 11

    def test_register_plugin_no_call(self, mocker, module_mocker, mocked_config):
        del module_mocker.call
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "missing call" in msg
        assert code == 11

    def test_register_plugin_in_ops(self, mocker, module_mocker, mocked_config):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        msg, code = arg_helpers.register_plugin("a", mocked_config, ["testing.plugin"])
        assert "conflicts with CLI operation" in msg
        assert code == 12

    def test_register_plugin_in_available_local(self, mocker, module_mocker, mocked_config):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        mocker.patch("linodecli.args.plugins.available_local", ["testing.plugin"])
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "conflicts with internal CLI plugin" in msg
        assert code == 13

    def test_register_plugin_re_register(self, mocker, module_mocker, mocked_config):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        mocker.patch("linodecli.args.plugins.available", return_value=["testing.plugin"])
        mocker.patch("linodecli.args.input", lambda _: "y")
        mocked_config.config.set("DEFAULT", "plugin-name-testing.plugin", "temp")
        mocked_config.config.set("DEFAULT", "registered-plugins", "testing.plugin")
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "successfully!" in msg
        assert code == 0

    def test_register_plugin_re_register_no(self, mocker, module_mocker, mocked_config):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        mocker.patch("linodecli.args.plugins.available", return_value=["testing.plugin"])
        mocker.patch("linodecli.args.input", lambda _: "n")
        mocked_config.config.set("DEFAULT", "plugin-name-testing.plugin", "temp")
        mocked_config.config.set("DEFAULT", "registered-plugins", "testing.plugin")
        msg, code = arg_helpers.register_plugin("a", mocked_config, {})
        assert "Registration aborted." in msg
        assert code == 0

    # arg_helpers.remove_plugin(plugin_name, config)
    def test_remove_plugin_success(self, mocker, mocked_config):
        mocker.patch("linodecli.args.plugins.available", return_value=["testing.plugin"])
        mocked_config.config.set("DEFAULT", "registered-plugins", "testing.plugin")
        mocked_config.config.set("DEFAULT", "plugin-name-testing.plugin", "temp")
        msg, code = arg_helpers.remove_plugin("testing.plugin", mocked_config)
        assert "removed" in msg
        assert code == 0

    def test_remove_plugin_in_available_local(self, mocker, mocked_config):
        mocker.patch("linodecli.args.plugins.available_local", ["testing.plugin"])
        msg, code = arg_helpers.remove_plugin("testing.plugin", mocked_config)
        assert "cannot be removed" in msg
        assert code == 13

    def test_remove_plugin_not_available(self, mocked_config):
        msg, code = arg_helpers.remove_plugin("testing.plugin", mocked_config)
        assert "not a registered plugin" in msg
        assert code == 14

    # arg_helpers.help_with_ops(ops, config)
    def test_help_with_ops(self, capsys, mocked_config):
        mock_ops = {"testkey1": "testvalue1"}
        arg_helpers.help_with_ops(mock_ops, mocked_config)
        captured = capsys.readouterr()
        assert "testkey1" in captured.out

    def test_help_with_ops_with_plugins(self, capsys, mocker, mocked_config):
        mock_ops = {"testkey1": "testvalue1"}
        mocker.patch("linodecli.args.plugins.available", return_value=["testing.plugin"])
        arg_helpers.help_with_ops(mock_ops, mocked_config)
        captured = capsys.readouterr()
        assert "testing.plugin" in captured.out

    # arg_helpers.action_help(cli, command, action)
    def test_action_help_value_error(self, capsys, mock_cli):
        arg_helpers.action_help(mock_cli, None, None)
        captured = capsys.readouterr()
        assert not captured.out

    def test_action_help_post_method(self, capsys, mocker, mock_cli):
        mocked_ops = mocker.MagicMock()
        mocked_ops.summary = "test summary"
        mocked_ops.docs_url = "https://website.com/endpoint"
        mocked_ops.method = "post"

        mocked_args = mocker.MagicMock()
        mocked_arg_helpers.required = True
        mocked_args.path = "path"
        mocked_args.description = "test description"

        mocked_ops.args = [mocked_args]

        mock_cli.find_operation = mocker.Mock(return_value=mocked_ops)

        arg_helpers.action_help(mock_cli, "command", "action")
        captured = capsys.readouterr()
        assert "test summary" in captured.out
        assert "API Documentation" in captured.out
        assert "https://website.com/endpoint" in captured.out
        assert "Arguments" in captured.out
        assert "test description" in captured.out
        assert "(required)" in captured.out
        assert "filter results" not in captured.out

    def test_action_help_get_method(self, capsys, mocker, mock_cli):
        mocked_ops = mocker.MagicMock()
        mocked_ops.summary = "test summary"
        mocked_ops.docs_url = "https://website.com/endpoint"
        mocked_ops.method = "get"
        mocked_ops.action = "list"
        mocked_ops.args = None

        mock_attr = mocker.MagicMock()
        mock_attr.filterable = True
        mock_attr.name = "filtername"
        mocked_ops.response_model.attrs = [mock_attr]

        mock_cli.find_operation = mocker.Mock(return_value=mocked_ops)

        arg_helpers.action_help(mock_cli, "command", "action")
        captured = capsys.readouterr()
        assert "test summary" in captured.out
        assert "API Documentation" in captured.out
        assert "https://website.com/endpoint" in captured.out
        assert "Arguments" not in captured.out
        assert "filter results" in captured.out
        assert "filtername" in captured.out

    def test_bake_command_bad_website(self, capsys, mocker, mock_cli):
        with pytest.raises(SystemExit) as ex:
            arg_helpers.bake_command(mock_cli, "https://website.com")
        captured = capsys.readouterr()
        assert ex.value.code == 2
        assert "Request failed to https://website.com" in captured.out

    def test_bake_command_good_website(self, capsys, mocker, mock_cli):
        mock_cli.bake = print
        mocker.patch("linodecli.completion.bake_completions")

        mock_res = mocker.MagicMock()
        mock_res.status_code = 200
        mock_res.content = "yaml loaded"
        mocker.patch("requests.get", return_value=mock_res)
        mocker.patch("yaml.safe_load", return_value=mock_res.content)

        arg_helpers.bake_command(mock_cli, "realwebsite")
        captured = capsys.readouterr()
        assert "yaml loaded" in captured.out

    def test_bake_command_good_file(self, capsys, mocker, mock_cli):
        mock_cli.bake = print
        mocker.patch("linodecli.completion.bake_completions")
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("yaml.safe_load", return_value="yaml loaded")

        arg_helpers.bake_command(mock_cli, "real/file")
        captured = capsys.readouterr()
        assert "yaml loaded" in captured.out
