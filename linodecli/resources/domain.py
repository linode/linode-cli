import os
import sys
import argparse
from colorclass import Color
from terminaltables import SingleTable
from datetime import datetime, timedelta

import linode
from linodecli.config import update_namespace

def _get_domain_or_die(client, label):
        try:
            return client.dns.get_zones(linode.DnsZone.dnszone == label).only()
        except:
            print("No Domain found for {}".format(label))
            sys.exit(1)

def _make_domain_row(d):
    return [
            d.dnszone,
            d.type,
            d.soa_email,
        ]

def _make_domain_record_row(r):
    return [
        r.type,
        r.name,
        r.target,
        r.port
    ]

class Domain:
    def list(args, client, unparsed=None):
        zones = client.dns.get_zones()

        data = [ _make_domain_row(d) for d in zones ]
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
            print("""    domain: {}
      type: {}
 soa email: {}
master ips: {}
     retry: {}
    expire: {}
   refresh: {}
       ttl: {}""".format(d.dnszone, d.type, d.soa_email, d.master_ips, d.retry_sec,
            d.expire_sec, d.refresh_sec, d.ttl_sec))

            if len(domains) > 1 and not d == domains[-1]:
                print()

    def create(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Create a Domain.")
        parser.add_argument('-l','--label', metavar='LABEL', type=str,
                help="The Domain (name).  The zone's name.")
        parser.add_argument('-t','--type', metavar='TYPE', type=str,
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
                help="Optional.  May be provided multiple times.  When teh domain is "
                        "a slave, this is the zone's master DNS servers list.")
        parser.add_argument('-x','--axfrip', metavar='AXFRIP', type=str, nargs='+',
                help="Optional.  May be provided mutliple times.  IP addresses allowed "
                        "to AXFR the entire zone.")

        args = parser.parse_args(args=unparsed, namespace=args)

        z = client.dns.create_zone(args.label, master=(args.type == 'master'),
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
        parser.add_argument('-t','--type', metavar='TYPE', type=str,
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
                help="Optional.  May be provided multiple times.  When teh domain is "
                        "a slave, this is the zone's master DNS servers list.")
        parser.add_argument('-x','--axfrip', metavar='AXFRIP', type=str, nargs='+',
                help="Optional.  May be provided mutliple times.  IP addresses allowed "
                        "to AXFR the entire zone.")

        args = parser.parse_args(args=unparsed, namespace=args)

        z = _get_domain_or_die(client, args.label)

        if args.new_label:
            z.dnszone = args.new_label

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
        parser.add_argument('-t','--type', metavar='TYPE', type=str,
                help="Optional.  Allows domain record filtering by type. "
                        "One of: NS, MX, A, AAAA, CNAME, TXT, or SRV")

        args = parser.parse_args(args=unparsed, namespace=args)

        z = _get_domain_or_die(client, args.label)

        print("Domain records for {}".format(z.dnszone))
        if not z.records:
            print("No records to list.")
            return

        data = []
        for r in z.records:
            if args.type and not r.zone_record_type == args.type:
                continue

            data.push(_make_domain_record_row(r))

        data = [ ['type', 'name', 'target', 'port' ] ] + data

        tab = SingleTable(data)
        print(tab.table)
