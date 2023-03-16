import re

import pytest
import time
from tests.integration.helpers import *

BASE_CMD = ['linode-cli', 'volumes']
timestamp = str(int(time.time()))
unique_tag = str(int(time.time()))+'-tag'


@pytest.fixture(scope="session", autouse=True)
def setup_test_volumes():
    remove_all(target="volumes")
    yield "setup"
    remove_all(target="tags")
    remove_all(target="volumes")


def get_volume_id():
    volume_id = os.popen('linode-cli volumes list --text --no-headers --delimiter="," --format="id" | head -n1').read().rstrip()
    return volume_id


def test_fail_to_create_volume_under_10gb():
    result = exec_failing_test_command(BASE_CMD+['create', '--label', "A"+timestamp, '--region', 'us-east', '--size', '5', '--text', '--no-headers']).stderr.decode()

    if "test" == os.environ.get("TEST_ENVIRONMENT", None) or "dev" == os.environ.get("TEST_ENVIRONMENT", None):
        assert("size	Must be 10-1024" in result)
    else:
        assert("size	Must be 10-10240" in result)


def test_fail_to_create_volume_without_region():
    result = exec_failing_test_command(BASE_CMD+['create', '--label', "A"+timestamp, '--size', '10', '--text', '--no-headers']).stderr.decode()
    assert("Request failed: 400" in result)
    assert("Must provide a region or a Linode ID" in result)


def test_fail_to_create_volume_without_label():
    result = exec_failing_test_command(BASE_CMD+['create', '--region', 'us-east', '--size', '10', '--text', '--no-headers']).stderr.decode()
    assert("Request failed: 400" in result)
    assert("label	label is required" in result)


def test_fail_to_create_volume_over_1024gb_in_size():
    result = exec_failing_test_command(BASE_CMD+['create', '--label', "A"+timestamp, '--region', 'us-east', '--size', '10241', '--text', '--no-headers']).stderr.decode()
    if "test" == os.environ.get("TEST_ENVIRONMENT", None) or "dev" == os.environ.get("TEST_ENVIRONMENT", None):
        assert("size	Must be 10-1024" in result)
    else:
        assert("size	Must be 10-10240" in result)


def test_fail_to_create_volume_with_all_numberic_label():
    result = exec_failing_test_command(BASE_CMD+['create', '--label', "11111", '--region', 'us-east', '--size', '10', '--text', '--no-headers']).stderr.decode()
    assert("Request failed: 400" in result)
    assert("label	Must begin with a letter" in result)


@pytest.fixture(scope="session")
def test_create_unattached_volume():
    result = exec_test_command(BASE_CMD+['create', '--label', "A"+timestamp, '--region', 'us-east', '--size', '10', '--text', '--no-headers']).stdout.decode()
    assert(re.search("[0-9]+,A[0-9]+,creating,10,us-east" in result))


@pytest.mark.usesfixture('test_create_unattached_volume')
def test_list_volume():
    result = exec_test_command(BASE_CMD+['list', '--text', '--no-headers', '--delimiter', ',']).stdout.decode()
    assert(re.search("[0-9]+,[A-Za-z0-9]+,(creating|active|offline),10,[a-z-]+", result))


def test_view_single_volume():
    volume_id = get_volume_id()
    result = exec_test_command(BASE_CMD+['view', volume_id, '--text', '--no-headers', '--delimiter', ',', '--format', 'id,label,size,region']).stdout.decode()

    assert(re.search(volume_id+",[A-Za-z0-9-]+,[0-9]+,[a-z-]+", result))


def test_update_volume_label():
    volume_id = get_volume_id()
    result = exec_test_command(BASE_CMD+['update', volume_id, '--label', 'A-NewLabel-2', '--format', 'label', '--text', '--no-headers']).stdout.decode()

    assert('A-NewLabel-2' in result)


def test_add_new_tag_to_volume():
    volume_id = get_volume_id()
    result = exec_test_command(BASE_CMD+['update', volume_id, '--tag', unique_tag, '--format', 'tags', '--text', '--no-headers']).stdout.decode()

    assert(unique_tag in result)


def test_view_tags_attached_to_volume():
    volume_id = get_volume_id()
    exec_test_command(BASE_CMD+['view', volume_id, '--format', 'tags', '--text', '--no-headers']).stdout.decode()


def test_fail_to_update_volume_size():
    volume_id = get_volume_id()
    os.system('linode-cli volumes update --size=15 ' + volume_id + ' 2>&1 | tee /tmp/output_file.txt')

    result = os.popen("cat /tmp/output_file.txt").read()

    assert("linode-cli volumes update: error: unrecognized arguments: --size=15" in result)
