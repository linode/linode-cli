import re
import time

from tests.integration.helpers import (
    delete_tag,
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
)

BASE_CMD = ["linode-cli", "domains"]


# @pytest.mark.skip(reason="BUG 943")
def test_fail_to_create_master_domain_with_invalid_tags():
    timestamp = str(int(time.time()))
    bad_tag = "*"

    exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--type",
            "master",
            "--domain",
            timestamp + "example.com",
            "--soa_email=" + timestamp + "pthiel@linode.com",
            "--text",
            "--no-header",
            "--format=id",
            "--tag",
            bad_tag,
        ]
    )


# @pytest.mark.skip(reason="BUG 943")
def test_fail_to_create_slave_domain_with_invalid_tags():
    timestamp = str(int(time.time()))
    bad_tag = "*"

    exec_failing_test_command(
        BASE_CMD
        + [
            "create",
            "--type",
            "slave",
            "--domain",
            timestamp + "example.com",
            "--soa_email=" + timestamp + "pthiel@linode.com",
            "--text",
            "--no-header",
            "--format=id",
            "--tag",
            bad_tag,
        ]
    )


# @pytest.mark.skip(reason="BUG 943")
def test_create_master_domain_with_tags():
    timestamp = str(int(time.time()))
    tag = "foo"

    process = exec_test_command(
        BASE_CMD
        + [
            "create",
            "--type",
            "master",
            "--domain",
            timestamp + "-example.com",
            "--soa_email=" + timestamp + "pthiel@linode.com",
            "--text",
            "--no-header",
            "--delimiter=,",
            "--format=id,domain,type,status,tags",
            "--tag",
            tag,
        ]
    )
    output = process.stdout.decode().rstrip()
    assert re.search("[0-9]+,[0-9]+-example.com,master,active," + tag, output)

    res_arr = output.split(",")
    domain_id = res_arr[0]
    delete_target_id(target="domains", id=domain_id)


# @pytest.mark.skip(reason="BUG 943")
def test_delete_domain_and_tag():
    timestamp = str(int(time.time()))
    tag = "zoo"

    domain_id = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--type",
                "master",
                "--domain",
                timestamp + "-example.com",
                "--soa_email=" + timestamp + "pthiel@linode.com",
                "--text",
                "--no-header",
                "--delimiter=,",
                "--format=id",
                "--tag",
                tag,
            ]
        )
        .stdout.decode()
        .rstrip()
    )
    # need to check if tag foo is still present while running this test
    result = exec_test_command(["linode-cli", "tags", "list"]).stdout.decode()

    if "zoo" in result:
        delete_tag("zoo")
        delete_target_id(target="domains", id=domain_id)
