import os
import re
import subprocess
from typing import List

BASE_CMD = ["linode-cli", "region-table"]

# Set the console width to 100
env = os.environ.copy()
env["COLUMNS"] = "100"


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
        check_marks = re.findall("✔", line)
        hyphens = re.findall("-", line)
        pipes = re.findall(r"\|", line)

        assert all(mark in line for mark in check_marks)
        assert all(hyphen in line for hyphen in hyphens)
        assert all(pipe in line for pipe in pipes)
