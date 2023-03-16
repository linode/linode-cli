import logging
import pytest
from tests.integration.linodes.helpers_linodes import *


@pytest.fixture(scope="session", autouse=True)
def setup_power_status():
    #create linode
    try:
        linode_id = create_linode()
    except:
        logging.exception("Failed in creating linode in setup..")
    yield linode_id
    try:
        # clean up
        remove_linodes()
    except:
        logging.exception("Failed removing all linodes..")


def test_create_linode_and_boot():
    output = exec_test_command(
        BASE_CMD + ['list', '--format=id', '--delimiter', ',', '--text', '--no-headers']).stdout.decode().rstrip()
    linode_arr = output.splitlines()
    linode_id = linode_arr[0]

    # returns false if status is not running after 240s
    result = wait_until(linode_id=linode_id, timeout=240, status="running")

    assert result, "Linode status has not changed to running from provisioning"


def test_reboot_linode():
    # create linode and wait until it is in "running" state
    linode_id = create_linode_and_wait()

    # reboot linode from "running" status
    exec_test_command(BASE_CMD+['reboot', linode_id, '--text', '--no-headers'])

    # returns false if status is not running after 240s after reboot
    assert wait_until(linode_id=linode_id, timeout=240, status="running"), "Linode status has not changed to running from provisioning"


def test_shutdown_linode():
    output = exec_test_command(
        BASE_CMD + ['list', '--format=id', '--delimiter', ',', '--text', '--no-headers']).stdout.decode().rstrip()
    linode_arr = output.splitlines()
    linode_id = linode_arr[0]

    # returns false if status is not running after 240s after reboot
    assert wait_until(linode_id=linode_id, timeout=240, status="running"), "Linode status has not changed to running from provisioning"

    # shutdown linode that is in running state
    exec_test_command(BASE_CMD+['shutdown', linode_id])

    result = wait_until(linode_id=linode_id, timeout=180, status="offline")

    assert(result, "Linode status has not changed to running from offline")

