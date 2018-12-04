"""
The alpha plugin includes Linode CLI features which are in an early,
pre-release, state.
"""
import argparse
from sys import exit

from terminaltables import SingleTable

def call(args, context):
    parser = argparse.ArgumentParser("cluster", add_help=False)
    parser.add_argument('command', metavar='COMMAND', nargs='?', type=str,
                        help="The clusters command to be invoked.")
    parsed, args = parser.parse_known_args(args)

    commands = { 'create': create, 'delete': delete }
    
    if parsed.command is None or (parsed.command is None and parsed.help):
        parser.print_help()
        print_available_commands(commands)
        exit(0)

    if parsed.command in commands.keys():
        commands[parsed.command](args, context)
    else:
        print('Unrecognized command {}'.format(parsed.command))

def create(args, context):
    print('creating cluster')

def delete(args, context):
    print('deleting cluster')

def print_available_commands(commands):
    print("\nAvailable commands:")
    content = [c for c in commands.keys()]
    proc = []
    for i in range(0,len(content),3):
        proc.append(content[i:i+3])
    if content[i+3:]:
        proc.append(content[i+3:])

    table = SingleTable(proc)
    table.inner_heading_row_border = False
    print(table.table)
