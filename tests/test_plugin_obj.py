from pytest import CaptureFixture

from linodecli.plugins.obj import get_obj_args_parser, print_help


def test_print_help(capsys: CaptureFixture):
    parser = get_obj_args_parser()
    print_help(parser)
    captured_text = capsys.readouterr()
    assert parser.format_help() in captured_text.out
    assert "See --help for individual commands for more information" in captured_text
