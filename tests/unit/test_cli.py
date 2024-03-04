from __future__ import annotations

import copy
import math
import re

import pytest
import requests
from pytest import MonkeyPatch

if True:
    from linodecli import CLI
    from linodecli.api_request import get_all_pages
    from linodecli.baked.operation import OpenAPIOperation


class MockResponse:
    def __init__(
        self,
        page: int,
        pages: int,
        results: int,
        status_code: int = 200,
        headers: dict = None,
    ):
        self.page = page
        self.pages = pages
        self.headers = headers
        self.results = results
        self.status_code = status_code

    def json(self):
        return {
            "data": ["test_data" for _ in range(500)],
            "page": self.page,
            "pages": self.pages,
            "results": self.results,
        }


class TestCLI:
    """
    Unit tests for linodecli.cli
    """

    def test_find_operation(
        self, mock_cli: CLI, list_operation: OpenAPIOperation
    ):
        target_operation = list_operation
        target_operation.command = "foo"
        target_operation.action = "list"
        target_operation.action_aliases = ["ls"]

        other_operation = copy.deepcopy(list_operation)
        other_operation.command = "cool"
        other_operation.action = "list"
        other_operation.action_aliases = ["ls"]

        mock_cli.ops = {
            "foo": {"list": target_operation},
            "cool": {"list": other_operation},
        }

        assert mock_cli.find_operation("foo", "list") == target_operation
        assert mock_cli.find_operation("foo", "ls") == target_operation
        assert mock_cli.find_operation("cool", "list") == other_operation
        assert mock_cli.find_operation("cool", "ls") == other_operation

        with pytest.raises(ValueError, match=r"Command not found: *"):
            mock_cli.find_operation("bad", "list")

        with pytest.raises(ValueError, match=r"No action *"):
            mock_cli.find_operation("foo", "cool")
            mock_cli.find_operation("cool", "cool")

    def test_user_agent(self, mock_cli: CLI):
        assert re.compile(
            r"linode-cli/[0-9]+\.[0-9]+\.[0-9]+ linode-api-docs/[0-9]+\.[0-9]+\.[0-9]+ python/[0-9]+\.[0-9]+\.[0-9]+"
        ).match(mock_cli.user_agent)


def test_get_all_pages(
    mock_cli: CLI, list_operation: OpenAPIOperation, monkeypatch: MonkeyPatch
):
    TOTAL_DATA = 2000

    def mock_get(url: str, *args, **kwargs):
        # assume page_size is always 500
        page = int(re.search(r"\?page=(.*?)&page_size", url).group(1))
        pages = math.ceil(TOTAL_DATA / 500)
        if page > pages:
            page = pages
        return MockResponse(page, pages, pages * 500)

    monkeypatch.setattr(requests, "get", mock_get)

    merged_result = get_all_pages(mock_cli, list_operation, [])

    assert len(merged_result["data"]) == TOTAL_DATA
    assert merged_result["page"] == 1
    assert merged_result["pages"] == 1
    assert merged_result["results"] == TOTAL_DATA
