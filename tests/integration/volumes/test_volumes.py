import json as _json
import os
import re

import pytest

from linodecli.exit_codes import ExitCodes
from tests.integration.helpers import (
    BASE_CMDS,
    delete_target_id,
    exec_failing_test_command,
    exec_test_command,
    get_random_text,
    wait_for_condition,
)
from tests.integration.volumes.fixtures import volume_instance_id  # noqa: F401


def test_fail_to_create_volume_under_10gb():
    label = get_random_text(8)

    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + [
            "create",
            "--label",
            label,
            "--region",
            "us-ord",
            "--size",
            "5",
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )

    if "test" == os.environ.get(
        "TEST_ENVIRONMENT", None
    ) or "dev" == os.environ.get("TEST_ENVIRONMENT", None):
        assert "size	Must be 10-1024" in result
    else:
        assert "size	Must be 10-16384" in result


def test_fail_to_create_volume_without_region():
    label = get_random_text(8)

    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + [
            "create",
            "--label",
            label,
            "--size",
            "10",
            "--text",
            "--no-headers",
            "--no-defaults",
        ],
        ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 400" in result
    assert "Must provide a region or a Linode ID" in result


def test_fail_to_create_volume_without_label():
    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + [
            "create",
            "--region",
            "us-ord",
            "--size",
            "10",
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 400" in result
    assert "label	label is required" in result


def test_fail_to_create_volume_over_1024gb_in_size():
    label = get_random_text(8)

    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + [
            "create",
            "--label",
            label,
            "--region",
            "us-ord",
            "--size",
            "19000",
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )
    if "test" == os.environ.get(
        "TEST_ENVIRONMENT", None
    ) or "dev" == os.environ.get("TEST_ENVIRONMENT", None):
        assert "size	Must be 10-1024" in result
    else:
        assert "size	Must be 10-16384" in result


def test_fail_to_create_volume_with_all_numberic_label():
    result = exec_failing_test_command(
        BASE_CMDS["volumes"]
        + [
            "create",
            "--label",
            "11111",
            "--region",
            "us-ord",
            "--size",
            "10",
            "--text",
            "--no-headers",
        ],
        ExitCodes.REQUEST_FAILED,
    )
    assert "Request failed: 400" in result
    assert "label	Must begin with a letter" in result


def test_list_volume(volume_instance_id):
    result = exec_test_command(
        BASE_CMDS["volumes"]
        + [
            "list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id,label,status,region,size,linode_id,linode_label",
        ]
    )
    assert re.search(
        "[0-9]+,[A-Za-z0-9-]+,(creating|active|offline),[A-Za-z0-9-]+,[0-9]+,,",
        result,
    )


@pytest.mark.smoke
def test_view_single_volume(volume_instance_id):
    volume_id = volume_instance_id
    result = exec_test_command(
        BASE_CMDS["volumes"]
        + [
            "view",
            volume_id,
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id,label,size,region",
        ]
    )

    assert re.search(volume_id + ",[A-Za-z0-9-]+,[0-9]+,[a-z-]+", result)


def test_update_volume_label(volume_instance_id):
    volume_id = volume_instance_id
    new_unique_label = "label-" + get_random_text(5)
    result = exec_test_command(
        BASE_CMDS["volumes"]
        + [
            "update",
            volume_id,
            "--label",
            new_unique_label,
            "--format",
            "label",
            "--text",
            "--no-headers",
        ]
    )

    assert new_unique_label in result


def test_add_new_tag_to_volume(volume_instance_id):
    unique_tag = get_random_text(5) + "-tag"
    volume_id = volume_instance_id
    result = exec_test_command(
        BASE_CMDS["volumes"]
        + [
            "update",
            volume_id,
            "--tag",
            unique_tag,
            "--format",
            "tags",
            "--text",
            "--no-headers",
        ]
    )

    assert unique_tag in result


def test_view_tags_attached_to_volume(volume_instance_id):
    volume_id = volume_instance_id
    exec_test_command(
        BASE_CMDS["volumes"]
        + ["view", volume_id, "--format", "tags", "--text", "--no-headers"]
    )


def test_fail_to_update_volume_size(volume_instance_id):
    volume_id = volume_instance_id
    os.system(
        "linode-cli volumes update --size=15 "
        + volume_id
        + " 2>&1 | tee /tmp/output_file.txt"
    )

    result = os.popen("cat /tmp/output_file.txt").read()

    assert (
        "linode-cli volumes update: error: unrecognized arguments: --size=15"
        in result
    )


def test_attach_volumes_to_extended_device_slots(linode_cloud_firewall):
    num_volumes = 12
    device_slots = [
        "sda", "sdb", "sdc", "sdd", "sde", "sdf", "sdg", "sdh",
        "sdi", "sdj", "sdk", "sdl",
    ]
    regions_data = _json.loads(
        exec_test_command(
            ["linode-cli", "regions", "ls", "--json", "--suppress-warnings"]
        )
    )
    eligible = [
        r["id"]
        for r in regions_data
        if r.get("site_type") == "core"
        and "Linodes" in r.get("capabilities", [])
        and "Block Storage" in r.get("capabilities", [])
    ]
    assert eligible, "No eligible region found with Linodes and Block Storage"
    test_region = eligible[0]
    linode_id = exec_test_command(
        [
            "linode-cli",
            "linodes",
            "create",
            "--type",
            "g6-standard-6",
            "--region",
            test_region,
            "--firewall_id",
            linode_cloud_firewall,
            "--booted",
            "true",
            "--format",
            "id",
            "--text",
            "--no-headers",
        ]
    )

    vol_ids = []
    label_base = "vol-ext-" + get_random_text(4)

    try:
        for i in range(num_volumes):
            vol_id = exec_test_command(
                BASE_CMDS["volumes"]
                + [
                    "create",
                    "--label",
                    f"{label_base}-{i}",
                    "--region",
                    test_region,
                    "--size",
                    "10",
                    "--text",
                    "--no-headers",
                    "--format",
                    "id",
                ]
            )
            vol_ids.append(vol_id)

            def volume_active(vid=vol_id):
                status = exec_test_command(
                    BASE_CMDS["volumes"]
                    + ["view", vid, "--text", "--no-headers", "--format", "status"]
                )
                return status.strip() == "active"

            wait_for_condition(10, 240, volume_active)

        configs_result = exec_test_command(
            BASE_CMDS["linodes"]
            + ["configs-list", linode_id, "--json", "--suppress-warnings"]
        )
        configs = _json.loads(configs_result)
        assert isinstance(configs, list), "configs-list should return a list"

        config_create_result = exec_test_command(
            BASE_CMDS["linodes"]
            + [
                "config-create",
                linode_id,
                "--label",
                label_base + "-config",
                "--devices.sda.volume_id",
                vol_ids[0],
                "--json",
                "--suppress-warnings",
            ]
        )
        config_json = _json.loads(config_create_result)[0]
        config_id = str(config_json["id"])

        view_result = exec_test_command(
            BASE_CMDS["linodes"]
            + ["config-view", linode_id, config_id, "--json", "--suppress-warnings"]
        )
        viewed = _json.loads(view_result)[0]
        assert str(viewed["id"]) == config_id, (
            "config-view should return the correct config"
        )
        assert "devices" in viewed, (
            "config-view response should include a 'devices' field"
        )

        for slot, vol_id in zip(device_slots[1:], vol_ids[1:]):
            exec_test_command(
                BASE_CMDS["linodes"]
                + [
                    "config-update",
                    linode_id,
                    config_id,
                    f"--devices.{slot}.volume_id",
                    vol_id,
                    "--text",
                    "--no-headers",
                ]
            )

        final_config_result = exec_test_command(
            BASE_CMDS["linodes"]
            + ["config-view", linode_id, config_id, "--json", "--suppress-warnings"]
        )
        final_config = _json.loads(final_config_result)[0]
        devices = final_config.get("devices", {})

        for slot in device_slots:
            assert devices.get(slot) is not None, (
                f"Extended device slot '{slot}' is unexpectedly empty; "
                "the plan-based volume limit may not be applied correctly."
            )

        populated = [slot for slot in device_slots if devices.get(slot) is not None]
        assert len(populated) == num_volumes, (
            f"Expected {num_volumes} populated device slots, "
            f"got {len(populated)}: {populated}"
        )

    finally:
        for vol_id in vol_ids:
            delete_target_id(
                target="volumes",
                id=vol_id,
                use_retry=True,
                retries=5,
                delay=15,
            )
        delete_target_id(
            target="linodes",
            id=linode_id,
            use_retry=True,
            retries=5,
            delay=15,
        )

