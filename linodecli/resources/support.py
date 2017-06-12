import sys
import argparse
from time import sleep
from colorclass import Color
from terminaltables import SingleTable
from datetime import datetime, timedelta

import linode
from linodecli.config import update_namespace

def _colorize_updater(updater):
    if updater == 'Linode':
        return Color('{green}Linode{/green}')
    return Color('{yellow}'+updater+'{/yellow}')


class Support:
    def list(args, client, unparsed=None):
        tickets = client.support.get_tickets(linode.SupportTicket.closed == None)
                # TODO linode.SupportTicket.status != 'closed')

        data = [ [ "id", "summary", "regarding", "updated", "updated by" ] ]

        for t in tickets:
            data.append([ t.id, t.summary, t.entity.label if t.entity else '', t.updated,
                    _colorize_updater(t.updated_by) ])

        tab = SingleTable(data)
        print(tab.table)

    def show(args, client, unparsed=None):
        parser = argparse.ArgumentParser(description="Show a ticket and its replies.")
        parser.add_argument('ticketid', metavar='TICKETID', type=int,
            help="The ticket to show.")

        args = parser.parse_args(args=unparsed, namespace=args)

        t = linode.SupportTicket(client, args.ticketid)

        try:
            t.summary
        except:
            print("No ticket found with ID {}".format(args.ticketid))
            sys.exit(0)

        print(t.summary)
        print("{}; Status: {}".format(t.opened, t.status))
        if t.entity:
            print("Regarding {}".format(t.entity.label))
        print("=================================")
        print('| ' + '\n| '.join(t.description.split('\n')))

        for r in t.replies:
            print("+================================")
            print("| Reply {}: {}".format(r.created, r.created_by))
            print("+--------------------------------")
            print('| ' + '\n| '.join(r.description.split('\n')))
