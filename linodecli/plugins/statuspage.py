"""
The StatusPage plugin allows querying status.linode.com from the command line!
This plugin requires BeautifulSoup
"""
from requests import get
from sys import exit

# if this isn't installed, don't blow up
try:
    from bs4 import BeautifulSoup
    HAS_SOUP=True
except ImportError:
    HAS_SOUP=False

def call(args, context):
    """
    """
    if not HAS_SOUP:
        print('The statuspage plugin requires BeautifulSoup.  You must install '
              'it with `pip install beautifulsoup` before this plugin can be used.')
        exit(2)

    response = get('https://status.linode.com')

    if response.status_code != 200:
        # the status page is down? 
        print('Could not fetch status.linode.com: {}'.format(response.status_code))
        exit(1)

    page = response.content
    soup = BeautifulSoup(page, 'html.parser')

    overall_status = soup.find('span', class_='status').text.strip()

    itemized_status = soup.find_all('div', class_='component-inner-container')
    status_items = []

    for item in itemized_status:
        # parse the relevant info out of the items
        is_subitem = 'border-color' not in item.parent.attrs['class']
        status = item.attrs['data-component-status']
        name = item.find('span', class_='name').text.strip()

        status_items.append((name, is_subitem, status))

    print(overall_status)
    print()

    for name, is_subitem, status in status_items:
        print('{}{}\t{}'.format('+ ' if is_subitem else '', name, status))
        
