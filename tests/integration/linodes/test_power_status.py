import pytest

from tests.integration.helpers import delete_target_id, exec_test_command
from tests.integration.linodes.helpers_linodes import (
    BASE_CMD,
    create_linode,
    create_linode_and_wait,
    wait_until,
)


@pytest.fixture
def setup_power_status():
    linode_id = create_linode()

    yield linode_id

    delete_target_id(target="linodes", id=linode_id)


@pytest.fixture
def create_linode_in_running_state():
    linode_id = create_linode_and_wait()

    yield linode_id

    delete_target_id("linodes", linode_id)


def test_create_linode_and_boot(setup_power_status):
    linode_id = setup_power_status

    # returns false if status is not running after 240s
    result = wait_until(linode_id=linode_id, timeout=240, status="running")

    assert result, "Linode status has not changed to running from provisioning"


def test_reboot_linode(create_linode_in_running_state):
    # create linode and wait until it is in "running" state
    linode_id = create_linode_in_running_state

    # reboot linode from "running" status
    exec_test_command(
        BASE_CMD + ["reboot", linode_id, "--text", "--no-headers"]
    )

    # returns false if status is not running after 240s after reboot
    assert wait_until(
        linode_id=linode_id, timeout=240, status="running"
    ), "Linode status has not changed to running from provisioning"


def test_shutdown_linode(setup_power_status):
    linode_id = setup_power_status

    # returns false if status is not running after 240s after reboot
    assert wait_until(
        linode_id=linode_id, timeout=240, status="running"
    ), "Linode status has not changed to running from provisioning"

    # shutdown linode that is in running state
    exec_test_command(BASE_CMD + ["shutdown", linode_id])

    result = wait_until(linode_id=linode_id, timeout=180, status="offline")

    assert (result, "Linode status has not changed to running from offline")
