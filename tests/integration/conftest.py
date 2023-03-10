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
from helpers import get_random_text

from linodecli import ENV_TOKEN_NAME


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
def generate_test_files(name_generator: Callable[[str], str]):
    """
    Return a function that can generate files with random text.
    """
    test_files_dir = tempfile.TemporaryDirectory()

    def _generate_test_files(
        num: Optional[int] = 1, content: Optional[str] = None
    ):
        if content is None:
            content = f"Linode CLI integration test\n{get_random_text(100)}\n"
        file_paths = [
            Path(test_files_dir.name) / f"{name_generator('test-file')}.txt"
            for _ in range(num)
        ]
        file_paths = [f.resolve() for f in file_paths]
        for f in file_paths:
            with open(f, "w") as f:
                f.write(content)
        return file_paths

    yield _generate_test_files
    test_files_dir.cleanup()
