import sys
import argparse
from time import sleep
from colorclass import Color
from terminaltables import SingleTable
from datetime import datetime, timedelta

import linode
from linodecli.config import update_namespace

class Account:
    def show(args, client, unparsed=None):
        settings = client.account.get_settings()
        transfer = client.account.get_transfer()

        form = """          managed: {}
          balance: {}
    transfer pool: {}
    transfer used: {}
transfer billable: {}
   billing method: {}
"""

        print(form.format("yes" if settings.managed else "no", "$ {:0.2f}".format(settings.balance),
            transfer.max, transfer.used, transfer.billable,
            "metered")) # billing method must be metered
