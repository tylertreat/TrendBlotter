from datetime import datetime
from operator import itemgetter
import time

from google.appengine.ext import ndb


AGGREGATION_QUEUE = 'trend-aggregator'
CONTENT_QUEUE = 'content-aggregator'


class ApiRequestException(Exception):

    def __init__(self, message, status):
        self.status = status
        Exception.__init__(self, message)


class ApiToken(ndb.Model):
    """Stores the state of an OAuth2 bearer token for an API."""

    bearer_token = ndb.StringProperty(required=True, indexed=False)
    last_modified = ndb.DateTimeProperty(indexed=False)

    def _pre_put_hook(self):
        self.last_modified = datetime.now()


class Location(ndb.Model):
    """Models a geographic location."""

    # The "user-friendly" location name
    name = ndb.StringProperty(required=True)

    # The WOEID of the location
    woeid = ndb.IntegerProperty(required=True)

    # The "user-friendly" location type (e.g. town, country, etc.)
    type_name = ndb.StringProperty(indexed=False)

    # Location type code
    type_code = ndb.IntegerProperty(indexed=False)

    # The WOEID of this Location's parent
    parent_id = ndb.IntegerProperty(indexed=False)

    # The "user-friendly" name of the country this Location is in
    country = ndb.StringProperty()

    # The code for the country this Location is in
    country_code = ndb.StringProperty(indexed=False)


class Trend(ndb.Model):
    """Models a trending topic at a given moment in time at a specific
    location on Earth.
    """

    location = ndb.KeyProperty(kind=Location, required=True)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    name = ndb.StringProperty(required=True)
    rating = ndb.FloatProperty(required=True)
    content = ndb.JsonProperty(compressed=True)
    has_content = ndb.BooleanProperty()

    def _pre_put_hook(self):
        if self.content:
            self.has_content = True
        else:
            self.has_content = False

    def unix_timestamp(self):
        """Return the timestamp as Unix time."""

        return time.mktime(self.timestamp.timetuple())

    def best_content(self):
        """Return the highest scored content for this Trend."""

        if not self.content:
            return None

        return sorted(self.content, key=itemgetter('score'), reverse=True)[0]


def scale_trend_rating(unscaled):
    """Normalize the given trend rating value."""

    return (99 * (unscaled - 1)) / 9 + 1

