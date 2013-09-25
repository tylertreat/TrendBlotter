from google.appengine.ext import ndb

from trendblotter.core.aggregation import Trend


def nuke_trends(count=1000):
    """Delete count Trend entities from the datastore."""

    keys = Trend.query().fetch(count, keys_only=True)
    ndb.delete_multi(keys)

