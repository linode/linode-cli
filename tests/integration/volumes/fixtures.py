import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_text,
    wait_for_condition,
)


@pytest.fixture(scope="session")
def volume_instance_id():
    label = get_random_text(8)
    volume_id = exec_test_command(
        BASE_CMDS["volumes"]
        + [
            "create",
            "--label",
            label,
            "--region",
            "us-ord",
            "--size",
            "10",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    )

    def poll_volume_status():
        status = exec_test_command(
            BASE_CMDS["volumes"]
            + [
                "view",
                volume_id,
                "--text",
                "--no-headers",
                "--format=status",
            ]
        )
        return status.strip() == "active"

    wait_for_condition(10, 240, poll_volume_status)

    yield volume_id

    delete_target_id(
        target="volumes", id=volume_id, use_retry=True, retries=5, delay=15
    )
