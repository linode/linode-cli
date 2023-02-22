from linodecli import args

class TestArgParsing:

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
        mocker.patch("linodecli.args.plugins.available_local", return_value=["testing.plugin"])
        msg, code = args.register_plugin("a", mocked_config, {})
        assert "conflicts with internal CLI plugin" in msg
        assert code == 13
