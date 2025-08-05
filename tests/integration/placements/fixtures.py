import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_text,
)
from tests.integration.linodes.helpers import create_linode


@pytest.fixture(scope="session")
def linode_for_placement_tests(linode_cloud_firewall):
    linode_id = create_linode(
        firewall_id=linode_cloud_firewall, test_region="us-mia"
    )

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="session")
def placement_group():
    new_label = get_random_text(5) + "-label"
    placement_group_id = exec_test_command(
        BASE_CMDS["placement"]
        + [
            "group-create",
            "--label",
            new_label,
            "--region",
            "us-mia",
            "--placement_group_type",
            "anti_affinity:local",
            "--placement_group_policy",
            "strict",
            "--text",
            "--no-headers",
            "--format=id",
        ]
    )
    yield placement_group_id

    delete_target_id(
        target="placement", delete_command="group-delete", id=placement_group_id
    )
