import pytest

from tests.integration.helpers import delete_target_id
from tests.integration.linodes.helpers import (
    create_linode,
    create_linode_and_wait,
)


@pytest.fixture(scope="package")
def get_linode_id(linode_cloud_firewall):
    linode_id = create_linode_and_wait(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture(scope="package")
def get_linode_ids_shared_ipv4(linode_cloud_firewall):
    target_region = "us-mia"

    linode_ids = (
        create_linode(
            test_region=target_region, firewall_id=linode_cloud_firewall
        ),
        create_linode(
            test_region=target_region, firewall_id=linode_cloud_firewall
        ),
    )

    yield linode_ids

    for id_num in linode_ids:
        delete_target_id(target="linodes", id=id_num)
