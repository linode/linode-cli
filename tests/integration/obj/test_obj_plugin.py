import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Callable, Optional
from unittest.mock import patch

import pytest
import requests
from pytest import MonkeyPatch

from linodecli.plugins.obj.list import TRUNCATED_MSG
from tests.integration.helpers import count_lines, exec_test_command
from tests.integration.obj.conftest import (
    BASE_CMD,
    REGION,
    GetTestFilesType,
    GetTestFileType,
    Keys,
    patch_keys,
)


def test_obj_single_file_single_bucket(
    create_bucket: Callable[[Optional[str]], str],
    generate_test_files: GetTestFilesType,
    keys: Keys,
    monkeypatch: MonkeyPatch,
):
    patch_keys(keys, monkeypatch)
    file_path = generate_test_files()[0]
    bucket_name = create_bucket()
    exec_test_command(BASE_CMD + ["put", str(file_path), bucket_name])
    process = exec_test_command(BASE_CMD + ["la"])
    output = process

    assert f"{bucket_name}/{file_path.name}" in output

    file_size = file_path.stat().st_size
    assert str(file_size) in output

    process = exec_test_command(BASE_CMD + ["ls"])
    output = process
    assert bucket_name in output
    assert file_path.name not in output

    process = exec_test_command(BASE_CMD + ["ls", bucket_name])
    output = process
    assert bucket_name not in output
    assert str(file_size) in output
    assert file_path.name in output

    downloaded_file_path = file_path.parent / f"downloaded_{file_path.name}"
    exec_test_command(
        BASE_CMD
        + ["get", bucket_name, file_path.name, str(downloaded_file_path)]
    )

    with open(downloaded_file_path) as f2, open(file_path) as f1:
        assert f1.read() == f2.read()


def test_obj_single_file_single_bucket_with_prefix(
    create_bucket: Callable[[Optional[str]], str],
    generate_test_files: GetTestFilesType,
    keys: Keys,
    monkeypatch: MonkeyPatch,
):
    patch_keys(keys, monkeypatch)
    file_path = generate_test_files()[0]
    bucket_name = create_bucket()
    exec_test_command(
        BASE_CMD + ["put", str(file_path), f"{bucket_name}/prefix"]
    )
    output = exec_test_command(BASE_CMD + ["la"])

    assert f"{bucket_name}/prefix/{file_path.name}" in output

    file_size = file_path.stat().st_size
    assert str(file_size) in output

    output = exec_test_command(BASE_CMD + ["ls"])
    assert bucket_name in output
    assert file_path.name not in output

    output = exec_test_command(BASE_CMD + ["ls", bucket_name])
    assert bucket_name not in output
    assert "prefix" in output

    downloaded_file_path = file_path.parent / f"downloaded_{file_path.name}"
    exec_test_command(
        BASE_CMD
        + [
            "get",
            bucket_name,
            "prefix/" + file_path.name,
            str(downloaded_file_path),
        ]
    )
    with open(downloaded_file_path) as f2, open(file_path) as f1:
        assert f1.read() == f2.read()


def test_obj_single_file_single_bucket_with_prefix_ltrim(
    create_bucket: Callable[[Optional[str]], str],
    generate_test_files: GetTestFilesType,
    keys: Keys,
    monkeypatch: MonkeyPatch,
):
    patch_keys(keys, monkeypatch)
    file_path = generate_test_files()[0]
    bucket_name = create_bucket()
    # using 'bk' in prefix to test out ltrim behaviour (bucket contains 'bk')
    exec_test_command(
        BASE_CMD + ["put", str(file_path), f"{bucket_name}/bkprefix"]
    )
    output = exec_test_command(BASE_CMD + ["la"])

    assert f"{bucket_name}/bkprefix/{file_path.name}" in output

    file_size = file_path.stat().st_size
    assert str(file_size) in output

    output = exec_test_command(BASE_CMD + ["ls"])
    assert bucket_name in output
    assert file_path.name not in output

    output = exec_test_command(BASE_CMD + ["ls", bucket_name])
    assert bucket_name not in output
    assert "bkprefix" in output

    downloaded_file_path = file_path.parent / f"downloaded_{file_path.name}"
    output = exec_test_command(
        BASE_CMD
        + [
            "get",
            bucket_name,
            "bkprefix/" + file_path.name,
            str(downloaded_file_path),
        ]
    )
    with open(downloaded_file_path) as f2, open(file_path) as f1:
        assert f1.read() == f2.read()


