from concurrent.futures import ThreadPoolExecutor, wait
from typing import Callable, Optional

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
