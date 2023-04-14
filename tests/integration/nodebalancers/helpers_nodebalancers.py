import pytest

from tests.integration.helpers import delete_target_id, exec_test_command

BASE_CMD = ["linode-cli", "nodebalancers"]


@pytest.fixture
def create_nodebalancer_with_default_conf():
    result = (
        exec_test_command(
            BASE_CMD
            + [
                "create",
                "--region",
                "us-east",
                "--text",
                "--delimiter",
                ",",
                "--format",
                "id,label,region,hostname,client_conn_throttle",
                "--suppress-warnings",
                "--no-headers",
            ]
        )
        .stdout.decode()
        .rstrip()
    )

    yield result

    res_arr = result.split(",")
    nodebalancer_id = res_arr[0]
    delete_target_id(target="nodebalancers", id=nodebalancer_id)