def test_multi_files_multi_bucket(
    create_bucket: Callable[[Optional[str]], str],
    generate_test_files: GetTestFilesType,
    keys: Keys,
    monkeypatch: MonkeyPatch,
):
    patch_keys(keys, monkeypatch)
    number = 5
    bucket_names = [create_bucket() for _ in range(number)]
    file_paths = generate_test_files(number)
    for bucket in bucket_names:
        for file in file_paths:
            output = exec_test_command(
                BASE_CMD + ["put", str(file.resolve()), bucket]
            )
            assert "100.0%" in output
            assert "Done" in output


@pytest.mark.parametrize("num_files", [1005])
def test_large_number_of_files_single_bucket_parallel(
    create_bucket: Callable[[Optional[str]], str],
    generate_test_files: GetTestFilesType,
    keys: Keys,
    monkeypatch: MonkeyPatch,
    num_files: int,
):
    patch_keys(keys, monkeypatch)

    bucket_name = create_bucket()
    file_paths = generate_test_files(num_files)

    with ThreadPoolExecutor(50) as executor:
        futures = [
            executor.submit(
                exec_test_command,
                BASE_CMD + ["put", str(file.resolve()), bucket_name],
            )
            for file in file_paths
        ]

        wait(futures)


def test_all_rows(
    create_bucket: Callable[[Optional[str]], str],
    generate_test_files: GetTestFilesType,
    keys: Keys,
    monkeypatch: MonkeyPatch,
):
    patch_keys(keys, monkeypatch)
    number = 5
    bucket_name = create_bucket()
    file_paths = generate_test_files(number)

    output = exec_test_command(
        BASE_CMD
        + ["put"]
        + [str(file.resolve()) for file in file_paths]
        + [bucket_name]
    )
    assert "100.0%" in output
    assert "Done" in output

    output = exec_test_command(
        BASE_CMD + ["ls", bucket_name, "--page-size", "2", "--page", "1"]
    )
    assert TRUNCATED_MSG in output
    assert count_lines(output) == 3

    output = exec_test_command(
        BASE_CMD + ["ls", bucket_name, "--page-size", "999"]
    )
    assert TRUNCATED_MSG not in output
    assert count_lines(output) == 5

    output = exec_test_command(
        BASE_CMD + ["ls", bucket_name, "--page-size", "2", "--all-rows"]
    )
    assert TRUNCATED_MSG not in output
    assert count_lines(output) == 5


