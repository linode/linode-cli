import random
import time
from string import ascii_lowercase
from typing import Callable

BASE_URL = "https://api.linode.com/v4/"

COMMAND_JSON_OUTPUT = ["--suppress-warnings", "--no-defaults", "--json"]


def get_random_text(length: int = 10):
    return "".join(random.choice(ascii_lowercase) for i in range(length))


def wait_for_condition(interval: int, timeout: int, condition: Callable):
    start_time = time.time()
    while True:
        if condition():
            break

        if time.time() - start_time > timeout:
            raise TimeoutError("SSH timeout expired")

        # Evil
        time.sleep(interval)
