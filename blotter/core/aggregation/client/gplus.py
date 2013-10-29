"""This is a simple client wrapper for Google+ trends. Google+ currently does
not expose an API for retrieving trending topics, so we have to rely on screen
scraping for now. As such, this is highly fragile.
"""

import logging
import re
import urllib2


def get_worldwide_trends():
    """Retrieve a list of the top 10 worldwide Google+ trends.

    Returns:
        a list of tuples consisting of trend name and rating.
    """

    try:
        site_file = urllib2.urlopen('https://plus.google.com/s/a')
        site_raw = site_file.read()
        trends = re.findall('s/(\S*)/posts', site_raw)

        # Reverse so we assign lower scores first
        trends.reverse()

        return [(urllib2.unquote(trend), rating + 1)
                for (rating, trend) in enumerate(trends[:10])]
    except urllib2.URLError:
        logging.error('Failed to load Google+ trends')
        return []

