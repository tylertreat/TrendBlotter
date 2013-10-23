from google.appengine.ext import ndb

from blotter.core.aggregation import Location
from blotter.core.aggregation import Trend


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
    )).order(-Trend.timestamp, -Trend.rating).fetch(count)

