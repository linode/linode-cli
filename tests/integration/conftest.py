# Use random integer as the start point here to avoid
# id conflicts when multiple testings are running.
import logging
import os
import subprocess
import tempfile
from collections import defaultdict
from itertools import count
from random import randint

import pytest

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
