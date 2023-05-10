import argparse

from linodecli import operation


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
                f"--{arg_name}",
                metavar=arg_name,
                action=operation.ListArgumentAction,
                type=str,
            )

        result = parser.parse_args(
            [
                "--foo",
                "cool",
                "--bar",
                "wow",
                "--aaa",
                "computer",
                "--foo",
                "test",
                "--bar",
                "wow",
                "--aaa",
                "akamai",
            ]
        )
        assert result.foo == ["cool", "test"]
        assert result.bar == ["wow", "wow"]
        assert result.aaa == ["computer", "akamai"]

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
                f"--{arg_name}",
                metavar=arg_name,
                action=operation.ListArgumentAction,
                type=str,
            )

        result = parser.parse_args(
            [
                "--foo",
                "cool",
                "--aaa",
                "computer",
                "--foo",
                "test",
                "--bar",
                "wow",
                "--foo",
                "linode",
                "--aaa",
                "akamai",
            ]
        )
        assert result.foo == ["cool", "test", "linode"]
        assert result.bar == [None, "wow"]
        assert result.aaa == ["computer", None, "akamai"]
