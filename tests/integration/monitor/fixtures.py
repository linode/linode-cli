import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
)


@pytest.fixture
def get_service_type():
    service_ids = exec_test_command(
        BASE_CMDS["monitor"]
        + [
            "service-list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "service_type",
        ]
    ).splitlines()
    first_id = service_ids[0].split(",")[0]
    yield first_id
