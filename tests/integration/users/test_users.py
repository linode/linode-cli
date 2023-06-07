import time

import pytest

from tests.integration.helpers import exec_test_command

BASE_CMD = ["linode-cli", "users"]
unique_user = "test-user-" + str(int(time.time()))


@pytest.fixture(scope="package", autouse=True)
def setup_test_users():
    yield "setup"
    remove_users()


def remove_users():
    exec_test_command(BASE_CMD + ["delete", unique_user])


@pytest.fixture
def test_create_user():
    exec_test_command(
        BASE_CMD
        + [
            "create",
            "--username",
            unique_user,
            "--email",
            unique_user + "@linode.com",
            "--restricted",
            "true",
            "--text",
            "--no-headers",
        ]
    )


def test_display_users():
    exec_test_command(BASE_CMD + ["list"])


@pytest.mark.usefixtures("test_create_user")
def test_view_user():
    exec_test_command(BASE_CMD + ["view", unique_user])
