"""
The ssh-into plugin allows sshing into Linodes by label or ID

Invoke as follows::

   linode-cli ssh-into LINODE_LABEL [--user USERNAME]

   LINODE_LABEL - the label of the Linode to ssh into
   USERNAME - the user to ssh into the Linode as.  Defaults to root
"""
import argparse
from sys import exit


def call(args, context):
    """
    Invokes this plugin
    """
    parser = argparse.ArgumentParser("linode-cli ssh-into", add_help=True)
    parser.add_argument('label', metavar='LABEL', nargs='?', type=str,
                        help="The label of the Linode to ssh into")
    parser.add_argument('--username', metavar='USERNAME', default='root',
                        help="The user to ssh as.  Defaults to 'root'")

    parsed = parser.parse_args(args)

    result, potential_matches = context.client.call_operation(
            "linodes", "list", ['--label', parsed.label])

    if result != 200:
        # TODO
        print('Something went wrong')
        exit(2)

    potential_matches = potential_matches['data']
    exact_match = None

    # see if we got a match
    for match in potential_matches:
        if match['label'] == parsed.label:
            exact_match = match
            break

    if exact_match is None:
        # no match - stop
        print("No Linode found for label {}".format(parsed.label))

        if potential_matches:
            print('Did you mean {}?'.format(
                '], '.join([p['label'] for p in potential_matches])))
        exit(1)

    # find a public IP Address to use
    public_ip = None
    for ip in exact_match['ipv4']:
        if not ip.startswith('192.168'):
            public_ip = ip
            break

    
    print("sshing in as {}@{}".format(parsed.username, public_ip))
