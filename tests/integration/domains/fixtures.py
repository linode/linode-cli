import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_domain_status,
    get_random_text,
    wait_for_condition,
)


@pytest.fixture(scope="function")
def master_domain():
    domain_id = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "create",
            "--type",
            "master",
            "--domain",
            get_random_text(5) + "-example.com",
            "--soa_email",
            "pthiel_test@linode.com",
            "--text",
            "--no-header",
            "--format",
            "id",
        ]
    )

    # Verify domain status becomes active before proceeding with tests
    wait_for_condition(5, 30, get_domain_status, "domains", domain_id, "active")

    yield domain_id

    delete_target_id("domains", id=domain_id)


@pytest.fixture(scope="function")
def slave_domain():
    domain_id = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "create",
            "--type",
            "slave",
            "--domain",
            get_random_text(5) + "-example.com",
            "--master_ips",
            "1.1.1.1",
            "--text",
            "--no-header",
            "--delimiter",
            ",",
            "--format=id",
        ]
    )

    # Verify domain status becomes active before proceeding with tests
    wait_for_condition(5, 30, get_domain_status, "domains", domain_id, "active")

    yield domain_id

    delete_target_id("domains", domain_id)


@pytest.fixture(scope="function")
def domain_and_record():
    # Create domain
    domain_id = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "create",
            "--type",
            "master",
            "--domain",
            get_random_text(5) + "-example.com",
            "--soa_email=pthiel@linode.com",
            "--text",
            "--no-header",
            "--format=id",
        ]
    )

    # Verify domain status becomes active before proceeding with tests
    wait_for_condition(5, 30, get_domain_status, "domains", domain_id, "active")

    # Create record
    record_id = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "records-create",
            "--protocol=tcp",
            "--type=SRV",
            "--port=23",
            "--priority=4",
            "--service=telnet",
            "--target=record-setup",
            "--weight=4",
            "--text",
            "--no-header",
            "--delimiter=,",
            "--format=id",
            domain_id,
        ]
    )

    yield domain_id, record_id

    delete_target_id(target="domains", id=domain_id)
