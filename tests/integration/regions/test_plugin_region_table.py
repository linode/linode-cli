import os
import subprocess
from typing import List

BASE_CMD = ["linode-cli", "region-table"]

# Set the console width to 150
env = os.environ.copy()
env["COLUMNS"] = "150"


def exec_test_command(args: List[str]):
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        env=env,
    )
    return process


def test_output():
    process = exec_test_command(BASE_CMD)
    output = process.stdout.decode()
    lines = output.split("\n")
    lines = lines[3 : len(lines) - 2]
    for line in lines:
        assert "-" in line
        assert "✔" in line
        assert "│" in line
