from linodecli import args

class TestArgParsing:

    # args.register_plugin(module, config, ops)
    def test_register_plugin_success(self, mocker, module_mocker, mocked_config):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        msg, code = args.register_plugin("a", mocked_config, {})
        assert "successfully!" in msg
        assert code == 0

    def test_register_plugin_no_mod(self, mocker, mocked_config):
        mocker.patch("linodecli.args.import_module", side_effect=ImportError())
        msg, code = args.register_plugin("a", mocked_config, {})
        assert "not installed" in msg
        assert code == 10

    def test_register_plugin_no_name(self, mocker, module_mocker, mocked_config):
        del module_mocker.PLUGIN_NAME
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        msg, code = args.register_plugin("a", mocked_config, {})
        assert "missing PLUGIN_NAME" in msg
        assert code == 11

    def test_register_plugin_no_call(self, mocker, module_mocker, mocked_config):
        del module_mocker.call
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        msg, code = args.register_plugin("a", mocked_config, {})
        assert "missing call" in msg
        assert code == 11

    def test_register_plugin_in_ops(self, mocker, module_mocker, mocked_config):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        msg, code = args.register_plugin("a", mocked_config, ["testing.plugin"])
        assert "conflicts with CLI operation" in msg
        assert code == 12

    def test_register_plugin_in_available_local(self, mocker, module_mocker, mocked_config):
        module_mocker.call = print
        module_mocker.PLUGIN_NAME = "testing.plugin"
        mocker.patch("linodecli.args.import_module", return_value=module_mocker)
        mocker.patch("linodecli.args.plugins.available_local", ["testing.plugin"])
        msg, code = args.register_plugin("a", mocked_config, {})
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
        msg, code = args.register_plugin("a", mocked_config, {})
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
        msg, code = args.register_plugin("a", mocked_config, {})
        assert "Registration aborted." in msg
        assert code == 0

    # args.remove_plugin(plugin_name, config)
    def test_remove_plugin_success(self, mocker, mocked_config):
        mocker.patch("linodecli.args.plugins.available", return_value=["testing.plugin"])
        mocked_config.config.set("DEFAULT", "registered-plugins", "testing.plugin")
        mocked_config.config.set("DEFAULT", "plugin-name-testing.plugin", "temp")
        msg, code = args.remove_plugin("testing.plugin", mocked_config)
        assert "removed" in msg
        assert code == 0

    def test_remove_plugin_in_available_local(self, mocker, mocked_config):
        mocker.patch("linodecli.args.plugins.available_local", ["testing.plugin"])
        msg, code = args.remove_plugin("testing.plugin", mocked_config)
        assert "cannot be removed" in msg
        assert code == 13

    def test_remove_plugin_not_available(self, mocked_config):
        msg, code = args.remove_plugin("testing.plugin", mocked_config)
        assert "not a registered plugin" in msg
        assert code == 14

    # args.help_with_ops(ops, config)
    def test_help_with_ops(self, capsys, mocked_config):
        mock_ops = {"testkey1": "testvalue1"}
        args.help_with_ops(mock_ops, mocked_config)
        captured = capsys.readouterr()
        assert "testkey1" in captured.out

    def test_help_with_ops_with_plugins(self, capsys, mocker, mocked_config):
        mock_ops = {"testkey1": "testvalue1"}
        mocker.patch("linodecli.args.plugins.available", return_value=["testing.plugin"])
        args.help_with_ops(mock_ops, mocked_config)
        captured = capsys.readouterr()
        assert "testing.plugin" in captured.out

    # args.action_help(cli, command, action)
    def test_action_help_value_error(self, capsys, mocker, mock_cli):
        mocker.patch("linodecli.args.action_help.cli.find_operation", side_effect=ValueError())
        args.action_help(mock_cli, None, None)
        captured = capsys.readouterr()
        assert not captured.out
