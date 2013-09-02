from datetime import datetime

from google.appengine.ext import ndb


class ApiRequestException(Exception):
    pass


class ApiToken(ndb.Model):
    """Stores the state of an OAuth2 bearer token for an API."""

    bearer_token = ndb.StringProperty(required=True, indexed=False)
    last_modified = ndb.DateTimeProperty(indexed=False)

    def _pre_put_hook(self):
        self.last_modified = datetime.now()

