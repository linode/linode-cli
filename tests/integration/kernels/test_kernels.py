import re

import pytest

from tests.integration.helpers import exec_test_command

BASE_CMD = ["linode-cli", "kernels", "list", "--text", "--no-headers"]


def test_list_available_kernels():
    process = exec_test_command(BASE_CMD + ["--format", "id"])
    output = process.stdout.decode()

    for line in output.splitlines():
        assert "linode" in line


def test_fields_from_kernels_list():
    process = exec_test_command(
        BASE_CMD
        + [
            "--delimiter",
            ",",
            "--format",
            "id,version,kvm,architecture,pvops,deprecated,built",
        ]
    )
    output = process.stdout.decode()

    for line in output.splitlines():
        assert re.search(
            "linode/.*,.*,(False|True),(i386|x86_64),(False|True),(False|True),.*",
            line,
        )


@pytest.mark.smoke
def test_view_kernel():
    process = exec_test_command(BASE_CMD + ["--format", "id"])
    output = process.stdout.decode()

    lines = output.splitlines()

    process = exec_test_command(
        [
            "linode-cli",
            "kernels",
            "view",
            str(lines[0]),
            "--format",
            "id,version,kvm,architecture,pvops,deprecated,built",
            "--text",
            "--delimiter",
            ",",
        ]
    )
    output = process.stdout.decode()

    assert "id,version,kvm,architecture,pvops,deprecated,built" in output

    assert re.search(
        "linode/.*,.*,(False|True),(i386|x86_64),(False|True),(False|True),.*",
        output,
    )
