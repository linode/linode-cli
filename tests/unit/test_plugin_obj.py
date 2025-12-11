from pytest import CaptureFixture, MonkeyPatch

from linodecli import CLI, plugins
from linodecli.plugins import obj
from linodecli.plugins.obj import get_obj_args_parser, helpers, print_help


def test_print_help(mock_cli: CLI, capsys: CaptureFixture):
    parser = get_obj_args_parser()
    print_help(parser)
    captured_text = capsys.readouterr()
    assert parser.format_help() in captured_text.out
    assert (
        "See --help for individual commands for more information"
        in captured_text.out
    )


def test_helpers_denominate():
    assert helpers._denominate(0) == "0.0 KB"
    assert helpers._denominate(1) == "0.0 KB"
    assert helpers._denominate(12) == "0.01 KB"
    assert helpers._denominate(123) == "0.12 KB"
    assert helpers._denominate(1000) == "0.98 KB"

    assert helpers._denominate(1024) == "1.0 KB"
    assert helpers._denominate(1024**2) == "1.0 MB"
    assert helpers._denominate(1024**3) == "1.0 GB"
    assert helpers._denominate(1024**4) == "1.0 TB"
    assert helpers._denominate(1024**5) == "1024.0 TB"

    assert helpers._denominate(102400) == "100.0 KB"
    assert helpers._denominate(1024000) == "1000.0 KB"
    assert helpers._denominate((1024**2) // 10) == "102.4 KB"

    assert helpers._denominate(123456789) == "117.74 MB"
    assert helpers._denominate(1e23) == "90949470177.29 TB"


def test_obj_action_triggers_key_cleanup_and_deletes_stale_key(
    monkeypatch: MonkeyPatch,
):
    now = int(time.time())
    stale_timestamp = (
        now - 31 * 24 * 60 * 60
    )  # 31 days ago (assuming 30d lifespan)
    fresh_timestamp = now

    stale_key = {
        "id": "stale-id",
        "label": f"linode-cli-testuser@localhost-{stale_timestamp}",
        "access_key": "STALEKEY",
    }
    fresh_key = {
        "id": "fresh-id",
        "label": f"linode-cli-testuser@localhost-{fresh_timestamp}",
        "access_key": "FRESHKEY",
    }

    # Mocks for Linode CLI commands
    def call_operation_side_effect(resource, action, *args, **kwargs):
        if resource == "object-storage" and action == "keys-list":
            return 200, {"data": [stale_key, fresh_key]}

        if resource == "object-storage" and action == "keys-delete":
            return 200, {}

        if resource == "object-storage" and action == "keys-create":
            return 200, {"access_key": "NEWKEY", "secret_key": "NEWSECRET"}

        if resource == "account" and action == "view":
            return 200, {}

        return 200, {}

    # OBJ plugin & CLI config mocks
    with (
        patch("linodecli.plugins.obj.__init__.CLI") as MockCLI,
        patch.dict(
            obj.COMMAND_MAP,
            {
                # We don't want to actually execute any S3 operations
                "ls": lambda *args, **kwargs: None,
            },
        ),
    ):
        mock_client = MockCLI.return_value
        mock_client.call_operation.side_effect = call_operation_side_effect

        mock_client.config.plugin_get_value.side_effect = (
            lambda k, d=None, t=None: {
                "key-cleanup-enabled": True,
                "key-lifespan": "30d",
                "key-rotation-period": "10d",
                "key-cleanup-batch-size": 10,
            }.get(k, None)
        )

        mock_client.config.plugin_set_value.return_value = None
        mock_client.config.write_config.return_value = None

        # Execute the ls command
        obj.call(
            ["ls", "bucket"],
            plugins.PluginContext("12345", mock_client),
        )

        # Check that keys-delete was called for the stale key only
        delete_calls = [
            c
            for c in mock_client.call_operation.mock_calls
            if c[1][1] == "keys-delete"
        ]
        assert any(
            c[1][2][0] == "stale-id" for c in delete_calls
        ), "Stale key was not deleted"
        assert not any(
            c[1][2][0] == "fresh-id" for c in delete_calls
        ), "Fresh key should not be deleted"


def test_obj_action_triggers_key_rotation(
    monkeypatch: MonkeyPatch,
):
    now = int(time.time())
    # Key created 31 days ago, rotation period is 30 days
    old_timestamp = now - 60 * 60 * 24 * 31

    key_due_for_rotation = {
        "id": "rotate-id",
        "label": f"linode-cli-testuser@localhost-{old_timestamp}",
        "access_key": "ROTATEKEY",
    }

    # Mocks for Linode CLI commands
    def call_operation_side_effect(resource, action, *args, **kwargs):
        if resource == "object-storage" and action == "keys-list":
            return 200, {"data": [key_due_for_rotation]}

        if resource == "object-storage" and action == "keys-delete":
            return 200, {}

        if resource == "object-storage" and action == "keys-create":
            return 200, {"access_key": "NEWKEY", "secret_key": "NEWSECRET"}

        if resource == "account" and action == "view":
            return 200, {}

        return 200, {}

    # OBJ plugin & CLI config mocks
    with (
        patch("linodecli.plugins.obj.__init__.CLI") as MockCLI,
        patch.dict(
            obj.COMMAND_MAP,
            {
                # We don't want to actually execute any S3 operations
                "ls": lambda *args, **kwargs: None,
            },
        ),
    ):
        mock_client = MockCLI.return_value
        mock_client.call_operation.side_effect = call_operation_side_effect
        mock_client.config.plugin_set_value.return_value = None
        mock_client.config.write_config.return_value = None

        mock_options = {
            "access-key": "ROTATEKEY",
            "secret-key": "12345",
            "key-cleanup-enabled": True,
            "key-lifespan": "90d",
            "key-rotation-period": "30d",
            "key-cleanup-batch-size": 10,
        }

        mock_client.config.plugin_get_value.side_effect = (
            lambda k, d=None, t=None: mock_options.get(k, None)
        )

        # This test relies on the plugin updating the config
        mock_client.config.plugin_remove_option.side_effect = (
            lambda k, d=None, t=None: mock_options.pop(k, None)
        )

        obj.call(
            ["ls", "bucket"],
            plugins.PluginContext("12345", mock_client),
        )

        # Check that keys-create (rotation) was called
        create_calls = [
            c
            for c in mock_client.call_operation.mock_calls
            if c[1][1] == "keys-create"
        ]
        assert create_calls, "Key rotation (keys-create) was not triggered"

        # Check that keys-delete was called for the old key
        delete_calls = [
            c
            for c in mock_client.call_operation.mock_calls
            if c[1][1] == "keys-delete"
        ]
        assert any(
            c[1][2][0] == "rotate-id" for c in delete_calls
        ), "Old key was not deleted after rotation"


def test_obj_action_does_not_trigger_cleanup_if_recent(
    monkeypatch: MonkeyPatch,
):
    now = int(time.time())
    # Set last cleanup to 1 hour ago (less than 24h)
    last_cleanup = now - 60 * 60

    stale_timestamp = now - 31 * 24 * 60 * 60
    stale_key = {
        "id": "stale-id",
        "label": f"linode-cli-testuser@localhost-{stale_timestamp}",
        "access_key": "STALEKEY",
    }

    def call_operation_side_effect(resource, action, *args, **kwargs):
        if resource == "object-storage" and action == "keys-list":
            return 200, {"data": [stale_key]}

        if resource == "object-storage" and action == "keys-delete":
            return 200, {}

        if resource == "object-storage" and action == "keys-create":
            return 200, {"access_key": "NEWKEY", "secret_key": "NEWSECRET"}

        if resource == "account" and action == "view":
            return 200, {}

        return 200, {}

    with (
        patch("linodecli.plugins.obj.__init__.CLI") as MockCLI,
        patch.dict(
            obj.COMMAND_MAP,
            {
                # We don't want to actually execute any S3 operations
                "ls": lambda *args, **kwargs: None,
            },
        ),
    ):
        mock_client = MockCLI.return_value

        mock_client.call_operation.side_effect = call_operation_side_effect
        mock_client.config.plugin_set_value.return_value = None
        mock_client.config.write_config.return_value = None

        mock_client.config.plugin_get_value.side_effect = (
            lambda k, d=None, t=None: {
                "cluster": "us-mia-1",
                "key-cleanup-enabled": True,
                "key-lifespan": "30d",
                "key-rotation-period": "10d",
                "key-cleanup-batch-size": 10,
                "last-key-cleanup-timestamp": str(last_cleanup),
            }.get(k, None)
        )

        obj.call(
            ["ls", "bucket"],
            plugins.PluginContext("12345", mock_client),
        )

        # Check that keys-delete was NOT called
        delete_calls = [
            c
            for c in mock_client.call_operation.mock_calls
            if c[1][1] == "keys-delete"
        ]
        assert (
            not delete_calls
        ), "Cleanup should not be performed if it was done in the last 24 hours"


def test_obj_action_does_not_trigger_cleanup_if_disabled(
    monkeypatch: MonkeyPatch,
):
    now = int(time.time())
    stale_timestamp = now - 31 * 24 * 60 * 60
    stale_key = {
        "id": "stale-id",
        "label": f"linode-cli-testuser@localhost-{stale_timestamp}",
        "access_key": "STALEKEY",
    }

    def call_operation_side_effect(resource, action, *args, **kwargs):
        if resource == "object-storage" and action == "keys-list":
            return 200, {"data": [stale_key]}

        if resource == "object-storage" and action == "keys-delete":
            return 200, {}

        if resource == "object-storage" and action == "keys-create":
            return 200, {"access_key": "NEWKEY", "secret_key": "NEWSECRET"}

        if resource == "account" and action == "view":
            return 200, {}

        return 200, {}

    with (
        patch("linodecli.plugins.obj.__init__.CLI") as MockCLI,
        patch.dict(
            obj.COMMAND_MAP,
            {
                # We don't want to actually execute any S3 operations
                "ls": lambda *args, **kwargs: None,
            },
        ),
    ):
        mock_client = MockCLI.return_value
        mock_client.config.plugin_get_value.side_effect = (
            lambda k, d=None, t=None: {
                "key-cleanup-enabled": False,  # Cleanup disabled
                "key-lifespan": "30d",
                "key-rotation-period": "10d",
                "key-cleanup-batch-size": 10,
            }.get(k, None)
        )
        mock_client.config.plugin_set_value.return_value = None
        mock_client.config.write_config.return_value = None
        mock_client.call_operation.side_effect = call_operation_side_effect

        obj.call(
            ["ls", "bucket"],
            plugins.PluginContext("12345", mock_client),
        )

        # Check that keys-delete was NOT called
        delete_calls = [
            c
            for c in mock_client.call_operation.mock_calls
            if c[1][1] == "keys-delete"
        ]
        assert (
            not delete_calls
        ), "Cleanup should not be performed when key-cleanup-enabled is False"
