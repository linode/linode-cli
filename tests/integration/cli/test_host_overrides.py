import os

from pytest import MonkeyPatch

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import INVALID_HOST, exec_failing_test_command


def test_cli_command_fails_to_access_invalid_host(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_HOST", INVALID_HOST)

    process = exec_failing_test_command(["linode-cli", "linodes", "ls"], ExitCodes.UNRECOGNIZED_COMMAND)
    output = process.stderr.decode()

    expected_output = ["Max retries exceeded with url:", "wrongapi.linode.com"]

    for eo in expected_output:
        assert eo in output


def test_cli_uses_v4beta_when_override_is_set(monkeypatch: MonkeyPatch):
    monkeypatch.setenv("LINODE_CLI_API_VERSION", "v4beta")
    os.system("linode-cli linodes ls --debug 2>&1 | tee /tmp/output_file.txt")

    result = os.popen("cat /tmp/output_file.txt").read()
    assert "v4beta" in result


def test_cli_command_fails_to_access_invalid_api_scheme(
    monkeypatch: MonkeyPatch,
):
    monkeypatch.setenv("LINODE_CLI_API_SCHEME", "ssh")
    process = exec_failing_test_command(["linode-cli", "linodes", "ls"], ExitCodes.UNRECOGNIZED_COMMAND)
    output = process.stderr.decode()

    assert "ssh://" in output
