import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

import pytest
from pytest import MonkeyPatch

from linodecli.plugins.obj import ENV_ACCESS_KEY_NAME, ENV_SECRET_KEY_NAME
from tests.integration.helpers import (
    BASE_CMDS,
    exec_test_command,
    get_random_text,
)

REGION = "us-southeast-1"
BASE_CMD = ["linode-cli", "obj", "--cluster", REGION]

"""
Complicated type alias for fixtures and other stuff.
"""

GetTestFilesType = Callable[[Optional[int], Optional[str]], List[Path]]
GetTestFileType = Callable[[Optional[str], Optional[str], Optional[int]], Path]


@dataclass
class Keys:
    access_key: str
    secret_key: str


def patch_keys(keys: Keys, monkeypatch: MonkeyPatch):
    assert keys.access_key is not None
    assert keys.secret_key is not None
    monkeypatch.setenv(ENV_ACCESS_KEY_NAME, keys.access_key)
    monkeypatch.setenv(ENV_SECRET_KEY_NAME, keys.secret_key)


def delete_bucket(bucket_name: str, force: bool = True):
    args = BASE_CMD + ["rb", bucket_name]
    if force:
        args.append("--recursive")
    exec_test_command(args)
    return bucket_name


@pytest.fixture
def create_bucket(
    name_generator: Callable, keys: Keys, monkeypatch: MonkeyPatch
):
    created_buckets = set()
    patch_keys(keys, monkeypatch)

    def _create_bucket(bucket_name: Optional[str] = None):
        if not bucket_name:
            bucket_name = name_generator("test-bk")

        exec_test_command(BASE_CMD + ["mb", bucket_name])
        created_buckets.add(bucket_name)
        return bucket_name

    yield _create_bucket
    for bk in created_buckets:
        try:
            delete_bucket(bk)
        except Exception as e:
            logging.exception(f"Failed to cleanup bucket: {bk}, {e}")


@pytest.fixture
def static_site_index():
    return (
        "<!DOCTYPE html>"
        "<html><head>"
        "<title>Hello World</title>"
        "</head><body>"
        "<p>Hello, World!</p>"
        "</body></html>"
    )


@pytest.fixture
def static_site_error():
    return (
        "<!DOCTYPE html>"
        "<html><head>"
        "<title>Error</title>"
        "</head><body>"
        "<p>Error!</p>"
        "</body></html>"
    )


@pytest.fixture(scope="session")
def keys():
    response = json.loads(
        exec_test_command(
            BASE_CMDS["object-storage"]
            + [
                "keys-create",
                "--label",
                "cli-integration-test-obj-key",
                "--json",
            ],
        )
    )[0]
    _keys = Keys(
        access_key=response.get("access_key"),
        secret_key=response.get("secret_key"),
    )
    yield _keys
    exec_test_command(
        BASE_CMDS["object-storage"] + ["keys-delete", str(response.get("id"))]
    )


@pytest.fixture(scope="session")
def test_key():
    label = get_random_text(10)
    key = exec_test_command(
        BASE_CMDS["object-storage"]
        + [
            "keys-create",
            "--label",
            label,
            "--text",
            "--no-headers",
            "--format=id",
        ]
    )

    yield key

    exec_test_command(BASE_CMDS["object-storage"] + ["keys-delete", key])
