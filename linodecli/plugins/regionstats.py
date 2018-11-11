"""
The regionstats plugin queries the API for all Linodes and breaks them down by
region, printing the result to the command line.
"""
import argparse
from sys import exit

def call(args, context):
    """
    Invokes the regionstats plugin
    """
    status, result = context.client.call_operation('linodes', 'list')

    if status != 200:
        print('It failed :(')
        exit(1)

    regions = {}

    for item in result['data']:
        region = item['region']
        if region not in regions:
            regions[region] = 0
        regions[region] += 1

    if not regions:
        print("You don't have any linodes")
        exit(0)

    print("Linodes by Region:")
    for region, number in regions.items():
        print("{}: {}".format(region, number))
