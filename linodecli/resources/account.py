import argparse
import sys
from datetime import datetime, timedelta
from time import sleep

import linode
from colorclass import Color
from terminaltables import SingleTable

from linodecli.config import update_namespace


class Account:
    def show(args, client, unparsed=None):
        act = client.get_account()
        settings = client.account.get_settings()
        transfer = client.account.get_transfer()

        form = """          managed: {}
          balance: {}
    transfer pool: {}
    transfer used: {}
transfer billable: {}
   billing method: {}
"""

        print(form.format("yes" if settings.managed else "no", "$ {:0.2f}".format(act.balance),
            transfer.quota, transfer.used, transfer.billable,
            "metered")) # billing method must be metered
