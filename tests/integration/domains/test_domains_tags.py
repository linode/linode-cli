import os
import time
import re
import pytest
import logging

from tests.integration.helpers import exec_test_command, exec_failing_test_command, delete_all_domains, delete_tag, FAILED_STATUS_CODE

BASE_CMD = ["linode-cli", "domains"]


@pytest.fixture(scope="session", autouse=True)
def domain_tags_setup():
    yield "setup"
    try:
        delete_all_domains()
    except:
        logging.exception("Failed to delete all domains")


# @pytest.mark.skip(reason="BUG 943")
def test_fail_to_create_master_domain_with_invalid_tags():
    timestamp = str(int(time.time()))
    bad_tag = '*'

    exec_failing_test_command(BASE_CMD + ['create', '--type', 'master', '--domain', timestamp + "example.com",
                                            '--soa_email='+timestamp+'pthiel@linode.com', '--text', '--no-header', '--format=id', '--tag', bad_tag])


# @pytest.mark.skip(reason="BUG 943")
def test_fail_to_create_slave_domain_with_invalid_tags():
    timestamp = str(int(time.time()))
    bad_tag = "*"

    exec_failing_test_command(BASE_CMD + ['create', '--type', 'slave', '--domain', timestamp + "example.com",
                                            '--soa_email='+timestamp+'pthiel@linode.com', '--text', '--no-header', '--format=id', '--tag', bad_tag])


# @pytest.mark.skip(reason="BUG 943")
def test_create_master_domain_with_tags():
    timestamp = str(int(time.time()))
    tag = "foo"

    process = exec_test_command(BASE_CMD + ['create', '--type', 'master', '--domain', timestamp + "-example.com",
                                            '--soa_email='+timestamp+'pthiel@linode.com', '--text', '--no-header', '--delimiter=,', '--format=id,domain,type,status,tags', '--tag', tag])
    output = process.stdout.decode()
    assert(re.search("[0-9]+,[0-9]+-example.com,master,active,"+tag, output))


# @pytest.mark.skip(reason="BUG 943")
def test_delete_domain_and_tag():
    # need to check if tag foo is still present while running this test
    result = exec_test_command(['linode-cli', 'tags', 'list']).stdout.decode()
    if "foo" in result:
        delete_tag("foo")
        delete_all_domains()
    else:
        delete_all_domains()


