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

        form = """          managed: {}
         balancer: {}
    transfer pool: {}
    transfer used: {}
transfer billable: {}
   billing method: {}
"""

        print(form.format("yes" if settings.managed else "no", "$ {:0.2f}".format(settings.balance),
            "?", "?", "?", # TODO - transfer pool and used are not returned by the api
            "metered")) # billing method must be metered
