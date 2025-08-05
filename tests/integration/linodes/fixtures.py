import json
import time

import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
    retry_exec_test_command_with_delay,
)
from tests.integration.linodes.helpers import (
    DEFAULT_LABEL,
    DEFAULT_LINODE_TYPE,
    DEFAULT_RANDOM_PASS,
    DEFAULT_REGION,
    DEFAULT_TEST_IMAGE,
    create_linode,
    create_linode_and_wait,
    create_linode_backup_disabled,
    get_disk_ids,
    get_subnet_id,
    set_backups_enabled_in_account_settings,
    wait_until,
)


# Backups
@pytest.fixture(scope="module")
def linode_basic_with_firewall(linode_cloud_firewall):
    linode_id = create_linode(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id("linodes", linode_id)


@pytest.fixture(scope="module")
def linode_backup_enabled(linode_cloud_firewall):
    # create linode with backups enabled
    linode_id = exec_test_command(
        [
            "linode-cli",
            "linodes",
            "create",
            "--backups_enabled",
            "true",
            "--type",
            DEFAULT_LINODE_TYPE,
            "--region",
            DEFAULT_REGION,
            "--image",
            DEFAULT_TEST_IMAGE,
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--firewall_id",
            linode_cloud_firewall,
            "--text",
            "--no-headers",
            "--format=id",
        ]
    )

    yield linode_id

    delete_target_id("linodes", linode_id)


@pytest.fixture(scope="module")
def linode_backup_disabled(linode_cloud_firewall):
    res = set_backups_enabled_in_account_settings(toggle=False)

    if res == "True":
        raise ValueError(
            "Backups are unexpectedly enabled before setting up the test."
        )

    linode_id = create_linode_backup_disabled(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id("linodes", linode_id)


@pytest.fixture(scope="module")
def snapshot_of_linode():
    # get linode id after creation and wait for "running" status
    linode_id = create_linode_and_wait()
    new_snapshot_label = "test_snapshot_" + get_random_text(5)

    result = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "snapshot",
            linode_id,
            "--label",
            new_snapshot_label,
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
        ]
    )

    yield linode_id, new_snapshot_label

    delete_target_id("linodes", linode_id)


# Configs

TEST_REGION = get_random_region_with_caps(
    required_capabilities=["Linodes", "VPCs"]
)


@pytest.fixture(scope="module")
def linode_instance_config_tests(linode_cloud_firewall):
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        disk_encryption=False,
        test_region=TEST_REGION,
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="module")
def linode_disk_config(linode_instance_config_tests):
    linode_id = linode_instance_config_tests

    label = get_random_text(5) + "_config"
    disk_id = get_disk_ids(linode_id=linode_id)[1]

    config_id = exec_test_command(
        BASE_CMDS["linodes"]
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

    yield config_id


@pytest.fixture(scope="module")
def test_vpc_w_subnet(request):
    vpc_json = create_vpc_w_subnet()
    vpc_id = str(vpc_json["id"])

    yield vpc_id


@pytest.fixture(scope="module")
def cleanup_vpc(request, test_vpc_w_subnet):
    # Register finalizer to delete VPC after the entire session, with a delay
    def delayed_cleanup():
        time.sleep(5)  # Delay if necessary
        delete_target_id(target="vpcs", id=test_vpc_w_subnet)

    request.addfinalizer(delayed_cleanup)


@pytest.fixture(scope="module")
def config_vpc_interface(
    linode_instance_config_tests, linode_disk_config, test_vpc_w_subnet
):
    linode_id = linode_instance_config_tests
    config_id = linode_disk_config
    subnet_id = get_subnet_id(vpc_id=test_vpc_w_subnet)

    interface_id = exec_test_command(
        BASE_CMDS["linodes"]
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

    yield interface_id

    retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"]
        + [
            "config-interface-delete",
            linode_id,
            config_id,
            interface_id,
        ]
    )


def create_vpc_w_subnet():
    vpc_label = get_random_text(5) + "vpc"
    subnet_label = get_random_text(5) + "subnet"

    vpc_json = json.loads(
        exec_test_command(
            BASE_CMDS["vpcs"]
            + [
                "create",
                "--label",
                vpc_label,
                "--region",
                TEST_REGION,
                "--subnets.ipv4",
                "10.0.0.0/24",
                "--subnets.label",
                subnet_label,
                "--json",
                "--suppress-warnings",
            ]
        )
    )[0]

    return vpc_json


# Disks
@pytest.fixture(scope="module")
def linode_instance_disk_tests(linode_cloud_firewall):
    test_region = get_random_region_with_caps(required_capabilities=["Linodes"])
    linode_id = create_linode_and_wait(
        firewall_id=linode_cloud_firewall,
        disk_encryption=False,
        test_region=test_region,
        test_plan="g6-standard-4",
    )

    retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"] + ["shutdown", linode_id]
    )

    wait_until(linode_id=linode_id, timeout=240, status="offline")

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


