import argparse

from linodecli.baked import operation


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
