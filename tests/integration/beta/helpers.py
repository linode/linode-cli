import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
)


def get_beta_id():
    beta_ids = exec_test_command(
        BASE_CMDS["betas"]
        + [
            "list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    if not beta_ids or beta_ids == [""]:
        pytest.skip("No betas available to test.")

    return beta_ids[0] if beta_ids else None
