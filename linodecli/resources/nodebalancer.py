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
            print("No NodeBalancer found with label {}".format(label))
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
        parser = argparse.ArgumentParser(description="Shows information about a NodeBalancer")
        parser.add_argument('label', metavar='LABEL', type=str, nargs='+',
                help="The NodeBalancer to show")

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
                help="The NodeBalancer to delete.")

        args = parser.parse_args(args=unparsed, namespace=args)

        n = _get_nodebalancer_or_die(client, args.label)
        n.delete()

    def config_list(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="List all configs (ports) for a specific NodeBalancer")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The NodeBalancer to list.")

        args = parser.parse_args(args=unparsed, namespace=args)

        n = _get_nodebalancer_or_die(client, args.label)
        configs = n.configs

        if not configs:
            print("{} has no configs".format(n.label))
            sys.exit(0)

        data = [ [ "port", "protocol", "algorithm", "stickiness", "check" ] ]

        for c in configs:
            data.append([ c.port, c.protocol, c.algorithm, c.stickiness, c.check ])

        tab = SingleTable(data)
        print(tab.table)

    def config_show(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Display information about a specific NodeBalancer config/port")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The NodeBalancer to show.")
        parser.add_argument('port', metavar='PORT', type=int,
                help="The NodeBalancer port or config port.")

        args = parser.parse_args(args=unparsed, namespace=args)

        n = _get_nodebalancer_or_die(client, args.label)
        config = [ c for c in n.configs if c.port == args.port ]

        if not config:
            print("{} has no config on port {}".format(args.label, args.port))
            sys.exit(0)
        config = config[0]

        form = """          port: {}
      protocol: {}
     algorithm: {}
    stickiness: {}
  check-health: {}
check-interval: {}
 check-timeout: {}
check-attempts: {}
    check-path: {}
   check: body: {}
"""

        print(form.format(config.port, config.protocol, config.algorithm, config.stickiness, config.check,
            config.check_interval, config.check_timeout, config.check_attempts, config.check_path, config.check_body))

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
                help="Perform active health checks on the backend nodes.  One of 'connection', 'http', or 'http_body'")
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
                help="Unpassphrased private key for the SSL certificate when protocol is 'https'")

        args = parser.parse_args(args=unparsed, namespace=args)

        n = _get_nodebalancer_or_die(client, args.label)

        n.create_config(port=args.port, label="port {}".format(args.port), protocol=args.protocol, algorithm=args.algorithm,
                stickiness=args.stickiness, check=args.checkhealth, check_interval=args.checkinterval, check_health=args.checkhealth,
                check_timeout=args.checktimeout, check_attempts=args.checkattempts, check_path=args.checkpath, check_body=args.checkbody,
                ssl_cert=args.sslcert, ssl_key=args.sslkey)

    def config_update(args, client, unparsed=None):
        raise NotImplementedError("This feature is coming soon!")

    def config_delete(args, client, unparsed=None):
        raise NotImplementedError("This feature is coming soon!")

    def node_list(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="List all Nodes for a specific NodeBalancer port.")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="A specific NodeBalancer.")
        parser.add_argument('port', metavar='PORT', type=int,
                help="The NodeBalancer port or config port.")

        args = parser.parse_args(args=unparsed, namespace=args)

        n = _get_nodebalancer_or_die(client, args.label)
        config = [ c for c in n.configs if c.port == args.port ]

        if not config:
            print("{} has no config on port {}".format(args.label, args.port))
            sys.exit(0)
        config = config[0]

        nodes = config.nodes

        if not nodes:
            print("{} has no Nodes for port {}".format(args.label, args.port))

        data = [ [ "name", "status", "address" ] ]
        for n in nodes:
            data.append([ n.label, n.status, n.address ])

        tab = SingleTable(data)
        print(tab.table)

    def node_show(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Show detailed information about a specific Node for a specific NodeBalancer port.")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="A specific NodeBalancer.")
        parser.add_argument('port', metavar='PORT', type=int,
                help="The NodeBalancer port or config port.")
        parser.add_argument('name', metavar='NAME', type=str,
                help="The name of the Node to show.")

        args = parser.parse_args(args=unparsed, namespace=args)

        n = _get_nodebalancer_or_die(client, args.label)
        config = [ c for c in n.configs if c.port == args.port ]

        if not config:
            print("{} has no config on port {}".format(args.label, args.port))
            sys.exit(0)
        config = config[0]

        node = [ n for n in config.nodes if n.label == args.name ]

        if not node:
            print("{} port {} has no node named {}".format(args.label, args.port, args.name))
            sys.exit(0)
        node = node[0]

        form="""   name: {}
address: {}
 status: {}
   mode: {}
 weight: {}
"""
        print(form.format(node.label, node.address, node.status, node.mode, node.weight))


    def node_create(args, client, unparsed=None):
        raise NotImplementedError("This feature is coming soon!")

    def node_update(args, client, unparsed=None):
        raise NotImplementedError("This feature is coming soon!")

    def node_delete(args, client, unparsed=None):
        raise NotImplementedError("This feature is coming soon!")
