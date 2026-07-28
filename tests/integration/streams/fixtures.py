import os
from typing import Any, Dict

import pytest
import requests

from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_test_command,
    get_random_region_with_caps,
    get_random_text,
)


def get_object_storage_buckets() -> Dict[str, Any]:
    token = os.getenv("LINODE_CLI_TOKEN")
    if token is None:
        raise ValueError("LINODE_CLI_TOKEN environment variable is not set. ")
    host = os.getenv("LINODE_CLI_API_HOST")
    if token is None:
        raise ValueError(
            "LINODE_CLI_API_HOST environment variable is not set. "
        )
    version = os.getenv("LINODE_CLI_API_VERSION")
    if token is None:
        raise ValueError(
            "LINODE_CLI_API_VERSION environment variable is not set. "
        )

    url = f"https://{host}/{version}/object-storage/buckets"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    return response.json()


@pytest.fixture(scope="session")
def create_stream(create_destination_akamai_object_storage_type):
    label = get_random_text(8) + "_stream_cli_test"
    result_create_stream = exec_test_command(
        BASE_CMDS["streams"]
        + [
            "create",
            "--label",
            label,
            "--type",
            "audit_logs",
            "--destinations",
            create_destination_akamai_object_storage_type[0],
            "--delimiter",
            ",",
            "--text",
        ]
    ).splitlines()
    yield result_create_stream
    delete_target_id("streams", str(result_create_stream[1]), "delete")


@pytest.fixture
def create_object_storage_keys():
    label = get_random_text(8) + "_destination_cli_test"
    test_bucket = get_object_storage_buckets()["data"][0]
    result_keys = exec_test_command(
        BASE_CMDS["object-storage"]
        + [
            "keys-create",
            "--label",
            label,
            "--bucket_access",
            '[{"region": "'
            + test_bucket["region"]
            + '", "bucket_name": "'
            + test_bucket["label"]
            + '", "permissions": "read_write" }]',
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "access_key,secret_key,id",
        ]
    ).split(",")
    yield result_keys[0], result_keys[1], test_bucket["label"], test_bucket["s3_endpoint"]
    delete_target_id("object-storage", str(result_keys[2]), "keys-delete")


@pytest.fixture(scope="function")
def create_destination_akamai_object_storage_type(create_object_storage_keys):
    get_random_region_with_caps(required_capabilities=["Linodes"])

    label = get_random_text(8) + "_destination_cli_test"
    result_create_destination = exec_test_command(
        BASE_CMDS["streams"]
        + [
            "destination-create",
            "--label",
            label,
            "--type",
            "akamai_object_storage",
            "--details.host",
            create_object_storage_keys[3],
            "--details.bucket_name",
            create_object_storage_keys[2],
            "--details.path",
            "audit-logs",
            "--details.access_key_secret",
            create_object_storage_keys[1],
            "--details.access_key_id",
            create_object_storage_keys[0],
            "--delimiter",
            ",",
            "--text",
        ]
    ).splitlines()
    yield result_create_destination
    delete_target_id(
        "streams", str(result_create_destination[0]), "destination-delete"
    )
