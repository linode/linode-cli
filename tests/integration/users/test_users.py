import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
    get_random_text,
)

BASE_CMD = ["linode-cli", "users"]
unique_user = "test-user-" + get_random_text(5)


@pytest.fixture(scope="package", autouse=True)
def teardown_fixture():
    yield "setup"
    exec_test_command(BASE_CMDS["users"] + ["delete", unique_user])


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
    exec_test_command(BASE_CMDS["users"] + ["list"])


@pytest.mark.smoke
@pytest.mark.usefixtures("test_create_user")
def test_view_user():
    exec_test_command(BASE_CMDS["users"] + ["view", unique_user])
