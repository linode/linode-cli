from tests.integration.helpers import exec_test_command

BASE_CMD = ["linode-cli", "betas"]


def test_beta_list():
    res = (
        exec_test_command(BASE_CMD + ["list", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    beta_id = lines[1].split(",")[0]

    headers = ["label", "description"]
    for header in headers:
        assert header in lines[0]
    return beta_id


def test_beta_view():
    beta_id = test_beta_list()
    res = (
        exec_test_command(
            BASE_CMD + ["view", beta_id, "--text", "--delimiter=,"]
        )
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["label", "description"]
    for header in headers:
        assert header in lines[0]


def test_beta_enrolled():
    res = (
        exec_test_command(BASE_CMD + ["enrolled", "--text", "--delimiter=,"])
        .stdout.decode()
        .rstrip()
    )
    lines = res.splitlines()

    headers = ["label", "enrolled"]
    for header in headers:
        assert header in lines[0]
