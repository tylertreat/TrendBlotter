"""This is a simple client wrapper for Google+ trends. Google+ currently does
not expose an API for retrieving trending topics, so we have to rely on screen
scraping for now. As such, this is highly fragile. Also, this currently only
supports worldwide trends and not trends for specific locations.
"""

import logging
import re
import urllib2


def get_trends_by_location(location):
    """Fetch a list of the top 10 trending topics for the given location.

    Args:
        location: location entity to collect trends for.

    Returns:
        a list of tuples consisting of trend name and rating.
    """

    if location.name != 'Worldwide':
        # NOTE: There's currently no way of getting location-specific trends
        return []

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

