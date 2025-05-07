from tests.integration.helpers import (
    exec_test_command,
)


def get_first_image_id():
    image_id = exec_test_command(
        [
            "linode-cli",
            "images",
            "list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_id = image_id[0].split(",")[0]

    return first_id
