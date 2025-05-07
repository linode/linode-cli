import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_text,
)


@pytest.fixture
def events_test_domain_id():
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

    yield domain_id

    delete_target_id(target="domains", id=domain_id)
