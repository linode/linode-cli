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
