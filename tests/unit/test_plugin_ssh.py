import argparse
from unittest.mock import patch

import pytest
from pytest import CaptureFixture

import linodecli.plugins.ssh as plugin
from linodecli.plugins import PluginContext


def test_print_help(capsys: CaptureFixture, get_platform_os_type):
    if get_platform_os_type == "Windows":
        pytest.skip("This test does not run on Windows")
    with pytest.raises(SystemExit) as err:
        plugin.call(["--help"], None)

    assert err.value.code == 0

    captured_text = capsys.readouterr().out
    assert "[USERNAME@]LABEL" in captured_text
    assert "uses the Linode's SLAAC address for SSH" in captured_text


@patch("linodecli.plugins.ssh.platform", "win32")
def test_windows_error(capsys: CaptureFixture):
    with pytest.raises(SystemExit) as err:
        plugin.call(["test@test"], None)

    assert err.value.code == 1

    captured_text = capsys.readouterr().out
    assert "This plugin is not currently supported in Windows." in captured_text


def test_target_not_running(
    mock_cli, capsys: CaptureFixture, get_platform_os_type
):
    if get_platform_os_type == "Windows":
        pytest.skip("This test does not run on Windows")
    test_label = "totally-real-label"

    def mock_call_operation(*a, filters=None):
        assert filters == {"label": {"+contains": test_label}}

        return 200, {"data": [{"label": test_label, "status": "provisioning"}]}

    mock_cli.call_operation = mock_call_operation

    with pytest.raises(SystemExit) as err:
        plugin.call(
            [f"test@{test_label}"], PluginContext("FAKETOKEN", mock_cli)
        )

    assert err.value.code == 2

    captured_text = capsys.readouterr().out
    assert (
        f"{test_label} is not running (status is provisioning)" in captured_text
    )


def test_target_success(mock_cli, capsys: CaptureFixture, get_platform_os_type):
    if get_platform_os_type == "Windows":
        pytest.skip("This test does not run on Windows")
    test_label = "totally-real-label"
    test_user = "test"
    test_ip = "123.123.123.123"

    ssh_called = False

    def mock_check_call(args):
        nonlocal ssh_called
        ssh_called = True

        assert args == ["ssh", f"{test_user}@{test_ip}", "--pass-through"]

    def mock_call_operation(*a, filters=None):
        assert filters == {"label": {"+contains": test_label}}

        return 200, {
            "data": [
                {"label": test_label, "status": "running", "ipv4": [test_ip]}
            ]
        }

    mock_cli.call_operation = mock_call_operation

    try:
        with patch("subprocess.check_call", mock_check_call):
            plugin.call(
                [f"{test_user}@{test_label}", "--pass-through"],
                PluginContext("FAKETOKEN", mock_cli),
            )
    except SystemExit as err:
        assert err.code == 0

    assert ssh_called


def test_find_with_label(mock_cli, capsys: CaptureFixture):
    test_label = "really-cool-label"

    def mock_call_operation(*a, filters=None):
        assert filters == {"label": {"+contains": test_label}}

        return 200, {
            "data": [{"label": test_label + "-bad"}, {"label": test_label}]
        }

    mock_cli.call_operation = mock_call_operation

    result = plugin.find_linode_with_label(
        PluginContext("FAKETOKEN", mock_cli), test_label
    )

    assert result == {"label": test_label}


def test_find_with_bad_label(mock_cli, capsys: CaptureFixture):
    test_label = "really-cool-label"

    def mock_call_operation(*a, filters=None):
        assert filters == {"label": {"+contains": test_label}}

        return 200, {
            "data": [
                {"label": test_label + "-bad"},
            ]
        }

    mock_cli.call_operation = mock_call_operation

    with pytest.raises(SystemExit) as err:
        plugin.find_linode_with_label(
            PluginContext("FAKETOKEN", mock_cli), test_label
        )

    assert err.value.code == 1

    captured_text = capsys.readouterr().out

    assert f"No Linode found for label {test_label}" in captured_text
    assert "Did you mean: " in captured_text
    assert f"{test_label}-bad" in captured_text


def test_find_api_error(mock_cli, capsys: CaptureFixture):
    test_label = "really-cool-label"

    def mock_call_operation(*a, filters=None):
        assert filters == {"label": {"+contains": test_label}}

        return 500, "everything broke"

    mock_cli.call_operation = mock_call_operation

    with pytest.raises(SystemExit) as err:
        plugin.find_linode_with_label(
            PluginContext("FAKETOKEN", mock_cli), test_label
        )

    assert err.value.code == 2

    captured_text = capsys.readouterr().out

    assert "Could not retrieve Linode: 500 error" in captured_text


def test_parse_target_components():
    username, label = plugin.parse_target_components("cool")
    assert username is None
    assert label == "cool"

    username, label = plugin.parse_target_components("foo@bar")
    assert username == "foo"
    assert label == "bar"


def test_parse_target_address():
    test_target = {
        "ipv4": [
            "192.168.1.100",
            "123.123.123.123",
        ],
        "ipv6": "c001:d00d::1337/128",
    }

    test_namespace = argparse.Namespace(**{"6": False})

    address = plugin.parse_target_address(test_namespace, test_target)
    assert address == "123.123.123.123"

    # Hack to work around invalid key
    setattr(test_namespace, "6", True)

    address = plugin.parse_target_address(test_namespace, test_target)
    assert address == "c001:d00d::1337"
