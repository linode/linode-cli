import sys
import argparse
from time import sleep
from colorclass import Color
from terminaltables import SingleTable
from datetime import datetime, timedelta

import linode
from linodecli.config import update_namespace

def _make_event_row(event):
    return [
            _colorize_seen("!" if not event.seen else "*" if not event.read else " "),
            event.entity.label,
            event.action,
            event.username,
            _colorize_status(event.status),
            event.created,
    ]

def _colorize_status(status):
    if status in ('finished'):
        return Color('{green}'+status+'{/green}')
    if status in ('started'):
        return Color('{yellow}'+status+'{/yellow}')
    if status in ('scheduled', 'notification'):
        return status
    return Color('{red}'+status+'{/red}')

def _colorize_seen(seen):
    if seen == '!':
        return Color('{green}●{/green}')
    if seen == '*':
        return Color('{yellow}●{/yellow}')
    return seen

class Event:
    def list(args, client, unparsed=None):
        events = client.account.get_events()

        header = [ " ", "entity", "action", "user", "status", "time" ]        

        data = [ header ]
        for e in events[:10]:
            data.append(_make_event_row(e))

        tab = SingleTable(data)
        print(tab.table)

    def seen(args, client, unparsed=None):
        event = client.account.get_events().first()

        client.account.mark_last_seen_event(event)
