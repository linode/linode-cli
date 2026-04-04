import subprocess
import os
def test_help_alias():
    env = os.environ.copy()
    env["LINODE_CLI_CONFIG"] = "/dev/null"
    env["HOME"] = "/tmp"

    result = subprocess.run(
        ["python3", "-m", "linodecli", "instance", "help"],
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
        input="\n"
    )

    assert result.returncode == 0
    assert "usage" in result.stdout.lower()