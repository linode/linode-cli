from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
)


def test_maintenance_policies_list():
    res = exec_test_command(
        BASE_CMDS["maintenance"] + ["policies-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = [
        "description",
        "is_default",
        "label",
        "is_default",
        "slug",
        "type",
    ]
    assert_headers_in_lines(headers, lines)
    rows = [line.split(",") for line in lines[1:] if line.strip()]

    type_index = headers.index("type")
    types = [row[type_index].strip() for row in rows]

    assert set(types) == {"migrate", "power_off_on"}
