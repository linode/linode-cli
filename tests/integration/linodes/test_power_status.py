import pytest

from tests.integration.helpers import delete_target_id, exec_test_command
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    create_linode_and_wait,
    wait_until,
)


@pytest.fixture
def test_linode_id(linode_cloud_firewall):
    linode_id = create_linode_and_wait(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture
def linode_in_running_state(linode_cloud_firewall):
    linode_id = create_linode_and_wait(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id("linodes", linode_id)


@pytest.fixture
def linode_in_running_state_for_reboot(linode_cloud_firewall):
    linode_id = create_linode_and_wait(firewall_id=linode_cloud_firewall)

    yield linode_id

    delete_target_id("linodes", linode_id)


@pytest.mark.smoke
def test_create_linode_and_boot(test_linode_id):
    linode_id = test_linode_id

    # returns false if status is not running after 240s
    result = wait_until(linode_id=linode_id, timeout=240, status="running")

    assert result, "Linode status has not changed to running from provisioning"


def test_reboot_linode(linode_in_running_state_for_reboot):
    # create linode and wait until it is in "running" state
    linode_id = linode_in_running_state_for_reboot

    # reboot linode from "running" status
    exec_test_command(
        BASE_CMD + ["reboot", linode_id, "--text", "--no-headers"]
    )

    # returns false if status is not running after 240s after reboot
    assert wait_until(
        linode_id=linode_id, timeout=240, status="running"
    ), "Linode status has not changed to running from provisioning"


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_shutdown_linode(test_linode_id):
    linode_id = test_linode_id

    # returns false if status is not running after 240s after reboot
    assert wait_until(
        linode_id=linode_id, timeout=240, status="running"
    ), "Linode status has not changed to running from provisioning"

    # shutdown linode that is in running state
    exec_test_command(BASE_CMD + ["shutdown", linode_id])

    result = wait_until(linode_id=linode_id, timeout=180, status="offline")

    assert result, "Linode status has not changed to running from offline"
