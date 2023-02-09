import contextlib
import copy
import io

import pytest
from terminaltables import SingleTable

from linodecli import api_request, ModelAttr, ResponseModel, OutputMode


class TestCLI:
    """
    Unit tests for linodecli.cli
    """

    def test_find_operation(self, mock_cli, list_operation):
        target_operation = list_operation
        target_operation.command = "foo"
        target_operation.action = "list"
        target_operation.action_aliases = ["ls"]

        other_operation = copy.deepcopy(list_operation)
        other_operation.command = "cool"
        other_operation.action = "list"
        other_operation.action_aliases = ["ls"]

        mock_cli.ops = {
            "foo": {
                "list": target_operation
            },
            "cool": {
                "list": other_operation
            },
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
