import argparse
import os
import sys
from datetime import datetime, timedelta

import linode
from colorclass import Color
from terminaltables import SingleTable

from linodecli.config import update_namespace


def _get_domain_or_die(client, label):
        try:
            return client.get_domains(linode.Domain.domain == label).only()
        except:
            print("No Domain found for {}".format(label))
            sys.exit(1)

def _make_domain_row(d):
    return [
            d.domain,
            d.type,
            d.soa_email,
        ]

def _make_domain_record_row(r):
    return [
        r.type,
        r.name,
        r.target,
        str(r.port)
    ]

class Domain:
    def list(args, client, unparsed=None):
        zones = client.get_domains()

        data = [ _make_domain_row(d) for d in zones ]
        if args.raw:
            for d in data:
                print(args.separator.join(d))
        else:
            data = [ [ 'domain', 'type', 'soa email' ] ] + data

            tab = SingleTable(data)
            print(tab.table)

    def show(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Shows detailed information about one or more Domains")
        parser.add_argument('label', metavar='LABEL', type=str, nargs='+',
                help="The Domains to show")

        args = parser.parse_args(args=unparsed, namespace=args)

        domains = []
        for label in args.label:
            domains.append(_get_domain_or_die(client, label))

        for d in domains:
            if args.raw:
                form = args.separator.join([ '{}' for i in range(0, 7) ])
            else:
                form = """    domain: {}
      type: {}
 soa email: {}
master ips: {}
     retry: {}
    expire: {}
   refresh: {}
       ttl: {}"""

            print(form.format(d.domain, d.type, d.soa_email, d.master_ips, d.retry_sec,
            d.expire_sec, d.refresh_sec, d.ttl_sec))

            if len(domains) > 1 and not d == domains[-1]:
                print()

    def create(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a Domain.")
        parser.add_argument('-l','--label', metavar='LABEL', type=str,
                help="The Domain (name).  The zone's name.")
        parser.add_argument('-y','--type', metavar='TYPE', type=str,
                default="master",
                help="Either master or slave.  Default: master")
        parser.add_argument('-e','--email', metavar='EMAIL', type=str,
                help="SOA email address.  Required for master domains.")
        parser.add_argument('-D','--description', metavar='DESC', type=str,
                help="Optional.  Notes describing details about the Domain.")
        parser.add_argument('-R','--refresh', metavar='REF', type=int, default=0,
                help="Optional.  Default: 0")
        parser.add_argument('-Y','--retry', metavar='RETRY', type=int, default=0,
                help="Optional.  Default: 0")
        parser.add_argument('-E','--expire', metavar='EXP', type=int, default=0,
                help="Optional.  Default: 0")
        parser.add_argument('-T','--ttl', metavar='TTL', type=int, default=0,
                help="Optional.  Default: 0")
        parser.add_argument('-g','--group', metavar='GRP', type=str,
                help="Optional.  Linode Manager display group to place this Domain under.")
        parser.add_argument('-s','--status', metavar='STS', type=str, default='active',
                help="Optional.  Statuses are active, edit, or disabled. Default: active")
        parser.add_argument('-m','--masterip', metavar='IP', type=str, nargs='+',
                help="Optional.  May be provided multiple times.  When the domain is "
                        "a slave, this is the zone's master DNS servers list.")
        parser.add_argument('-x','--axfrip', metavar='AXFRIP', type=str, nargs='+',
                help="Optional.  May be provided multiple times.  IP addresses allowed "
                        "to AXFR the entire zone.")

        args = parser.parse_args(args=unparsed, namespace=args)

        z = client.create_domain(args.label, master=(args.type == 'master'),
                display_group=args.group, description=args.description,
                soa_email=args.email, refresh_sec=args.refresh, master_ips=args.masterip,
                axfr_ips=args.axfrip, expire_sec=args.expire, retry_sec=args.retry,
                ttl_sec=args.ttl)

    def update(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a Domain.")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The Domain to update.")
        parser.add_argument('-n','--new-label', metavar='LABEL', type=str,
                help="Optional.  Renames the domain.")
        parser.add_argument('-y','--type', metavar='TYPE', type=str,
                help="Either master or slave.")
        parser.add_argument('-e','--email', metavar='EMAIL', type=str,
                help="SOA email address.  Required for master domains.")
        parser.add_argument('-D','--description', metavar='DESC', type=str,
                help="Optional.  Notes describing details about the Domain.")
        parser.add_argument('-R','--refresh', metavar='REF', type=int,
                help="Optional.  Default: 0")
        parser.add_argument('-Y','--retry', metavar='RETRY', type=int,
                help="Optional.  Default: 0")
        parser.add_argument('-E','--expire', metavar='EXP', type=int,
                help="Optional.  Default: 0")
        parser.add_argument('-T','--ttl', metavar='TTL', type=int,
                help="Optional.  Default: 0")
        parser.add_argument('-g','--group', metavar='GRP', type=str,
                help="Optional.  Linode Manager display group to place this Domain under.")
        parser.add_argument('-s','--status', metavar='STS', type=str,
                help="Optional.  Statuses are active, edit, or disabled. Default: active")
        parser.add_argument('-m','--masterip', metavar='IP', type=str, nargs='+',
                help="Optional.  May be provided multiple times.  When the domain is "
                        "a slave, this is the zone's master DNS servers list.")
        parser.add_argument('-x','--axfrip', metavar='AXFRIP', type=str, nargs='+',
                help="Optional.  May be provided multiple times.  IP addresses allowed "
                        "to AXFR the entire zone.")

        args = parser.parse_args(args=unparsed, namespace=args)

        z = _get_domain_or_die(client, args.label)

        if args.new_label:
            z.domain = args.new_label

        if args.type:
            z.type = args.type

        if args.email:
            z.soa_email = args.email

        if args.description:
            z.description = args.description

        if args.refresh:
            z.refresh_sec = args.refresh

        if args.retry:
            z.retry_sec = args.retry

        if args.expire:
            z.expire_sec = args.expire

        if args.ttl:
            z.ttl_sec = args.ttl

        if args.group:
            z.group = args.group

        if args.status:
            z.status = args.status

        if args.masterip:
            z.master_ips = args.masterip

        if args.axfrip:
            z.axfr_ips = args.axfrip

        z.save()

    def delete(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a Domain.")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The Domain to delete.")

        args = parser.parse_args(args=unparsed, namespace=args)

        z = _get_domain_or_die(client, args.label)

        z.delete()

    def record_list(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a Domain.")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The Domain to delete.")
        parser.add_argument('-y','--type', metavar='TYPE', type=str,
                help="Optional.  Allows domain record filtering by type. "
                        "One of: NS, MX, A, AAAA, CNAME, TXT, or SRV")

        args = parser.parse_args(args=unparsed, namespace=args)

        z = _get_domain_or_die(client, args.label)

        if not args.raw:
            print("Domain records for {}".format(z.domain))
        if not z.records:
            print("No records to list.")
            return

        data = []
        for r in z.records:
            if args.type and not r.zone_record_type == args.type:
                continue

            data.append(_make_domain_record_row(r))

        if args.raw:
            for d in data:
                print(args.separator.join(d))
        else:
            data = [ ['type', 'name', 'target', 'port' ] ] + data

            tab = SingleTable(data)
            print(tab.table)

    def record_create(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a Domain record.")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The Domain to add the record to.")
        parser.add_argument('-y','--type', metavar='TYPE', type=str,
                help="One of: NS, MX, A, AAAA, CNAME, TXT, or SRV")
        parser.add_argument('-n','--name', metavar='NAME', type=str,
                help="Optional.  The hostname or FQDN.  When Type=MX the subdomain "
                        "to delegate to the Target MX server.  Default: blank")
        parser.add_argument('-p','--port', metavar='PORT', type=int,
                help="Optional.  Default: 80")
        parser.add_argument('-R','--target', metavar='TARGET', type=str,
                help="Optional.  When Type=MX the hostname.  When Type=CNAME the "
                        "target of the alias. When Type=TXT the value of the record. "
                        "When Type=A or AAAA the token of '[remote_addr]' will be "
                        "substituted with the IP address of the request.")
        parser.add_argument('-P','--priority', metavar='PRI', type=int,
                help="Optional. Priority for MX and SRV records, 0-255.  Default: 10")
        parser.add_argument('-W','--weight', metavar='WEI', type=int,
                help="Optional.  Default: 5")
        parser.add_argument('-L','--protocol', metavar='PRO', type=str,
                help="Optional.  The protocol to append to an SRV record.  Ignored "
                        "on other record types. Default: blank.")
        parser.add_argument('-T','--ttl', metavar='TTL', type=int,
                help="Optional.  Default: 0")

        args = parser.parse_args(args=unparsed, namespace=args)

        z = _get_domain_or_die(client, args.label)

        z.create_record(args.type, name=args.name, port=args.port, target=args.target,
                priority=args.priority, weight=args.weight, protocol=args.protocol,
                ttl_sec=args.ttl)

    def record_update(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a Domain record.")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The Domain to add the record to.")
        parser.add_argument('-n','--name', metavar='NAME', type=str,
                help="Optional.  The hostname or FQDN.  When Type=MX the subdomain "
                        "to delegate to the Target MX server.  Default: blank")
        parser.add_argument('-p','--port', metavar='PORT', type=int,
                help="Optional.  Default: 80")
        parser.add_argument('-R','--target', metavar='TARGET', type=str,
                help="Optional.  When Type=MX the hostname.  When Type=CNAME the "
                        "target of the alias. When Type=TXT the value of the record. "
                        "When Type=A or AAAA the token of '[remote_addr]' will be "
                        "substituted with the IP address of the request.")
        parser.add_argument('-P','--priority', metavar='PRI', type=int,
                help="Optional. Priority for MX and SRV records, 0-255.  Default: 10")
        parser.add_argument('-W','--weight', metavar='WEI', type=int,
                help="Optional.  Default: 5")
        parser.add_argument('-L','--protocol', metavar='PRO', type=str,
                help="Optional.  The protocol to append to an SRV record.  Ignored "
                        "on other record types. Default: blank.")
        parser.add_argument('-T','--ttl', metavar='TTL', type=int,
                help="Optional.  Default: 0")
        parser.add_argument('match_type', metavar='MATCH_TYPE', type=str,
                help="The type of record to delete.  One of: NS, MX, A, AAA "
                        "CNAME, TXT, or SRV")
        parser.add_argument('match', metavar='MATCH', type=str,
                help="The match for the record to delete.  Match to a name or target")

        args = parser.parse_args(args=unparsed, namespace=args)

        z = _get_domain_or_die(client, args.label)

        to_update = [ r for r in z.records if r.type == args.match_type and \
                ( r.target == args.match or r.name == args.match ) ]

        if not len(to_update) == 1:
            print("Ambiguous criteria - found {} records instead of 1".format(len(to_update)))

        to_update = to_update[0]

        if args.name:
            to_update.name=args.name

        if args.port:
            to_update.port=args.port

        if args.target:
            to_update.target=args.target

        if args.priority:
            to_update.priority=args.priority

        if args.weight:
            to_update.weight=args.weight

        if args.protocol:
            to_update.protocol=args.protocol

        if args.ttl:
            to_update.ttl_sec=args.ttl

        to_update.save()

    def record_delete(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a Domain.")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The Domain containing the record to delete.")
        parser.add_argument('match_type', metavar='MATCH_TYPE', type=str,
                help="The type of record to delete.  One of: NS, MX, A, AAA "
                        "CNAME, TXT, or SRV")
        parser.add_argument('match', metavar='MATCH', type=str,
                help="The match for the record to delete.  Match to a name or target")

        args = parser.parse_args(args=unparsed, namespace=args)

        z = _get_domain_or_die(client, args.label)

        to_delete = [ r for r in z.records if r.type == args.match_type and \
                ( r.target == args.match or r.name == args.match ) ]

        if not len(to_delete) == 1:
            print("Ambiguous criteria - found {} records instead of 1".format(len(to_delete)))

        to_delete = to_delete[0]
        to_delete.delete()

    def record_show(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a Domain.")
        parser.add_argument('label', metavar='LABEL', type=str,
                help="The Domain containing the record to delete.")
        parser.add_argument('match_type', metavar='MATCH_TYPE', type=str,
                help="The type of record to delete.  One of: NS, MX, A, AAA "
                        "CNAME, TXT, or SRV")
        parser.add_argument('match', metavar='MATCH', type=str,
                help="The match for the record to delete.  Match to a name or target")

        args = parser.parse_args(args=unparsed, namespace=args)

        z = _get_domain_or_die(client, args.label)

        to_show = [ r for r in z.records if r.type == args.match_type and \
                ( r.target == args.match or r.name == args.match ) ]

        if not len(to_show) == 1:
            print("Ambiguous criteria - found {} records instead of 1".format(len(to_show)))

        to_show = to_show[0]

        if args.raw:
            form = args.separator.join([ '{}' for i in range(0, 8) ])
        else:
            form = """domain: {}

    type: {}
    name: {}
  target: {}
    port: {}
  weight: {}
priority: {}
     ttl: {}"""

        print(form.format(z.domain, to_show.type, to_show.name, to_show.target, to_show.port, to_show.weight,
                        to_show.priority, to_show.ttl_sec))
