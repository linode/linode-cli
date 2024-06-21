import argparse
import contextlib
import io
import json

from linodecli.baked import operation
from linodecli.baked.operation import ExplicitEmptyListValue, ExplicitNullValue


class TestOperation:
    def test_list_arg_action_basic(self):
        """
        Tests a basic list argument condition.
        """

        parser = argparse.ArgumentParser(
            prog=f"foo",
        )

        for arg_name in ["foo", "bar", "aaa"]:
            parser.add_argument(
                f"--foo.{arg_name}",
                metavar=arg_name,
                action=operation.ListArgumentAction,
                type=str,
            )

        result = parser.parse_args(
            [
                "--foo.foo",
                "cool",
                "--foo.bar",
                "wow",
                "--foo.aaa",
                "computer",
                "--foo.foo",
                "test",
                "--foo.bar",
                "wow",
                "--foo.aaa",
                "akamai",
            ]
        )
        assert getattr(result, "foo.foo") == ["cool", "test"]
        assert getattr(result, "foo.bar") == ["wow", "wow"]
        assert getattr(result, "foo.aaa") == ["computer", "akamai"]

    def test_list_arg_action_missing_attr(self):
        """
        Tests that a missing attribute for the first element will be
        implicitly populated.
        """

        parser = argparse.ArgumentParser(
            prog=f"foo",
        )

        for arg_name in ["foo", "bar", "aaa"]:
            parser.add_argument(
                f"--foo.{arg_name}",
                metavar=arg_name,
                action=operation.ListArgumentAction,
                type=str,
            )

        result = parser.parse_args(
            [
                "--foo.foo",
                "cool",
                "--foo.aaa",
                "computer",
                "--foo.foo",
                "test",
                "--foo.bar",
                "wow",
                "--foo.foo",
                "linode",
                "--foo.aaa",
                "akamai",
            ]
        )
        assert getattr(result, "foo.foo") == ["cool", "test", "linode"]
        assert getattr(result, "foo.bar") == [None, "wow"]
        assert getattr(result, "foo.aaa") == ["computer", None, "akamai"]

    def test_password_prompt_basic(self):
        """
        Tests a basic password prompt base condition.
        """

        parser = argparse.ArgumentParser(
            prog=f"",
        )

        parser.add_argument(
            f"--TOKEN",
            metavar="TOKEN",
            action=operation.PasswordPromptAction,
            type=str,
        )

        result = parser.parse_args(
            [
                "--TOKEN",
                "test_token",
            ]
        )

        assert getattr(result, "TOKEN") == "test_token"

    def test_optional_from_file_action(self):
        """
        Tests a optional from file action base condition.
        """

        parser = argparse.ArgumentParser(
            prog=f"",
        )

        parser.add_argument(
            f"--path",
            action=operation.OptionalFromFileAction,
            type=str,
        )

        result = parser.parse_args(
            [
                "--path",
                "/path/get",
            ]
        )

        assert getattr(result, "path") == "/path/get"

    def test_parse_args_nullable_string(self, create_operation):
        result = create_operation.parse_args(
            ["--nullable_string", "null", "--region", "null"]
        )
        assert result.region == "null"
        assert isinstance(result.nullable_string, ExplicitNullValue)

        result = create_operation.parse_args(["--nullable_string", "foobar"])
        assert result.nullable_string == "foobar"

    def test_parse_args_nullable_integer(self, create_operation):
        result = create_operation.parse_args(
            ["--nullable_int", "null", "--region", "null"]
        )
        assert result.region == "null"
        assert isinstance(result.nullable_int, ExplicitNullValue)

        result = create_operation.parse_args(["--nullable_int", "456"])
        assert result.nullable_int == 456

    def test_parse_args_nullable_float(self, create_operation):
        result = create_operation.parse_args(
            ["--nullable_float", "null", "--region", "null"]
        )
        assert result.region == "null"
        assert isinstance(result.nullable_float, ExplicitNullValue)

        result = create_operation.parse_args(["--nullable_float", "456.123"])
        assert result.nullable_float == 456.123

    def test_parse_args_object_list(self, create_operation):
        result = create_operation.parse_args(
            [
                # First object
                "--object_list.field_string",
                "test1",
                "--object_list.field_int",
                "123",
                "--object_list.field_dict.nested_string",
                "test2",
                "--object_list.field_dict.nested_int",
                "789",
                "--object_list.field_array",
                json.dumps(["foo", "bar"]),
                # Second object
                "--object_list.field_int",
                "456",
                "--object_list.field_dict.nested_string",
                "test3",
            ]
        )

        assert result.object_list == [
            {
                "field_string": "test1",
                "field_int": 123,
                "field_dict": {"nested_string": "test2", "nested_int": 789},
                "field_array": ["foo", "bar"],
                "nullable_string": None,  # We expect this to be filtered out later
            },
            {"field_int": 456, "field_dict": {"nested_string": "test3"}},
        ]

    def test_parse_args_object_list_json(self, create_operation):
        expected = [
            {
                "field_string": "test1",
                "field_int": 123,
                "field_dict": {"nested_string": "test2", "nested_int": 789},
                "field_array": ["foo", "bar"],
            },
            {"field_int": 456, "field_dict": {"nested_string": "test3"}},
        ]

        result = create_operation.parse_args(
            ["--object_list", json.dumps(expected)]
        )

        assert result.object_list == expected

    def test_parse_args_conflicting_parent_child(self, create_operation):
        stderr_buf = io.StringIO()

        try:
            with contextlib.redirect_stderr(stderr_buf):
                create_operation.parse_args(
                    [
                        "--object_list",
                        "[]",
                        "--object_list.field_string",
                        "test",
                        "--object_list.field_int",
                        "123",
                        "--object_list.field_dict.nested_string",
                        "cool",
                    ]
                )
        except SystemExit as sys_exit:
            assert sys_exit.code == 7
        else:
            raise RuntimeError("Expected system exit, got none")

        stderr_result = stderr_buf.getvalue()
        assert (
            "Argument(s) --object_list.field_dict.nested_string, --object_list.field_string, "
            "--object_list.field_int cannot be specified when --object_list is specified."
            in stderr_result
        )

    def test_array_arg_action_basic(self):
        """
        Tests a basic array argument condition..
        """

        parser = argparse.ArgumentParser(
            prog=f"foo",
        )

        parser.add_argument(
            "--foo",
            metavar="foo",
            action=operation.ArrayAction,
            type=str,
        )

        # User specifies a normal list
        result = parser.parse_args(["--foo", "foo", "--foo", "bar"])
        assert getattr(result, "foo") == ["foo", "bar"]

        # User wants an explicitly empty list
        result = parser.parse_args(["--foo", "[]"])
        assert isinstance(getattr(result, "foo"), ExplicitEmptyListValue)

        # User doesn't specify the list
        result = parser.parse_args([])
        assert getattr(result, "foo") is None

        # User specifies a normal value and an empty list value
        result = parser.parse_args(["--foo", "foo", "--foo", "[]"])
        assert getattr(result, "foo") == ["foo", "[]"]
