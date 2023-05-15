import importlib
from unittest.mock import patch

import pytest
from pytest import CaptureFixture

from linodecli.plugins import PluginContext

# Non-importable package name
plugin = importlib.import_module("linodecli.plugins.image-upload")


def test_print_help(capsys: CaptureFixture):
    with pytest.raises(SystemExit) as err:
        plugin.call(["--help"], None)

    captured_text = capsys.readouterr().out

    assert err.value.code == 0
    assert "The image file to upload" in captured_text
    assert "The region to upload the image to" in captured_text


def test_no_file(mock_cli, capsys: CaptureFixture):
    with pytest.raises(SystemExit) as err:
        plugin.call(
            ["--label", "cool", "blah.txt"],
            PluginContext("REALTOKEN", mock_cli),
        )

    captured_text = capsys.readouterr().out

    assert err.value.code == 2
    assert "No file at blah.txt" in captured_text


@patch("os.path.isfile", lambda a: True)
@patch("os.path.getsize", lambda a: plugin.MAX_UPLOAD_SIZE + 1)
def test_file_too_large(mock_cli, capsys: CaptureFixture):
    args = ["--label", "cool", "blah.txt"]
    ctx = PluginContext("REALTOKEN", mock_cli)

    with pytest.raises(SystemExit) as err:
        plugin.call(args, ctx)

    captured_text = capsys.readouterr().out

    assert err.value.code == 2
    assert "File blah.txt is too large" in captured_text


@patch("os.path.isfile", lambda a: True)
@patch("os.path.getsize", lambda a: 1)
def test_unauthorized(mock_cli, capsys: CaptureFixture):
    args = ["--label", "cool", "blah.txt"]

    mock_cli.call_operation = lambda *a: (401, None)

    ctx = PluginContext("REALTOKEN", mock_cli)

    with pytest.raises(SystemExit) as err:
        plugin.call(args, ctx)

    captured_text = capsys.readouterr().out

    assert err.value.code == 3
    assert "Your token was not authorized to use this endpoint" in captured_text


@patch("os.path.isfile", lambda a: True)
@patch("os.path.getsize", lambda a: 1)
def test_non_beta(mock_cli, capsys: CaptureFixture):
    args = ["--label", "cool", "blah.txt"]

    mock_cli.call_operation = lambda *a: (404, None)

    ctx = PluginContext("REALTOKEN", mock_cli)

    with pytest.raises(SystemExit) as err:
        plugin.call(args, ctx)

    captured_text = capsys.readouterr().out

    assert err.value.code == 4
    assert (
        "It looks like you are not in the Machine Images Beta" in captured_text
    )


@patch("os.path.isfile", lambda a: True)
@patch("os.path.getsize", lambda a: 1)
def test_non_beta(mock_cli, capsys: CaptureFixture):
    args = ["--label", "cool", "blah.txt"]

    mock_cli.call_operation = lambda *a: (404, None)

    ctx = PluginContext("REALTOKEN", mock_cli)

    with pytest.raises(SystemExit) as err:
        plugin.call(args, ctx)

    captured_text = capsys.readouterr().out

    assert err.value.code == 4
    assert (
        "It looks like you are not in the Machine Images Beta" in captured_text
    )


@patch("os.path.isfile", lambda a: True)
@patch("os.path.getsize", lambda a: 1)
def test_failed_upload(mock_cli, capsys: CaptureFixture):
    args = ["--label", "cool", "blah.txt"]
    mock_cli.call_operation = lambda *a: (500, "it borked :(")

    ctx = PluginContext("REALTOKEN", mock_cli)

    with pytest.raises(SystemExit) as err:
        plugin.call(args, ctx)

    captured_text = capsys.readouterr().out

    assert err.value.code == 3
    assert (
        "Upload failed with status 500; response was it borked :("
        in captured_text
    )
