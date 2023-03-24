# Use random integer as the start point here to avoid
# id conflicts when multiple testings are running.
import logging
import os
import subprocess
import tempfile
from collections import defaultdict
from itertools import count
from pathlib import Path
from random import randint
from typing import Callable, Optional

import pytest

from linodecli import ENV_TOKEN_NAME
from tests.integration.helpers import get_random_text


@pytest.fixture(scope="session")
def _id_generators():
    return defaultdict(lambda: count(randint(0, 1000000)))


@pytest.fixture(scope="session")
def name_generator(_id_generators: dict):
    generator = lambda prefix: f"{prefix}-{next(_id_generators[prefix])}"
    return generator


@pytest.fixture(scope="session")
def ssh_key_pair_generator():
    key_dir = tempfile.TemporaryDirectory()

    # Generate the key pair
    process = subprocess.run(
        [
            "ssh-keygen",
            "-f",
            f"{key_dir.name}/key",
            "-b",
            "4096",
            "-q",
            "-t",
            "rsa",
            "-N",
            "",
        ],
        stdout=subprocess.PIPE,
    )
    assert process.returncode == 0

    yield f"{key_dir.name}/key.pub", f"{key_dir.name}/key"

    key_dir.cleanup()


@pytest.fixture(scope="session")
def token():
    token = os.getenv(ENV_TOKEN_NAME)
    if not token:
        logging.error(
            f"Token is required in the environment as {ENV_TOKEN_NAME}"
        )
    return token


@pytest.fixture
def generate_test_file(name_generator: Callable[[str], str]):
    test_files_dir = tempfile.TemporaryDirectory()

    def _generate_test_file(
        content: Optional[str] = None,
        filename: Optional[str] = None,
        size: Optional[int] = 100,
    ):
        if content is None:
            content = f"{get_random_text(size)}"
        if filename is None:
            filename = f"{name_generator('test-file')}.txt"
        file_path = Path(test_files_dir.name) / filename
        file_path = file_path.resolve()
        with open(file_path, "w") as f:
            f.write(content)
        return file_path

    yield _generate_test_file
    test_files_dir.cleanup()


@pytest.fixture
def generate_test_files(
    generate_test_file: Callable[[Optional[str], Optional[str]], Path]
):
    """
    Return a function that can generate files with random text.
    """

    def _generate_test_files(
        num: Optional[int] = 1, content: Optional[str] = None
    ):
        file_paths = [generate_test_file(content=content) for _ in range(num)]
        return file_paths

    return _generate_test_files
