import os
import subprocess
from typing import List

env = os.environ.copy()
env["COLUMNS"] = "200"


def exec_test_command(args: List[str]):
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        env=env,
    )
    return process


def test_account_transfer():
    process = exec_test_command(["linode-cli", "account", "transfer"])
    output = process.stdout.decode()
    assert "billable" in output
    assert "quota" in output
    assert "used" in output
