import json
import random

from tests.integration.helpers import BASE_CMDS, exec_test_command


def test_obj_quotas_list():
    response = exec_test_command(
        BASE_CMDS["object-storage"] + ["get-object-storage-quotas", "--json"]
    )

    quotas = json.loads(response)

    quota = quotas[0]
    assert isinstance(quota, dict)

    required_fields = {
        "quota_id",
        "quota_name",
        "endpoint_type",
        "s3_endpoint",
        "description",
        "quota_limit",
        "resource_metric",
    }
    assert required_fields.issubset(quota.keys())


def test_obj_quota_view():
    quota_id = get_quota_id()

    response = exec_test_command(
        BASE_CMDS["object-storage"]
        + ["get-object-storage-quota", quota_id, "--json"]
    )

    data = json.loads(response)

    quota = data[0]
    assert isinstance(quota, dict)
    assert "quota_id" in quota
    assert "quota_name" in quota
    assert "endpoint_type" in quota
    assert "s3_endpoint" in quota
    assert "description" in quota
    assert "quota_limit" in quota
    assert "resource_metric" in quota

    assert isinstance(quota["quota_id"], str)
    assert isinstance(quota["quota_name"], str)
    assert isinstance(quota["endpoint_type"], str)
    assert isinstance(quota["s3_endpoint"], str)
    assert isinstance(quota["description"], str)
    assert isinstance(quota["quota_limit"], int)
    assert isinstance(quota["resource_metric"], str)


def test_obj_quota_usage_view():
    quota_id = get_quota_id()

    response = exec_test_command(
        BASE_CMDS["object-storage"]
        + ["get-object-storage-quota-usage", quota_id, "--json"]
    )

    data = json.loads(response)

    item = data[0]
    assert isinstance(item, dict)
    assert "quota_limit" in item
    assert "usage" in item
    assert isinstance(item["quota_limit"], int)
    assert isinstance(item["usage"], int)


def get_quota_id():
    response = exec_test_command(
        BASE_CMDS["object-storage"] + ["get-object-storage-quotas", "--json"]
    )

    quotas = json.loads(response)
    if not quotas:
        return None

    random_quota = random.choice(quotas)
    return random_quota["quota_id"]
