from pytest import CaptureFixture

from linodecli import CLI
from linodecli.plugins.obj import get_obj_args_parser, helpers, print_help


def test_print_help(mock_cli: CLI, capsys: CaptureFixture):
    parser = get_obj_args_parser(["us-mia-1"])
    print_help(parser)
    captured_text = capsys.readouterr()
    assert parser.format_help() in captured_text.out
    assert (
        "See --help for individual commands for more information"
        in captured_text.out
    )


def test_helpers_denominate():
    assert helpers._denominate(0) == "0.0 KB"
    assert helpers._denominate(1) == "0.0 KB"
    assert helpers._denominate(12) == "0.01 KB"
    assert helpers._denominate(123) == "0.12 KB"
    assert helpers._denominate(1000) == "0.98 KB"

    assert helpers._denominate(1024) == "1.0 KB"
    assert helpers._denominate(1024**2) == "1.0 MB"
    assert helpers._denominate(1024**3) == "1.0 GB"
    assert helpers._denominate(1024**4) == "1.0 TB"
    assert helpers._denominate(1024**5) == "1024.0 TB"

    assert helpers._denominate(102400) == "100.0 KB"
    assert helpers._denominate(1024000) == "1000.0 KB"
    assert helpers._denominate((1024**2) // 10) == "102.4 KB"

    assert helpers._denominate(123456789) == "117.74 MB"
    assert helpers._denominate(1e23) == "90949470177.29 TB"
