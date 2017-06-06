import sys
import argparse
from time import sleep
from colorclass import Color
from terminaltables import SingleTable
from datetime import datetime, timedelta

import linode
from linodecli.config import update_namespace

def _get_nodebalancer_or_die(client, label):
        try:
            return client.get_nodebalancers(linode.NodeBalancer.label == label).only()
        except:
            print("No nodebaalncer found with label {}".format(label))
            sys.exit(1)

class NodeBalancer:
    def list(args, client, unparsed=None):
        nodebalancers = client.get_nodebalancers()

        header = [ "label", "region" ]        

        data = [ header ]
        for n in nodebalancers:
            data.append([ n.label, n.region.label ])

        tab = SingleTable(data)
        print(tab.table)

    def create(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a NodeBalancer")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="the label for the NodeBalancer")
        parser.add_argument('-L', '--location', metavar='LOCATION', type=str,
                help="the location for deployment.", )
        
        args = parser.parse_args(args=unparsed, namespace=args)

        n = client.create_nodebalancer(args.location, label=args.label)

        print("Created NodeBalancer {}".format(n.label))

    def rename(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Change a NodeBalancer's label")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The NodeBalancer whose label is to be changed")
        parser.add_argument('new_label', metavar='NEW_LABEL', type=str,
                help="The new label for this NodeBalancer")

        args = parser.parse_args(args=unparsed, namespace=args)

        n = _get_nodebalancer_or_die(client, args.label)
        n.label = args.new_label
        n.save()

    def show(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Shows infomration about a NodeBalancer")
        parser.add_argument('label', metavar='LABEL', type=str, nargs='+',
                help="THe NodeBalancer to show")

        args = parser.parse_args(args=unparsed, namespace=args)

        nodebalancers = []
        for label in args.label:
            nodebalancers.append(_get_nodebalancer_or_die(client, label))

        for n in nodebalancers:
            if args.raw:
                form = args.separator.join([ '{}' for i in range(0,7) ])
            else:
                form = """   label: {}
  region: {}
    ipv4: {}
    ipv6: {}
hostname: {}
throttle: {}"""


            print(form.format(n.label, n.region.label, n.ipv4.address, n.ipv6, n.hostname, n.client_conn_throttle))

            if not args.raw and len(nodebalancers) > 1 and not n == nodebalancers[-1]:
                print()
