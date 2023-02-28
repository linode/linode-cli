# Use random integer as the start point here to avoid
# id conflicts when multiple testings are running.
import os
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
def token():
    return os.getenv(ENV_TOKEN_NAME)
