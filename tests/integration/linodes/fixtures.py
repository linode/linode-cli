
import pytest

from tests.integration.helpers import (
    delete_target_id,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
    retry_exec_test_command_with_delay,
)
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    create_linode,
    create_linode_backup_disabled,
    get_disk_ids,
    set_backups_enabled_in_account_settings,
)


# Backups
@pytest.fixture
def create_linode_setup(linode_cloud_firewall):
    linode_id = create_linode(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id("linodes", linode_id)


@pytest.fixture
def create_linode_backup_disabled_setup(linode_cloud_firewall):
    res = set_backups_enabled_in_account_settings(toggle=False)

    if res == "True":
        raise ValueError(
            "Backups are unexpectedly enabled before setting up the test."
        )

    linode_id = create_linode_backup_disabled(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id("linodes", linode_id)


# Configs

TEST_REGION = get_random_region_with_caps(
    required_capabilities=["Linodes", "VPCs"]
)


@pytest.fixture(scope="session", autouse=True)
def linode_instance_config_tests(linode_cloud_firewall):
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        disk_encryption=False,
        test_region=TEST_REGION,
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="session", autouse=True)
def linode_disk_config(linode_instance_config_tests):
    linode_id = linode_instance_config_tests

    label = get_random_text(5) + "_config"
    disk_id = get_disk_ids(linode_id=linode_id)[1]

    config_id = (
        exec_test_command(
            BASE_CMD
            + [
                "config-create",
                linode_id,
                "--label",
                label,
                "--devices.sda.disk_id",
                disk_id,
                "--no-headers",
                "--format=id",
                "--text",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield config_id


@pytest.fixture(scope="session", autouse=True)
def test_vpc_w_subnet(request):
    vpc_json = create_vpc_w_subnet()
    vpc_id = str(vpc_json["id"])

    yield vpc_id


@pytest.fixture(scope="session", autouse=True)
def cleanup_vpc(request, test_vpc_w_subnet):
    # Register finalizer to delete VPC after the entire session, with a delay
    def delayed_cleanup():
        time.sleep(5)  # Delay if necessary
        delete_target_id(target="vpcs", id=test_vpc_w_subnet)

    request.addfinalizer(delayed_cleanup)


@pytest.fixture(scope="session", autouse=True)
def config_vpc_interface(
    linode_instance_config_tests, linode_disk_config, test_vpc_w_subnet
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config
    subnet_id = get_subnet_id(vpc_id=test_vpc_w_subnet)

    interface_id = (
        exec_test_command(
            BASE_CMD
            + [
                "config-interface-add",
                linode_id,
                config_id,
                "--purpose",
                "vpc",
                "--primary",
                "false",
                "--subnet_id",
                subnet_id,
                "--ipv4.vpc",
                "10.0.0.3",
                "--text",
                "--no-headers",
                "--format",
                "id",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield interface_id

    retry_exec_test_command_with_delay(
        BASE_CMD
        + [
            "config-interface-delete",
            linode_id,
            config_id,
            interface_id,
        ]
    )
