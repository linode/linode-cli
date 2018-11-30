import argparse

def call(args, context):
    """
    This method is invoked when this plugin is invoked on the command line.

    :param args: sys.argv, trimmed to represent only arguments to this command
    :type args: list
    """
    parser = argparse.ArgumentParser("echo", add_help=True)
    parser.add_argument('word', nargs='*', help="The stuff to echo")
    data = parser.parse_args(args)

    print(' '.join(data.word))