# Interfaces
@pytest.fixture(scope="module")
def linode_with_vpc_interface_as_json(linode_cloud_firewall):
    vpc_json = create_vpc_w_subnet()

    vpc_region = vpc_json["region"]
    vpc_id = str(vpc_json["id"])
    subnet_id = int(vpc_json["subnets"][0]["id"])

    linode_json = json.loads(
        exec_test_command(
            BASE_CMDS["linodes"]
            + [
                "create",
                "--type",
                "g6-nanode-1",
                "--region",
                vpc_region,
                "--image",
                DEFAULT_TEST_IMAGE,
                "--root_pass",
                DEFAULT_RANDOM_PASS,
                "--firewall_id",
                linode_cloud_firewall,
                "--interfaces",
                json.dumps(
                    [
                        {
                            "purpose": "vpc",
                            "primary": True,
                            "subnet_id": subnet_id,
                            "ipv4": {"nat_1_1": "any", "vpc": "10.0.0.5"},
                            "ip_ranges": ["10.0.0.6/32"],
                        },
                        {"purpose": "public"},
                    ]
                ),
                "--json",
                "--suppress-warnings",
            ]
        )
    )[0]

    yield linode_json, vpc_json

    delete_target_id(target="linodes", id=str(linode_json["id"]))
    delete_target_id(target="vpcs", id=vpc_id)


# Interfaces new
@pytest.fixture(scope="module")
def linode_interface_public(linode_cloud_firewall):
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        test_region="us-sea",
        interface_generation="linode",
        interfaces='[{"public": {"ipv4": {"addresses": [{"primary": true}]}}, "default_route": {"ipv4": true, "ipv6": true }, "firewall_id":'
        + linode_cloud_firewall
        + "}]",
    )

    wait_until(linode_id=linode_id, timeout=300, status="running")

    # TODO: add support of creating a offline linode in `create_linode` then remove this workaround
    exec_test_command(BASE_CMDS["linodes"] + ["shutdown", linode_id])

    wait_until(linode_id=linode_id, timeout=60, status="offline")

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="module")
def linode_interface_vlan(linode_cloud_firewall):
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        test_region="us-sea",
        interface_generation="linode",
        interfaces='[{"vlan": {"ipam_address": "10.0.0.1/24","vlan_label": "my-vlan"}}]',
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="module")
def linode_interface_legacy(linode_cloud_firewall):
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        test_region="us-sea",
        interface_generation="legacy_config",
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="module")
def linode_interface_vpc(linode_cloud_firewall):
    vpc_output = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "vpcs",
                "create",
                "--label",
                get_random_text(5) + "-vpc",
                "--region",
                "us-sea",
                "--subnets.ipv4",
                "10.0.0.0/24",
                "--subnets.label",
                get_random_text(5) + "-vpc",
                "--json",
                "--suppress-warnings",
            ]
        )
    )

    subnet_id = vpc_output[0]["subnets"][0]["id"]

    linode_id = create_linode(
        firewall_id=linode_cloud_firewall,
        test_region="us-sea",
        interface_generation="linode",
        interfaces='[{"default_route":{"ipv4":true},"firewall_id":'
        + str(linode_cloud_firewall)
        + ',"vpc":{"ipv4":{"addresses":[{"address":"auto","nat_1_1_address":"auto","primary":true}]},"subnet_id":'
        + str(subnet_id)
        + "}}]",
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)
    delete_target_id(target="vpcs", id=str(vpc_output[0]["id"]))


