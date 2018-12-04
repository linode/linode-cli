"""
The alpha plugin includes Linode CLI features which are in an early,
pre-release, state.
"""
import argparse
from sys import exit
import os
from subprocess import call as spcall
import hashlib

from terminaltables import SingleTable

plugin_name = os.path.basename(__file__)[:-3]

def call(args, context):
    parser = argparse.ArgumentParser("{}".format(plugin_name), add_help=False)
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
    parser = argparse.ArgumentParser("{} create".format(plugin_name), add_help=True)
    parser.add_argument('name', metavar='NAME', type=str,
                        help="A name for the cluster.")
#    parser.add_argument('--ha', metavar="MASTERS", type=int, required=False,
#                        choices=[3, 5],
#                        help="Make the cluster highly-available with MASTERS "
#                             "number of masters (3 or 5)")
    parsed = parser.parse_args(args)

    # Check if Terraform is installed
    try:
        nullf = open(os.devnull, 'w')
        spcall(['terraformo'], stdout=nullf)
    except:
        print('To create a cluster you must first install Terraform\n'
              'https://learn.hashicorp.com/terraform/getting-started/install.html'
              '\n\nThis command will automatically download and install the Linode provider '
              'for Terraform.')
        exit(1)

    hashname = get_hashname(parsed.name)
#   MAJOR @TODO: check here if this hashname already appears as a prefix on any
#   volumes, linodes, or nodebalancers. If it does, bail with an error message,
#   because we don't want to later delete resources from both clusters!

    print(hashname)

def delete(args, context):
    print('deleting cluster')

#def update(args, context):
#    pass
#    # If a user attempts an update but does not have the corresponding
#    # terraform file, point them to a community post on how to retrieve it.

def get_hashname(name):
    """
    A cluster hashname is the first 9 characters of a SHA256 digest encoded in base36.

    This is used as a compact way to uniquely identify a cluster's Linode resources.
    It's also stateless! If a user loses their terraform file and wishes to
    delete a cluster they can still do so.
    """
    hashname = int(hashlib.sha256(name.encode('utf8')).hexdigest(), 16)
    hashname = base36encode(hashname)[:9]

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

def base36encode(number):
    """Converts an integer to a base36 string."""
    if not isinstance(number, (int)):
        raise TypeError('number must be an integer')
    alphabet='0123456789abcdefghijklmnopqrstuvwxyz'
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return sign + base36

def base36decode(number):
    return int(number, 36)