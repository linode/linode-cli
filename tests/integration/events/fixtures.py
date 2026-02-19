import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    check_attribute_value,
    delete_target_id,
    exec_test_command,
    get_random_text,
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

    # Verify domain status becomes active before proceeding with tests
    wait_for_condition(5, 60, check_attribute_value, "domains", "view",
                       domain_id, "status", "active")

    yield domain_id

    delete_target_id(target="domains", id=domain_id)
