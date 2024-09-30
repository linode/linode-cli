import os
import subprocess
from typing import List

import pytest

env = os.environ.copy()
env["COLUMNS"] = "200"


def exec_test_command(args: List[str]):
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        env=env,
    )
    return process


# verifying the DC pricing changes along with types
@pytest.mark.smoke
def test_linode_type():
    process = exec_test_command(["linode-cli", "linodes", "types"])
    output = process.stdout.decode()
    assert " price.hourly " in output
    assert " price.monthly " in output
    assert " region_prices " in output
    assert " hourly " in output
    assert " monthly " in output
