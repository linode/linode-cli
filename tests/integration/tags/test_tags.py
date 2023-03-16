import pytest
import time
from tests.integration.helpers import *

BASE_CMD = ['linode-cli', 'tags']
unique_tag = str(int(time.time()))+'-tag'


@pytest.fixture(scope="session", autouse=True)
def setup_test_tags():
    yield "setup"


def test_display_tags():
    exec_test_command(BASE_CMD+['list'])


@pytest.fixture(scope="session")
def test_create_tag():
    exec_test_command(BASE_CMD+['create', '--label', unique_tag, '--text', '--no-headers']).stdout.decode()
    yield unique_tag


def test_view_unique_tag(test_create_tag):
    result = exec_test_command(BASE_CMD+['list', '--text', '--no-headers']).stdout.decode()
    assert(test_create_tag in result)


def test_fail_to_create_tag_shorter_than_three_char():
    bad_tag = 'aa'
    result = exec_failing_test_command(BASE_CMD+['create', '--label', bad_tag, '--text', '--no-headers']).stderr.decode()
    assert("Request failed: 400" in result)
    assert("Length must be 3-50 characters" in result)


def test_remove_tag(test_create_tag):
    exec_test_command(BASE_CMD+['delete', test_create_tag])




