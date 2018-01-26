#!/usr/local/bin/python3
import argparse
import sys

import linode
import pkg_resources
from colorclass import Color
from terminaltables import SingleTable

from linodecli import config, resources

package_version = pkg_resources.require("linode-cli")[0].version,

def preparse():
    avail_resources = [ r for r in dir(resources) if not '__' in r ]

    args = sys.argv
    held_help = False
    if '-h' in args:
        if len(args) > 1 and args[1] in avail_resources:
            held_help = True
            args.remove('-h')

    if len(args) > 1:
        if args[1] not in avail_resources:
            args.insert(1, 'linode')
            return args, held_help

    return args, held_help

def warn():
    """
    Deprecation warning for old way to invoke script
    """
    msg = [ [ Color('{yellow}WARNING{/yellow}') ], [ "The 'linode-beta' command has been deprecated and renamed to "
            "'linode-cli'.  Please invoke with that command to hide this warning." ] ]

    print(SingleTable(msg).table)
    main()

def main():
    if not sys.stdout.isatty():
        sys.argv.append('--raw')

    sys.argv, add_help = preparse()

    parser = argparse.ArgumentParser(description="Command Line Interface for Linode API v4")
    parser.add_argument('object', metavar='TYPE', type=str,
            help="the type of object to act on (linode if omitted)", default='linode')
    parser.add_argument('command', metavar='CMD', type=str,
            help="the command to run on the given objects")
    parser.add_argument('-t','--token', metavar='TOKEN', type=str,
            help="the Personal Access Token to use when talking to Linode.")
    parser.add_argument('-u','--username', metavar='USERNAME', type=str,
            help="the User to act as.  Uses default user if omitted")
    parser.add_argument('--raw', action='store_true',
            help="return output in a machine-readable format, assumed when "
                 "stdout is not a tty device")
    parser.add_argument('--separator', metavar='SEPARATOR', type=str, default=':',
            help="the field separator when using raw output")

    args, unparsed = parser.parse_known_args()
    sys.argv = sys.argv[:1] # clean up sys.argv so future parsers works as expected
    if add_help:
        unparsed.insert(0, '-h')

    if args.command == 'configure':
        config.configure(username=args.username)
        sys.exit(0)

    args = config.update(args, username=args.username)

    if not args.token:
        print("No Personal Access Token provided!  Please run configure or "
                "provide a token with the --token argument.")
        sys.exit(1)

    client = linode.LinodeClient(args.token, user_agent='linode-cli/{}'.format(package_version))

    if hasattr(resources, args.object):
        obj = getattr(resources, args.object)
        cmd = args.command.replace('-','_')
        if hasattr(obj, cmd):
            try:
                getattr(obj, cmd)(args, client, unparsed=unparsed)
            except linode.ApiError as e:
                print("Error: {}".format(e))
        else:
            print("Command not found - options are: {}".format(', '.join([ c.replace('_', '-') for c in dir(obj) if not c.startswith('__') ])))
    else:
        print("Resource not found - options are: {}".format(', '.join([ r for r in dir(resources) if not '__' in r ])))
