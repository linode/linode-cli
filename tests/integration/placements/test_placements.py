from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    exec_test_command,
    get_random_text,
)
from tests.integration.placements.fixtures import (  # noqa: F401
    linode_for_placement_tests,
    placement_group,
)


def test_placement_group_list():
    res = exec_test_command(
        BASE_CMDS["placement"] + ["groups-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["placement_group_type", "region", "label"]
    assert_headers_in_lines(headers, lines)


def test_placement_group_view(placement_group):
    placement_group_id = placement_group
    res = exec_test_command(
        BASE_CMDS["placement"]
        + ["group-view", placement_group_id, "--text", "--delimiter=,"]
    )
    lines = res.splitlines()

    headers = ["placement_group_type", "region", "label"]
    assert_headers_in_lines(headers, lines)


def test_assign_placement_group(linode_for_placement_tests, placement_group):
    linode_id = linode_for_placement_tests
    placement_group_id = placement_group
    res = exec_test_command(
        BASE_CMDS["placement"]
        + [
            "assign-linode",
            placement_group_id,
            "--linodes",
            linode_id,
            "--text",
            "--delimiter=,",
            "--no-headers",
        ]
    )

    assert placement_group_id in res


def test_unassign_placement_group(linode_for_placement_tests, placement_group):
    linode_id = linode_for_placement_tests
    placement_group_id = placement_group
    exec_test_command(
        BASE_CMDS["placement"]
        + [
            "unassign-linode",
            placement_group_id,
            "--linode",
            linode_id,
            "--text",
            "--delimiter=,",
        ]
    )

    res = exec_test_command(
        BASE_CMDS["placement"]
        + [
            "group-view",
            placement_group_id,
            "--text",
            "--delimiter=,",
        ]
    )

    assert placement_group_id in res
    assert linode_id not in res


def test_update_placement_group(placement_group):
    placement_group_id = placement_group
    new_label = get_random_text(5) + "label"
    updated_label = exec_test_command(
        BASE_CMDS["placement"]
        + [
            "group-update",
            placement_group_id,
            "--label",
            new_label,
            "--text",
            "--no-headers",
            "--format=label",
        ]
    )
    assert new_label == updated_label
