from google.appengine.ext import ndb

from ripl.core.aggregation import Trend


def nuke_trends(count=1000):
    """Delete count Trend entities from the datastore."""

    keys = Trend.query().fetch(count, keys_only=True)
    ndb.delete_multi(keys)

