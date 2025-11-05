import pytest

from tests.integration.helpers import (
    BASE_CMDS,
    assert_headers_in_lines,
    assert_help_actions_list,
    delete_target_id,
    exec_test_command,
    get_random_text,
    retry_exec_test_command_with_delay,
)


def test_help_alerts():
    output = exec_test_command(
        BASE_CMDS["alerts"]
        + [
            "--help",
            "--text",
            "--delimiter=,",
        ]
    )

    actions = [
        "channels-list",
        "definition-create",
        "definition-delete",
        "definition-update",
        "definition-view",
        "definitions-list-all",
    ]
    assert_help_actions_list(actions, output)


def test_channels_list():
    res = exec_test_command(
        BASE_CMDS["alerts"] + ["channels-list", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = [
        "channel_type",
        "content.email.email_addresses",
        "id",
        "label",
        "type",
        "updated",
    ]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def get_channel_id():
    channel_ids = exec_test_command(
        BASE_CMDS["alerts"]
        + [
            "channels-list",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_id = channel_ids[0].split(",")[0]
    yield first_id


def test_alerts_definition_create(get_channel_id, get_service_type):
    label = get_random_text(8) + "_alert"
    exec_test_command(
        BASE_CMDS["alerts"]
        + [
            "definition-create",
            "--channel_ids",
            get_channel_id,
            "--label",
            label,
            "--rule_criteria.rules.metric",
            "cpu_usage",
            "--rule_criteria.rules.operator",
            "eq",
            "--rule_criteria.rules.threshold",
            "80",
            "--rule_criteria.rules.aggregate_function",
            "avg",
            "--severity",
            "1",
            "--trigger_conditions.criteria_condition",
            "ALL",
            "--trigger_conditions.evaluation_period_seconds",
            "300",
            "--trigger_conditions.polling_interval_seconds",
            "300",
            "--trigger_conditions.trigger_occurrences",
            "3",
            get_service_type,
        ]
    )


@pytest.mark.skip
def test_list_alert_definitions_for_service_type(get_service_type):
    service_type = get_service_type
    output = exec_test_command(
        BASE_CMDS["alerts"]
        + [
            "definition-view",
            service_type,
            "--text",
            "--delimiter=,",
        ]
    )

    headers = ["class", "created", "label", "severity", "service_type"]
    assert_headers_in_lines(headers, output.splitlines())


def test_alerts_list():
    res = exec_test_command(
        BASE_CMDS["alerts"]
        + ["definitions-list-all", "--text", "--delimiter=,"]
    )
    lines = res.splitlines()
    headers = ["class", "created", "label", "severity", "service_type"]
    assert_headers_in_lines(headers, lines)


@pytest.fixture
def get_alert_id():
    alert_id = exec_test_command(
        BASE_CMDS["alerts"]
        + [
            "definitions-list-all",
            "--text",
            "--no-headers",
            "--delimiter",
            ",",
            "--format",
            "id",
        ]
    ).splitlines()
    first_id = alert_id[-1]
    yield first_id


def test_alert_view(get_alert_id, get_service_type):
    alert_id = get_alert_id
    service_type = get_service_type
    res = exec_test_command(
        BASE_CMDS["alerts"]
        + [
            "definition-view",
            service_type,
            alert_id,
            "--text",
            "--delimiter=,",
        ]
    )
    lines = res.splitlines()

    headers = ["class", "created", "label", "severity", "service_type"]
    assert_headers_in_lines(headers, lines)


def test_alert_update(get_alert_id, get_service_type):
    alert_id = get_alert_id
    service_type = get_service_type
    new_label = get_random_text(8) + "_updated"
    updated_label = retry_exec_test_command_with_delay(
        BASE_CMDS["alerts"]
        + [
            "definition-update",
            service_type,
            alert_id,
            "--label",
            new_label,
            "--text",
            "--no-headers",
            "--format=label",
        ],
        delay=50,
    )
    assert updated_label == new_label
    delete_target_id(
        target="alerts",
        delete_command="definition-delete",
        service_type=service_type,
        id=alert_id,
        use_retry=True,
    )
