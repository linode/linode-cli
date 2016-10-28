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

