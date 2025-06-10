import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
    retry_exec_test_command_with_delay,
)
from tests.integration.linodes.fixtures import (  # noqa: F401
    linode_in_running_state_for_reboot,
    linode_instance_basic,
)
from tests.integration.linodes.helpers import (
    wait_until,
)


@pytest.mark.smoke
def test_create_linode_and_boot(linode_instance_basic):
    linode_id = linode_instance_basic

    # returns false if status is not running after 240s
    result = wait_until(linode_id=linode_id, timeout=240, status="running")

    assert result, "Linode status has not changed to running from provisioning"


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_reboot_linode(linode_in_running_state_for_reboot):
    # create linode and wait until it is in "running" state
    linode_id = linode_in_running_state_for_reboot

    # reboot linode from "running" status
    retry_exec_test_command_with_delay(
        BASE_CMDS["linodes"] + ["reboot", linode_id, "--text", "--no-headers"],
        3,
        20,
    )

    assert wait_until(
        linode_id=linode_id, timeout=240, status="running"
    ), "Linode status has not changed to running from provisioning after reboot"


@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_shutdown_linode(linode_instance_basic):
    linode_id = linode_instance_basic

    # returns false if status is not running after 240s after reboot
    assert wait_until(
        linode_id=linode_id, timeout=240, status="running"
    ), "Linode status has not changed to running from provisioning"

    # shutdown linode that is in running state
    exec_test_command(BASE_CMDS["linodes"] + ["shutdown", linode_id])

    result = wait_until(linode_id=linode_id, timeout=180, status="offline")

    assert result, "Linode status has not changed to running from offline"
