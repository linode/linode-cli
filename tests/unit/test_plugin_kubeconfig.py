import base64
import contextlib
import importlib
import io
import os
import random
import string
import tempfile

import pytest
import yaml

from linodecli.plugins import PluginContext

# Non-importable package name
plugin = importlib.import_module("linodecli.plugins.get-kubeconfig")

TEST_YAML_CONTENT_A = """
name: testing-kubeconfig
things:
- thing:
    property-1: hello
    property-2: world
  name: thing-1
- thing:
    property-1: foo
    property-2: bar
  name: thing-2
items:
- item:
    property-1: a
    property-2: b
    property-3: c
  name: item-1
dictionary: {}
"""

TEST_YAML_CONTENT_B = """
name: testing-kubeconfig-2
things: []
items:
- item:
    property-1: a
    property-2: b
    property-3: c
  name: item-1
- item:
    property-1: d
    property-2: e
  name: item-2
dictionary: {"foo": "bar"}
"""


# Test the output of --help
def test_print_help():
    stdout_buf = io.StringIO()

    with pytest.raises(SystemExit) as err:
        with contextlib.redirect_stdout(stdout_buf):
            plugin.call(["--help"], None)

    assert err.value.code == 0

    assert "Path to kubeconfig file." in stdout_buf.getvalue()
    assert "Label for desired cluster." in stdout_buf.getvalue()


# Test the error message when neither a label nor an id is provided
def test_no_label_no_id(mock_cli):
    stderr_buf = io.StringIO()

    with pytest.raises(SystemExit) as err:
        with contextlib.redirect_stderr(stderr_buf):
            plugin.call(
                [],
                PluginContext("REALTOKEN", mock_cli),
            )

    assert err.value.code == 1

    assert "Either --label or --id must be used." in stderr_buf.getvalue()


# Test the output when a label that doesn't exist is used
def test_nonexisting_label(mock_cli):
    stderr_buf = io.StringIO()
    mock_cli.call_operation = mock_call_operation

    with pytest.raises(SystemExit) as err:
        with contextlib.redirect_stderr(stderr_buf):
            plugin.call(
                ["--label", "empty_data"],
                PluginContext("REALTOKEN", mock_cli),
            )

    assert err.value.code == 1

    assert (
        "Cluster with label empty_data does not exist." in stderr_buf.getvalue()
    )


# Test the output when an id that doesn't exist is used
def test_nonexisting_id(mock_cli):
    stderr_buf = io.StringIO()

    with pytest.raises(SystemExit) as err:
        with contextlib.redirect_stderr(stderr_buf):
            plugin.call(
                ["--id", "12345"],
                PluginContext("REALTOKEN", mock_cli),
            )

    assert err.value.code == 1

    assert "Error retrieving kubeconfig:" in stderr_buf.getvalue()


# Test the output when the provided path exists but the file there contains improper YAML
def test_improper_file(mock_cli, fake_empty_file):
    stderr_buf = io.StringIO()
    mock_cli.call_operation = mock_call_operation

    file_path = fake_empty_file

    with pytest.raises(SystemExit) as err:
        with contextlib.redirect_stderr(stderr_buf):
            plugin.call(
                [
                    "--label",
                    "nonempty_data",
                    "--kubeconfig",
                    file_path,
                ],
                PluginContext("REALTOKEN", mock_cli),
            )

    assert err.value.code == 1

    assert "Could not load file at" in stderr_buf.getvalue()


# Test the output when a kubeconfig is merged into a path without an existing kubeconfig file
def test_no_existing_config(mock_cli):
    stdout_buf = io.StringIO()
    mock_cli.call_operation = mock_call_operation

    random_dir = "".join(random.choice(string.ascii_letters) for i in range(10))

    try:
        with contextlib.redirect_stdout(stdout_buf):
            plugin.call(
                [
                    "--label",
                    "nonempty_data",
                    "--kubeconfig",
                    "~/fake/path/" + random_dir + "/config",
                    "--dry-run",
                ],
                PluginContext("REALTOKEN", mock_cli),
            )
    except SystemExit as err:
        assert err.code == 0

    assert "testing-kubeconfig-2" in stdout_buf.getvalue()


# Test the output when a kubeconfig is merged into a path with an existing kubeconfig file and
# verify that the merge is correct.
def test_merge(mock_cli, fake_kubeconfig_file):
    stdout_buf = io.StringIO()
    mock_cli.call_operation = mock_call_operation

    file_path = fake_kubeconfig_file

    try:
        with contextlib.redirect_stdout(stdout_buf):
            plugin.call(
                [
                    "--label",
                    "nonempty_data",
                    "--kubeconfig",
                    file_path,
                    "--dry-run",
                ],
                PluginContext("REALTOKEN", mock_cli),
            )
    except SystemExit as err:
        assert err.code == 0

    result = yaml.safe_load(stdout_buf.getvalue())
    yaml_a = yaml.safe_load(TEST_YAML_CONTENT_A)
    yaml_b = yaml.safe_load(TEST_YAML_CONTENT_B)

    assert result["name"] == yaml_a["name"]
    assert result["things"] == yaml_a["things"]
    assert result["items"] == yaml_a["items"] + [yaml_b["items"][1]]
    assert result["dictionary"] == yaml_a["dictionary"]


@pytest.fixture(scope="session", autouse=True)
def fake_kubeconfig_file():
    with tempfile.NamedTemporaryFile(delete=False) as fp:
        fp.write(bytes(TEST_YAML_CONTENT_A, "utf-8"))
        file_path = fp.name

    yield file_path

    os.remove(file_path)


@pytest.fixture(scope="session", autouse=True)
def fake_empty_file():
    with tempfile.NamedTemporaryFile(delete=False) as fp:
        file_path = fp.name

    yield file_path

    os.remove(file_path)


def mock_call_operation(command, action, **kwargs):
    if (
        command == "lke"
        and action == "clusters-list"
        and "empty_data" in kwargs["args"]
    ):
        return 200, {"data": []}
    if (
        command == "lke"
        and action == "clusters-list"
        and "nonempty_data" in kwargs["args"]
    ):
        return 200, {"data": [{"id": "100"}]}
    if command == "lke" and action == "kubeconfig-view":
        return 200, {
            "kubeconfig": base64.b64encode(TEST_YAML_CONTENT_B.encode())
        }

    # Default response
    return 200, None