# Linodes
@pytest.fixture(scope="module")
def test_linode_instance(linode_cloud_firewall):
    linode_label = DEFAULT_LABEL + get_random_text(5)

    linode_id = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "create",
            "--type",
            "g6-nanode-1",
            "--region",
            "us-ord",
            "--image",
            DEFAULT_TEST_IMAGE,
            "--label",
            linode_label,
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--firewall_id",
            linode_cloud_firewall,
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format",
            "id",
            "--no-defaults",
            "--format",
            "id",
        ]
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


# Linode Power Status
@pytest.fixture(scope="module")
def linode_instance_basic(linode_cloud_firewall):
    linode_id = create_linode_and_wait(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="module")
def linode_in_running_state(linode_cloud_firewall):
    linode_id = create_linode_and_wait(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id("linodes", linode_id)


@pytest.fixture(scope="session")
def linode_in_running_state_for_reboot(linode_cloud_firewall):
    linode_id = create_linode_and_wait(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id("linodes", linode_id)


# Rebuild
@pytest.fixture(scope="module")
def linode_for_rebuild_tests(linode_cloud_firewall):
    test_region = get_random_region_with_caps(
        required_capabilities=["Linodes", "Disk Encryption"]
    )
    linode_id = create_linode_and_wait(
        firewall_id=linode_cloud_firewall,
        disk_encryption=False,
        test_region=test_region,
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


# Resize
@pytest.fixture(scope="module")
def linode_instance_for_resize_tests(linode_cloud_firewall):
    plan = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "types",
            "--format",
            "id",
            "--text",
            "--no-headers",
        ]
    ).splitlines()[1]
    linode_id = create_linode_and_wait(
        firewall_id=linode_cloud_firewall, test_plan=plan
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


# Linodes
@pytest.fixture(scope="module")
def linode_wo_image(linode_cloud_firewall):
    label = get_random_text(5) + "-label"
    linode_id = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "create",
            "--no-defaults",
            "--label",
            label,
            "--type",
            DEFAULT_LINODE_TYPE,
            "--region",
            DEFAULT_REGION,
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--firewall_id",
            linode_cloud_firewall,
            "--format",
            "id",
            "--no-headers",
            "--text",
        ]
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="module")
def linode_min_req(linode_cloud_firewall):
    result = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "create",
            "--type",
            "g6-nanode-1",
            "--region",
            "us-ord",
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--firewall_id",
            linode_cloud_firewall,
            "--no-defaults",
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format",
            "id,region,type",
        ]
    )

    yield result

    res_arr = result.split(",")
    linode_id = res_arr[0]
    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="module")
def linode_with_label(linode_cloud_firewall):
    label = "cli" + get_random_text(5)
    result = exec_test_command(
        BASE_CMDS["linodes"]
        + [
            "create",
            "--type",
            "g6-nanode-1",
            "--region",
            "us-ord",
            "--image",
            DEFAULT_TEST_IMAGE,
            "--label",
            label,
            "--root_pass",
            DEFAULT_RANDOM_PASS,
            "--firewall_id",
            linode_cloud_firewall,
            "--text",
            "--delimiter",
            ",",
            "--no-headers",
            "--format",
            "label,region,type,image,id",
            "--no-defaults",
        ]
    )

    yield result
    res_arr = result.split(",")
    linode_id = res_arr[4]
    delete_target_id(target="linodes", id=linode_id)
