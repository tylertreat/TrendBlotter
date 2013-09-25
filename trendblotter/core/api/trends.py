from google.appengine.ext import ndb

from trendblotter.core.aggregation import Location
from trendblotter.core.aggregation import Trend


def get_trends_for_location(location, count):
    """Fetch the most recent and popular trends for the given location.

    Args:
        location: the location to retrieve trends for.
        count: the number of trends to retrieve.

    Returns:
        a single trend, list of trends, or None.
    """

    if count <= 0:
        return None

    if isinstance(location, Location):
        location = location.name

    return Trend.query(ndb.AND(
        Trend.has_content == True,
        Trend.location == ndb.Key('Location', location)
    )).order(-Trend.rating, -Trend.timestamp).fetch(count)


def get_recent_trends(count, preferred=None, dedupe=True):
    """Fetch recent and popular trends.

    Args:
        count: the number of trends to retrieve.
        preferred: a list of location names to try to get trends for.
        dedupe: ensure that duplicate trends are not returned.

    Returns:
        a dict mapping locations to trends.
    """
    # TODO
    pass

