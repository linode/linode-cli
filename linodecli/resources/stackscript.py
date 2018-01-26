import argparse
import os
import sys
from datetime import datetime, timedelta

import linode
from colorclass import Color
from terminaltables import SingleTable

from linodecli.config import update_namespace


def _get_stackscript_or_die(client, label):
        try:
            if label.isdigit():
                return linode.StackScript(client, int(label))
            else:
                return client.linode.get_stackscripts(linode.StackScript.label == label).only() #TODO - mine_only=True
        except:
            print("No StackScript found for {}".format(label))
            sys.exit(1)

#TODO - DRY
def _colorize_yesno(yesno):
    if yesno == 'yes' or yesno == True:
        return Color('{green}yes{/green}')
    return Color('{red}no{/red}')

def _make_stackscript_row(ss):
    return [
        ss.id,
        ss.label,
        _colorize_yesno(ss.is_public),
        ss.rev_note
    ]

class StackScript:
    def list(args, client, unparsed=None):
        stackscripts = client.linode.get_stackscripts(mine_only=True)

        data = [ _make_stackscript_row(s) for s in stackscripts ]
        data = [ [ 'id', 'label', 'public', 'revision note' ] ] + data

        tab = SingleTable(data)
        print(tab.table)

    def show(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Shows detailed information about one or more StackScripts")
        parser.add_argument('label', metavar='LABEL', type=str, nargs='+',
                help="The StackScripts to show")

        args = parser.parse_args(args=unparsed, namespace=args)

        stackscripts = []
        for label in args.label:
            stackscripts.append(_get_stackscript_or_die(client, label))

        for s in stackscripts:
            print("""             label: {}
                id: {}
            public: {}
     revision note: {}
 total deployments: {}
active deployments: {}""".format(s.label, s.id, "yes" if s.is_public else "no", s.rev_note, s.deployments_total,
                    s.deployments_active))

            if len(stackscripts) > 1 and not s == stackscripts[-1]:
                print()

    def source(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Shows the source of one or more StackScripts")
        parser.add_argument('label', metavar='LABEL', type=str, nargs='+',
                help="The StackScripts to show")

        args = parser.parse_args(args=unparsed, namespace=args)

        stackscripts = []
        for label in args.label:
            stackscripts.append(_get_stackscript_or_die(client, label))

        for s in stackscripts:
            print("""{}:
{}""".format(s.label, s.script))

            if len(stackscripts) > 1 and not s == stackscripts[-1]:
                print()

    def create(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a StackScript")
        parser.add_argument('-l','--label', metavar='LABEL', type=str, required=True,
                help="The label (name) for the StackScript")
        parser.add_argument('-d','--distribution', metavar='DISTRO', type=str, nargs='+', required=True,
                help="The Distributions to deploy.")
        parser.add_argument('-c','--codefile', metavar='FILE', type=str, required=True,
                help="Path to the script file.")
        parser.add_argument('-p','--ispublic', action='store_true',
                help="Optional.  Whether this StackScript is published in the Library, for everyone to use. "
                        "If included, the StackScript is public.  Otherwise, it is private.")
        parser.add_argument('-D','--description', metavar='DESC', type=str,
                help="Optional.  Notes describing details about the StackScript")
        parser.add_argument('-r','--revnote', metavar='NOTE', type=str,
                help="Optional.  Note for describing the version.")

        args = parser.parse_args(args=unparsed, namespace=args)

        s = client.linode.create_stackscript(args.label, args.codefile, args.distribution, desc=args.description, public=args.ispublic,
                rev_note=args.revnote)

    def update(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Update a StackScript")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The label (name) for the StackScript.")
        parser.add_argument('-n','--new-label', metavar="NEW_LABEL", type=str,
                help="Optional.  Renames the StackScript.")
        parser.add_argument('-d','--new_distribution', metavar="DISTRO", type=str, nargs='+',
                help="Optional.  The Distributions to deploy.")
        parser.add_argument('-c','--codefile', metavar='FILE', type=str,
                help="Optional.  Path to the new script file.")
        parser.add_argument('-p','--ispublic', action='store_true',
                help="Makes this StackScript public if included.  This is not a reversible operation")
        parser.add_argument('-D','--description', metavar='DESC', type=str,
                help="Optional.  Notes describing details about the StackScript.")
        parser.add_argument('-r','--revnote', metavar='NOTE', type=str,
                help="Optional.  Note for describing the version.")

        args = parser.parse_args(args=unparsed, namespace=args)

        s = _get_stackscript_or_die(client, args.label)

        if args.codefile:
            if not os.path.isfile(args.codefile):
                print("File not found: {}".format(args.codefile))
                sys.exit(1)

            with open(args.codefile) as c:
                script = c.read()
            s.script = script

        if args.ispublic:
            s.is_public = True

        if args.new_label:
            s.label = args.new_label

        if args.new_distribution:
            distro = args.new_distribution
            if not isinstance(distro, list):
                distro = [ distro ]
            s.distributions = distro

        if args.revnote:
            s.rev_note = args.revnote

        s.save()
