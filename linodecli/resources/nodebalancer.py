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

    def throttle(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Adjust the connections per second allowed per client IP for a NodeBalancer, to help mitigate abuse.")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The NodeBalancer whose throttle is to be changed")
        parser.add_argument('connections', metavar='CONNECTIONS', type=int,
                help="The help mitigate abuse, throttle connections per second, per client IP.  0 to disable.")

        args = parser.parse_args(args=unparsed, namespace=args)

        n = _get_nodebalancer_or_die(client, args.label)
        n.client_conn_throttle = args.connections
        n.save()

    def delete(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Delete a NodeBalancer")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="Thre NodeBalancer to delete.")

        args = parser.parse_args(args=unparsed, namespace=args)

        n = _get_nodebalancer_or_die(client, args.label)
        n.delete()

    def config_create(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a NodeBalancer Config (port)")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The NodeBalancer to add the Config to.")
        parser.add_argument('-p', '--port', metavar='PORT', type=int, default=80,
                help="The NodeBalancer config port to bind on (1-65534).  Default is 80")
        parser.add_argument('-L', '--protocol', metavar='PROTOCOL', type=str, default='http',
                help="One of 'tcp', 'http', and 'https'")
        parser.add_argument('-A', '--algorithm', metavar='ALGORITHM', type=str, default='roundrobin',
                help="Balancing algorithm.  Options are 'roundrobin', 'leastconn', and 'source'")
        parser.add_argument('-S', '--stickiness', metavar='STICKINESS', type=str, default='table',
                help="Session persistence.  One of 'none', 'table', 'http_cookie'")
        parser.add_argument('-H', '--checkhealth', metavar='CHECKHEALTH', type=str, default='connection',
                help="Perform acive health checks on the backend nodes.  One of 'connection', 'http', or 'http_body'")
        parser.add_argument('-I', '--checkinterval', metavar="CHECKINTERVAL", type=int, default=5,
                help="Seconds between health check probes (2-3600)")
        parser.add_argument('-T', '--checktimeout', metavar='CHECKTIMEOUT', type=int, default=3,
                help="Seconds to wait before considering the probe a failure (1-30)")
        parser.add_argument('-X', '--checkattempts', metavar='CHECKATTEMPTS', type=int, default=2,
                help="Number of failed probes before taking a node out of rotation (1-30)")
        parser.add_argument('-P', '--checkpath', metavar='CHECKPATH', type=str, default='/',
                help="When check-health='http', the path to request.")
        parser.add_argument('-B', '--checkbody', metavar="CHECKBODY", type=str,
                help="When check-health='http_body', a regex against the expected result body.")
        parser.add_argument('-C', '--sslcert', metavar="SSLCERT", type=str,
                help="SSL certificate served by the NodeBalancer when the protocol is 'https'")
        parser.add_argument('-K', '--sslkey', metavar="SSLKEY", type=str,
                help="Unpassphrased private key for teh SSL certificate whe protocol is 'https'")

        args = parser.parse_args(args=unparsed, namespace=args)

        n = _get_nodebalancer_or_die(client, args.label)

        n.create_config(port=args.port, label="port {}".format(args.port), protocol=args.protocol, algorithm=args.algorithm,
                stickiness=args.stickiness, check=args.checkhealth, check_interval=args.checkinterval, check_health=args.checkhealth,
                check_timeout=args.checktimeout, check_attempts=args.checkattempts, check_path=args.checkpath, check_body=args.checkbody,
                ssl_cert=args.sslcert, ssl_key=args.sslkey)
