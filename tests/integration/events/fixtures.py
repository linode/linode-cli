import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_text,
    view_command_attribute,
    wait_for_condition,
)


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

    def get_domain_status():
        status = view_command_attribute("domains", domain_id, "status")
        return "active" in status

    wait_for_condition(5, 30, get_domain_status)

    yield domain_id

    delete_target_id(target="domains", id=domain_id)
