import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_text,
    view_command_attribute,
    wait_for_condition,
)


def get_domain_status(command: str, item_id: str, expected_status: str) -> bool:
    status = view_command_attribute(command, item_id, "status")
    return expected_status in status


@pytest.fixture(scope="function")
def events_create_domain():
    # Create domain
    domain_id = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "create",
            "--type",
            "master",
            "--domain",
            "A" + get_random_text(5) + "example.com",
            "--soa_email=developer-test@linode.com",
            "--text",
            "--no-header",
            "--format",
            "id",
        ]
    )

    # Verify domain status becomes active before proceeding with tests
    wait_for_condition(5, 30, get_domain_status, "domains", domain_id, "active")

    yield domain_id

    delete_target_id(target="domains", id=domain_id)
