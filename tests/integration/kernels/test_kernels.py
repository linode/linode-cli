import re

import pytest

from tests.integration.helpers import BASE_CMDS, exec_test_command


def test_list_available_kernels():
    output = exec_test_command(
        BASE_CMDS["kernels"]
        + ["list", "--text", "--no-headers", "--format", "id"]
    )

    for line in output.splitlines():
        assert "linode" in line


def test_fields_from_kernels_list():
    output = exec_test_command(
        BASE_CMDS["kernels"]
        + [
            "list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id,version,kvm,architecture,pvops,deprecated,built",
        ]
    )

    for line in output.splitlines():
        assert re.search(
            "linode/.*,.*,(False|True),(i386|x86_64),(False|True),(False|True),.*",
            line,
        )


@pytest.mark.smoke
def test_view_kernel():
    output = exec_test_command(
        BASE_CMDS["kernels"]
        + ["list", "--text", "--no-headers", "--format", "id"]
    )

    lines = output.splitlines()

    output = exec_test_command(
        BASE_CMDS["kernels"]
        + [
            "view",
            str(lines[0]),
            "--format",
            "id,version,kvm,architecture,pvops,deprecated,built",
            "--text",
            "--delimiter",
            ",",
        ]
    )

    assert "id,version,kvm,architecture,pvops,deprecated,built" in output

    assert re.search(
        "linode/.*,.*,(False|True),(i386|x86_64),(False|True),(False|True),.*",
        output,
    )
