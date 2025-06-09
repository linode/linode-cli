import re

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
)


def test_fail_to_create_master_domain_with_invalid_tags():
    bad_tag = (
        "a" * 300
    )  # Tag validation rules changed — '*' is no longer rejected

    exec_failing_test_command(
        BASE_CMDS["domains"]
        + [
            "create",
            "--type",
            "master",
            "--domain",
            get_random_text(5) + "example.com",
            "--soa_email=" + get_random_text(5) + "pthiel@linode.com",
            "--text",
            "--no-header",
            "--format=id",
            "--tag",
            bad_tag,
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )


def test_fail_to_create_slave_domain_with_invalid_tags():
    bad_tag = "*"

    exec_failing_test_command(
        BASE_CMDS["domains"]
        + [
            "create",
            "--type",
            "slave",
            "--domain",
            get_random_text(5) + "example.com",
            "--soa_email=" + get_random_text(5) + "pthiel@linode.com",
            "--text",
            "--no-header",
            "--format=id",
            "--tag",
            bad_tag,
        ],
        expected_code=ExitCodes.REQUEST_FAILED,
    )


@pytest.mark.smoke
def test_create_master_domain_with_tags():
    tag = "foo"

    output = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "create",
            "--type",
            "master",
            "--domain",
            get_random_text(5) + "-example.com",
            "--soa_email=" + get_random_text(5) + "pthiel@linode.com",
            "--text",
            "--no-header",
            "--delimiter=,",
            "--format=id,domain,type,status,tags",
            "--tag",
            tag,
        ]
    )

    assert re.search(
        r"\d+,[^,]*-example\.com,master,active," + re.escape(tag), output
    )

    res_arr = output.split(",")
    domain_id = res_arr[0]
    delete_target_id(target="domains", id=domain_id)


def test_delete_domain_and_tag():
    tag = "zoo"

    domain_id = exec_test_command(
        BASE_CMDS["domains"]
        + [
            "create",
            "--type",
            "master",
            "--domain",
            get_random_text(5) + "-example.com",
            "--soa_email=" + get_random_text(5) + "pthiel@linode.com",
            "--text",
            "--no-header",
            "--delimiter=,",
            "--format=id",
            "--tag",
            tag,
        ]
    )
    # need to check if tag foo is still present while running this test
    result = exec_test_command(["linode-cli", "tags", "list"])

    if "zoo" in result:
        delete_target_id(target="tags", id="zoo")
        delete_target_id(target="domains", id=domain_id)