def test_modify_access_control(
    keys: Keys,
    monkeypatch: MonkeyPatch,
    create_bucket: Callable[[Optional[str]], str],
    generate_test_files: GetTestFilesType,
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


def test_static_site(
    keys: Keys,
    monkeypatch: MonkeyPatch,
    generate_test_file: GetTestFileType,
    static_site_index: str,
    static_site_error: str,
    create_bucket: Callable[[Optional[str]], str],
):
    patch_keys(keys, monkeypatch)
    index_file = generate_test_file(static_site_index, "index.html").resolve()
    error_file = generate_test_file(static_site_error, "error.html").resolve()
    bucket = create_bucket()
    exec_test_command(
        BASE_CMD + ["put", str(index_file), bucket, "--acl-public"]
    )
    exec_test_command(
        BASE_CMD + ["put", str(error_file), bucket, "--acl-public"]
    )

    exec_test_command(
        BASE_CMD
        + [
            "ws-create",
            "--ws-index",
            index_file.name,
            "--ws-error",
            error_file.name,
            bucket,
        ]
    )

    ws_endpoint = f"{bucket}.website-{REGION}.linodeobjects.com"
    ws_url = f"https://{ws_endpoint}"
    response = requests.get(ws_url)
    assert response.status_code == 200
    assert "Hello, World!" in response.text

    response = requests.get(f"{ws_url}/invalid-page.html")
    assert response.status_code == 404
    assert "Error!" in response.text

    output = exec_test_command(BASE_CMD + ["ws-info", bucket])
    assert f"Bucket {bucket}: Website configuration" in output
    assert f"Website endpoint: {ws_endpoint}" in output
    assert f"Index document: {index_file.name}" in output
    assert f"Error document: {error_file.name}" in output

    exec_test_command(BASE_CMD + ["ws-delete", bucket])
    response = requests.get(ws_url)
    assert response.status_code == 404


def test_show_usage(
    keys: Keys,
    monkeypatch: MonkeyPatch,
    generate_test_file: GetTestFileType,
    create_bucket: Callable[[Optional[str]], str],
):
    patch_keys(keys, monkeypatch)

    KB = 1024
    MB = 1024 * KB

    large_file1 = generate_test_file(size=10 * MB).resolve()
    large_file2 = generate_test_file(size=20 * MB).resolve()

    bucket1 = create_bucket()
    bucket2 = create_bucket()

    exec_test_command(BASE_CMD + ["put", str(large_file1), bucket1])

    exec_test_command(
        BASE_CMD + ["put", str(large_file1), str(large_file2), bucket2]
    )

    output = exec_test_command(BASE_CMD + ["du"])
    assert "MB Total" in output

    output = exec_test_command(BASE_CMD + ["du", bucket1])
    assert "10.0 MB" in output
    assert "1 objects" in output

    output = exec_test_command(BASE_CMD + ["du", bucket2])
    assert "30.0 MB" in output
    assert "2 objects" in output


def test_generate_url(
    keys: Keys,
    monkeypatch: MonkeyPatch,
    generate_test_file: GetTestFileType,
    create_bucket: Callable[[Optional[str]], str],
):
    patch_keys(keys, monkeypatch)
    bucket = create_bucket()
    content = "Hello, World!"
    test_file = generate_test_file(content=content).resolve()

    exec_test_command(BASE_CMD + ["put", str(test_file), bucket])

    url = exec_test_command(
        BASE_CMD + ["signurl", bucket, test_file.name, "+300"]
    )
    response = requests.get(url.strip("\n"))
    assert response.text == content
    assert response.status_code == 200


def test_obj_action_triggers_key_cleanup_and_deletes_stale_key(
    keys: Keys,
    monkeypatch: MonkeyPatch,
    create_bucket: callable,
):
    patch_keys(keys, monkeypatch)
    bucket = create_bucket()

    now = int(time.time())
    stale_timestamp = (
        now - 31 * 24 * 60 * 60
    )  # 31 days ago (assuming 30d lifespan)
    fresh_timestamp = now

    stale_key = {
        "id": "stale-id",
        "label": f"linode-cli-testuser@localhost-{stale_timestamp}",
        "access_key": "STALEKEY",
    }
    fresh_key = {
        "id": "fresh-id",
        "label": f"linode-cli-testuser@localhost-{fresh_timestamp}",
        "access_key": "FRESHKEY",
    }

    def call_operation_side_effect(resource, action, *args, **kwargs):
        if resource == "object-storage" and action == "keys-list":
            return 200, {"data": [stale_key, fresh_key]}
        if resource == "object-storage" and action == "keys-delete":
            return 200, {}
        if resource == "object-storage" and action == "keys-create":
            return 200, {"access_key": "NEWKEY", "secret_key": "NEWSECRET"}
        if resource == "account" and action == "view":
            return 200, {}
        return 200, {}

    with patch("linodecli.plugins.obj.__init__.CLI") as MockCLI:
        mock_client = MockCLI.return_value
        mock_client.config.plugin_get_value.side_effect = (
            lambda k, d=None, t=None: {
                "perform-key-cleanup": True,
                "key-lifespan": "30d",
                "key-rotation-period-days": "10d",
                "key-cleanup-batch-size": 10,
            }[k]
        )
        mock_client.call_operation.side_effect = call_operation_side_effect
        mock_client.config.plugin_set_value.return_value = None
        mock_client.config.write_config.return_value = None

        # Execute the ls command
        exec_test_command(BASE_CMD + ["ls", bucket])

        # Check that keys-delete was called for the stale key only
        delete_calls = [
            c
            for c in mock_client.call_operation.mock_calls
            if c[1][1] == "keys-delete"
        ]
        assert any(
            c[1][2][0] == "stale-id" for c in delete_calls
        ), "Stale key was not deleted"
        assert not any(
            c[1][2][0] == "fresh-id" for c in delete_calls
        ), "Fresh key should not be deleted"


def test_obj_action_triggers_key_rotation(
    keys: Keys,
    monkeypatch: MonkeyPatch,
    create_bucket: callable,
):
    patch_keys(keys, monkeypatch)
    bucket = create_bucket()

    now = int(time.time())
    # Key created 31 days ago, rotation period is 30 days
    old_timestamp = now - 60 * 60 * 24 * 31

    key_due_for_rotation = {
        "id": "rotate-id",
        "label": f"linode-cli-testuser@localhost-{old_timestamp}",
        "access_key": "ROTATEKEY",
    }

    def call_operation_side_effect(resource, action, *args, **kwargs):
        if resource == "object-storage" and action == "keys-list":
            return 200, {"data": [key_due_for_rotation]}
        if resource == "object-storage" and action == "keys-create":
            return 200, {"access_key": "NEWKEY", "secret_key": "NEWSECRET"}
        if resource == "object-storage" and action == "keys-delete":
            return 200, {}
        if resource == "account" and action == "view":
            return 200, {}
        return 200, {}

    with patch("linodecli.plugins.obj.__init__.CLI") as MockCLI:
        mock_client = MockCLI.return_value
        mock_client.config.plugin_get_value.side_effect = (
            lambda k, d=None, t=None: {
                "key-cleanup-enabled": True,
                "key-lifespan": "90d",
                "key-rotation-period": "30d",
                "key-cleanup-batch-size": 10,
            }[k]
        )
        mock_client.call_operation.side_effect = call_operation_side_effect
        mock_client.config.plugin_set_value.return_value = None
        mock_client.config.write_config.return_value = None

        exec_test_command(BASE_CMD + ["ls", bucket])

        # Check that keys-create (rotation) was called
        create_calls = [
            c
            for c in mock_client.call_operation.mock_calls
            if c[1][1] == "keys-create"
        ]
        assert create_calls, "Key rotation (keys-create) was not triggered"

        # Check that keys-delete was called for the old key
        delete_calls = [
            c
            for c in mock_client.call_operation.mock_calls
            if c[1][1] == "keys-delete"
        ]
        assert any(
            c[1][2][0] == "rotate-id" for c in delete_calls
        ), "Old key was not deleted after rotation"


def test_obj_action_does_not_trigger_cleanup_if_recent(
    keys: Keys,
    monkeypatch: MonkeyPatch,
    create_bucket: callable,
):
    patch_keys(keys, monkeypatch)
    bucket = create_bucket()

    now = int(time.time())
    # Set last cleanup to 1 hour ago (less than 24h)
    last_cleanup = now - 60 * 60

    stale_timestamp = now - 31 * 24 * 60 * 60
    stale_key = {
        "id": "stale-id",
        "label": f"linode-cli-testuser@localhost-{stale_timestamp}",
        "access_key": "STALEKEY",
    }

    def call_operation_side_effect(resource, action, *args, **kwargs):
        if resource == "object-storage" and action == "keys-list":
            return 200, {"data": [stale_key]}
        if resource == "object-storage" and action == "keys-delete":
            return 200, {}
        if resource == "object-storage" and action == "keys-create":
            return 200, {"access_key": "NEWKEY", "secret_key": "NEWSECRET"}
        if resource == "account" and action == "view":
            return 200, {}
        return 200, {}

    with patch("linodecli.plugins.obj.__init__.CLI") as MockCLI:
        mock_client = MockCLI.return_value
        mock_client.config.plugin_get_value.side_effect = (
            lambda k, d=None, t=None: {
                "key-cleanup-enabled": True,
                "key-lifespan": "30d",
                "key-rotation-period": "10d",
                "key-cleanup-batch-size": 10,
                "last-key-cleanup-timestamp": str(last_cleanup),
            }[k]
        )
        mock_client.call_operation.side_effect = call_operation_side_effect
        mock_client.config.plugin_set_value.return_value = None
        mock_client.config.write_config.return_value = None

        exec_test_command(BASE_CMD + ["ls", bucket])

        # Check that keys-delete was NOT called
        delete_calls = [
            c
            for c in mock_client.call_operation.mock_calls
            if c[1][1] == "keys-delete"
        ]
        assert (
            not delete_calls
        ), "Cleanup should not be performed if it was done in the last 24 hours"


def test_obj_action_does_not_trigger_cleanup_if_disabled(
    keys: Keys,
    monkeypatch: MonkeyPatch,
    create_bucket: callable,
):
    patch_keys(keys, monkeypatch)
    bucket = create_bucket()

    now = int(time.time())
    stale_timestamp = now - 31 * 24 * 60 * 60
    stale_key = {
        "id": "stale-id",
        "label": f"linode-cli-testuser@localhost-{stale_timestamp}",
        "access_key": "STALEKEY",
    }

    def call_operation_side_effect(resource, action, *args, **kwargs):
        if resource == "object-storage" and action == "keys-list":
            return 200, {"data": [stale_key]}
        if resource == "object-storage" and action == "keys-delete":
            return 200, {}
        if resource == "object-storage" and action == "keys-create":
            return 200, {"access_key": "NEWKEY", "secret_key": "NEWSECRET"}
        if resource == "account" and action == "view":
            return 200, {}
        return 200, {}

    with patch("linodecli.plugins.obj.__init__.CLI") as MockCLI:
        mock_client = MockCLI.return_value
        mock_client.config.plugin_get_value.side_effect = (
            lambda k, d=None, t=None: {
                "key-cleanup-enabled": False,  # Cleanup disabled
                "key-lifespan": "30d",
                "key-rotation-period": "10d",
                "key-cleanup-batch-size": 10,
            }[k]
        )
        mock_client.config.plugin_set_value.return_value = None
        mock_client.config.write_config.return_value = None
        mock_client.call_operation.side_effect = call_operation_side_effect

        exec_test_command(BASE_CMD + ["ls", bucket])

        # Check that keys-delete was NOT called
        delete_calls = [
            c
            for c in mock_client.call_operation.mock_calls
            if c[1][1] == "keys-delete"
        ]
        assert (
            not delete_calls
        ), "Cleanup should not be performed when perform-key-cleanup is False"
