import json

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    exec_failing_test_command,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
)


def test_arg_raw_body():
    label = get_random_text(12)
    region = get_random_region_with_caps(["VPCs"])

    res = json.loads(
        exec_test_command(
            [
                "linode-cli",
                "vpcs",
                "create",
                "--json",
                "--raw-body",
                json.dumps(
                    {
                        "label": label,
                        "region": region,
                    }
                ),
            ],
        )
    )

    exec_test_command(["linode-cli", "vpcs", "delete", str(res[0]["id"])])

    assert res[0]["id"] > 0
    assert res[0]["label"] == label
    assert res[0]["region"] == region


def test_arg_raw_body_conflict():
    label = get_random_text(12)
    region = get_random_region_with_caps(["VPCs"])

    res = exec_failing_test_command(
        [
            "linode-cli",
            "vpcs",
            "create",
            "--json",
            "--label",
            label,
            "--region",
            region,
            "--raw-body",
            json.dumps(
                {
                    "label": label,
                    "region": region,
                }
            ),
        ],
        expected_code=ExitCodes.ARGUMENT_ERROR,
    )

    assert (
        "--raw-body cannot be specified with action arguments: --label, --region"
        in res
    )


def test_arg_raw_body_get():
    res = exec_failing_test_command(
        [
            "linode-cli",
            "vpcs",
            "list",
            "--json",
            "--raw-body",
            json.dumps({"label": "test"}),
        ],
        expected_code=ExitCodes.ARGUMENT_ERROR,
    )

    assert "--raw-body cannot be specified for actions with method get" in res
