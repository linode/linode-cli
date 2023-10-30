import subprocess
from typing import List

BASE_CMD = ["linode-cli", "region-table"]


def exec_test_command(args: List[str]):
    process = subprocess.run(
        args,
        stdout=subprocess.PIPE,
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
