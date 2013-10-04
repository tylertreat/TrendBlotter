from google.appengine.ext import ndb

from blotter.core.aggregation import Trend


def get_previous_trend_rating(trend, location):
    """Fetch the trend's last rating.

    Args:
        trend: the trend to retrieve the previous rating for
        location: the location the trend pertains to.

    Returns:
        trend's last rating or None if it has never trended.
    """

    latest = Trend.query(
        Trend.name == trend,
        Trend.location == ndb.Key('Location', location)).order(
        -Trend.timestamp).get()

    if not latest:
        return None

    return latest.rating

