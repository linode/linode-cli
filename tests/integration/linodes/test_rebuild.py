import logging
import pytest
from tests.integration.linodes.helpers_linodes import *


@pytest.fixture(scope="session", autouse=True)
def setup_rebuild():
    # create linode
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


def test_rebuild_fails_without_image():
    linode_id = create_linode_and_wait()

    result = exec_failing_test_command(BASE_CMD+['rebuild', '--root_pass', DEFAULT_RANDOM_PASS, linode_id, '--text', '--no-headers']).stderr.decode()

    assert('Request failed: 400' in result)
    assert('You must specify an image' in result)


def test_rebuild_fails_with_invalid_image():
    linode_id = os.popen('linode-cli linodes list --format id --text --no-header | head -n 1').read().rstrip()
    rebuild_image = "bad/image"

    result = exec_failing_test_command(BASE_CMD+['rebuild', '--image', rebuild_image, '--root_pass', DEFAULT_RANDOM_PASS, linode_id, '--text', '--no-headers']).stderr.decode()

    assert('Request failed: 400' in result)


@pytest.mark.skipif(os.environ.get("RUN_LONG_TESTS", None) != "TRUE", reason="Skipping long-running Test, to run set RUN_LONG_TESTS=TRUE")
def test_rebuild_a_linode():
    linode_id = create_linode_and_wait()
    rebuild_image = os.popen('linode-cli images list --text --no-headers --format=id | sed -n 3p').read().rstrip()

    # trigger rebuild
    exec_test_command(BASE_CMD+['rebuild', '--image', rebuild_image, '--root_pass', DEFAULT_RANDOM_PASS, '--text', '--no-headers', linode_id]).stdout.decode()

    # check status for rebuilding
    assert wait_until(linode_id=linode_id, timeout=180, status="rebuilding"), "linode failed to change status to rebuilding.."

    # check if rebuilding finished
    assert wait_until(linode_id=linode_id, timeout=180, status="running"), "linode failed to change status to running from rebuilding.."

    result = exec_test_command(BASE_CMD+['view', linode_id, '--format', 'image', '--text', '--no-headers']).stdout.decode()
    assert(rebuild_image in result)
