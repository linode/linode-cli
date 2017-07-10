import sys
import argparse
from time import sleep
from colorclass import Color
from terminaltables import SingleTable
from datetime import datetime, timedelta

import linode
from linodecli.config import update_namespace

def _make_volume_row(volume):
    return [
        volume.label,
        _colorize_status(volume.status),
        "{} GB".format(volume.size),
        volume.region.label,
        volume.linode.label if volume.linode else None,
    ]

def _colorize_status(status):
    if status in ('active'):
        return Color('{green}'+status+'{/green}')
    return Color('{red}'+status+'{/red}')

def _get_volume_or_die(client, label):
        try:
            return client.linode.get_volumes(linode.Volume.label == label).only()
        except:
            print("No volume found with label {}".format(label))
            sys.exit(1)

class Volume:
    def list(args, client, unparsed=None):
        volumes = client.linode.get_volumes()

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


            print(form.format(v.label, v.status, v.region.label, v.size, v.linode.label if v.linode else ""))

            if not args.raw and len(volumes) > 1 and not v == volumes[-1]:
                print()
