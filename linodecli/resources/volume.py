import argparse
import sys
from datetime import datetime, timedelta
from time import sleep

import linode
from colorclass import Color
from terminaltables import SingleTable

from linodecli.config import update_namespace


def _make_volume_row(volume):
    return [
        volume.label,
        _colorize_status(volume.status),
        "{} GB".format(volume.size),
        volume.region.id,
        volume.linode.label if volume.linode else '',
    ]

def _colorize_status(status):
    if status in ('active'):
        return Color('{green}'+status+'{/green}')
    return Color('{red}'+status+'{/red}')

def _get_volume_or_die(client, label):
        try:
            return client.get_volumes(linode.Volume.label == label).only()
        except:
            print("No volume found with label {}".format(label))
            sys.exit(1)

class Volume:
    def list(args, client, unparsed=None):
        volumes = client.get_volumes()

        header = [ "label", "status", "size", "location", "attached to" ]

        data = [ header ] + [ _make_volume_row(v) for v in volumes ]
        tab = SingleTable(data)
        print(tab.table)

    def show(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Shows information about a Volume")
        parser.add_argument('label', metavar='LABEL', type=str, nargs='+',
                help="The Volume to show")

        args = parser.parse_args(args=unparsed, namespace=args)

        volumes = []
        for label in args.label:
            volumes.append(_get_volume_or_die(client, label))

        for v in volumes:
            if args.raw:
                form = args.separator.join([ '{}' for i in range(0,5) ])
            else:
                form = """      label: {}
     status: {}
   location: {}
       size: {} GB
attached to: {}"""


            print(form.format(v.label, v.status, v.region.id, v.size, v.linode.label if v.linode else ""))

            if not args.raw and len(volumes) > 1 and not v == volumes[-1]:
                print()

    def create(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a volume")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The label for the new volume")
        parser.add_argument('-L', '--location', metavar='LOCATION', type=str,
                help="The location for this volume.")
        parser.add_argument('-l', '--linode', metavar='LINODE', type=str,
                help="The Linode to attach the new volume to.  Implies location.")
        parser.add_argument('-s', '--size', metavar='SIZE', type=int,
                help="The size of the new volume in GB (defaults to 20)")
        # TODO - linode-api does not support this
        #parser.add_argument('-w', '--wait', metavar='TIME', type=int, nargs='?', const=5,
        #    help="The amount of minutes to wait for completion.  If given with no argument, defaults to 5")

        args = parser.parse_args(args=unparsed, namespace=args)

        params = {}
        if args.linode:
            try:
                to_linode = client.linode.get_instances(linode.Linode.label == args.linode).only()
            except:
                print("No linode found for label {}".format(args.linode))
                sys.exit(1)
            params.update({ "linode": to_linode.id })
        elif args.location:
            params.update({ "region": args.location })
        else:
            print("Either --linode or --location must be provided.")
            sys.exit(1)

        if args.size:
            params['size'] = args.size

        v = client.create_volume(args.label, **params)

        # TODO - linode-api does not support this
        #if args.wait:
        #    _wait_for_state(args.wait, v, 'active')

    def rename(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Change a volume's label")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The volume whose label is to be changed")
        parser.add_argument('new_label', metavar='NEW_LABEL', type=str,
                help="The new label for this volume")

        args = parser.parse_args(args=unparsed, namespace=args)

        v = _get_volume_or_die(client, args.label)
        v.label = args.new_label
        v.save()

    def delete(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Delete a volume")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The volume to delete")

        args = parser.parse_args(args=unparsed, namespace=args)

        v = _get_volume_or_die(client, args.label)
        v.delete()


    def attach(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Attach this volume to a Linode")
        parser.add_argument('label', metavar='LABEL', type=str,
            help="The volume to attach")
        parser.add_argument('linode', metavar='LINODE', type=str,
            help="The Linode label to attach this volume to.")

        args = parser.parse_args(args=unparsed, namespace=args)

        volume = _get_volume_or_die(client, args.label)
        try:
            to_linode = client.linode.get_instances(linode.Linode.label == args.linode).only()
        except:
            print("No linode found for label {}".format(args.linode))
            sys.exit(1)

        volume.attach(to_linode)
        print("{} attached to {}".format(args.label, to_linode.label))

    def detach(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Attach this volume to a Linode")
        parser.add_argument('label', metavar='LABEL', type=str,
            help="The volume to attach")

        args = parser.parse_args(args=unparsed, namespace=args)

        volume = _get_volume_or_die(client, args.label)

        volume.detach()
        print("{} has been detached".format(args.label))
