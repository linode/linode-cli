import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

import pytest
import requests
from fixture_types import GetTestFileType
from helpers import BASE_URL
from pytest import MonkeyPatch

from linodecli.configuration.auth import _do_request
from linodecli.plugins.obj import ENV_ACCESS_KEY_NAME, ENV_SECRET_KEY_NAME

REGION = "us-southeast-1"
BASE_CMD = ["linode-cli", "obj", "--cluster", REGION]


@dataclass
class Keys:
    access_key: str
    secret_key: str


@pytest.fixture(scope="session")
def keys(token: str):
    response = _do_request(
        BASE_URL,
        requests.post,
        "object-storage/keys",
        token,
        False,
        {"label": "cli-integration-test-obj-key"},
    )

    _keys = Keys(
        access_key=response.get("access_key"),
        secret_key=response.get("secret_key"),
    )
    yield _keys
    _do_request(
        BASE_URL,
        requests.delete,
        f"object-storage/keys/{response['id']}",
        token,
    )


def patch_keys(keys: Keys, monkeypatch: MonkeyPatch):
    assert keys.access_key is not None
    assert keys.secret_key is not None
    monkeypatch.setenv(ENV_ACCESS_KEY_NAME, keys.access_key)
    monkeypatch.setenv(ENV_SECRET_KEY_NAME, keys.secret_key)


def exec_test_command(args: List[str]):
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
    )
    assert process.returncode == 0
    return process


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
        except:
            logging.exception(f"Failed to cleanup bucket: {bk}")


def delete_bucket(bucket_name: str, force: bool = True):
    args = BASE_CMD + ["rb", bucket_name]
    if force:
        args.append("--recursive")
    exec_test_command(args)
    return bucket_name


def test_obj_single_file_single_bucket(
    create_bucket: Callable[[Optional[str]], str],
    generate_test_files: GetTestFileType,
    keys: Keys,
    monkeypatch: MonkeyPatch,
):
    patch_keys(keys, monkeypatch)
    file_path = generate_test_files()[0]
    bucket_name = create_bucket()
    exec_test_command(BASE_CMD + ["put", str(file_path), bucket_name])
    process = exec_test_command(BASE_CMD + ["la"])
    output = process.stdout.decode()

    assert f"{bucket_name}/{file_path.name}" in output

    file_size = file_path.stat().st_size
    assert str(file_size) in output

    process = exec_test_command(BASE_CMD + ["ls"])
    output = process.stdout.decode()
    assert bucket_name in output
    assert file_path.name not in output

    process = exec_test_command(BASE_CMD + ["ls", bucket_name])
    output = process.stdout.decode()
    assert bucket_name not in output
    assert str(file_size) in output
    assert file_path.name in output

    downloaded_file_path = Path.cwd() / f"downloaded_{file_path.name}"
    process = exec_test_command(
        BASE_CMD
        + ["get", bucket_name, file_path.name, downloaded_file_path.name]
    )
    output = process.stdout.decode()
    with open(downloaded_file_path) as f2, open(file_path) as f1:
        assert f1.read() == f2.read()

    downloaded_file_path.unlink()
    file_path.unlink()


def test_multi_files_multi_bucket(
    create_bucket: Callable[[Optional[str]], str],
    generate_test_files: GetTestFileType,
    keys: Keys,
    monkeypatch: MonkeyPatch,
):
    patch_keys(keys, monkeypatch)
    number = 5
    bucket_names = [create_bucket() for _ in range(number)]
    file_paths = generate_test_files(number)
    for bucket in bucket_names:
        for file in file_paths:
            process = exec_test_command(
                BASE_CMD + ["put", str(file.resolve()), bucket]
            )
            output = process.stdout.decode()
            assert "100.0%" in output
            assert "Done" in output
    for file in file_paths:
        file.unlink()


def test_modify_access_control(
    keys: Keys,
    monkeypatch: MonkeyPatch,
    create_bucket: Callable[[Optional[str]], str],
    generate_test_files: GetTestFileType,
):
    patch_keys(keys, monkeypatch)
    bucket = create_bucket()
    file = generate_test_files()[0]
    exec_test_command(BASE_CMD + ["put", str(file.resolve()), bucket])
    file_url = f"https://{bucket}.{REGION}.linodeobjects.com/{file.name}"
    exec_test_command(BASE_CMD + ["setacl", bucket, file.name, "--acl-public"])
    response = requests.get(file_url)
    assert response.status_code == 200
    exec_test_command(BASE_CMD + ["setacl", bucket, file.name, "--acl-private"])
    response = requests.get(file_url)
    assert response.status_code == 403
