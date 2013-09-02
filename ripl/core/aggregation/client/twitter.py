import base64
from httplib2 import Http
import json
import logging
import urllib

from google.appengine.api import memcache

from ripl.core.aggregation import ApiToken


API = 'https://api.twitter.com'
BEARER_TOKEN_ENDPOINT = '/oauth2/token'
TWITTER_API_TOKEN = 'twitter_api_token'


def get_bearer_token(consumer_key, consumer_secret, force_refresh=False):
    """Exchange the Twitter API consumer key and secret for a bearer token to
    be used with application-only requests. When set to True, force_refresh
    will force a call to Twitter's token endpoint, bypassing any caching
    mechanisms.
    """

    if not force_refresh:
        # First check if there is a cached token
        cached_token = memcache.get(TWITTER_API_TOKEN)
        if cached_token:
            return cached_token

        # Then check the datastore
        cached_token = ApiToken.get_by_id(TWITTER_API_TOKEN)
        if cached_token:
            memcache.set(TWITTER_API_TOKEN, cached_token.bearer_token)
            return cached_token.bearer_token

    # Otherwise, exchange credentials and store the new token
    encoded_key = urllib.quote(consumer_key)
    encoded_secret = urllib.quote(consumer_secret)

    credentials = '%s:%s' % (encoded_key, encoded_secret)
    encoded_credentials = base64.b64encode(credentials)

    http = Http()
    content_type = 'application/x-www-form-urlencoded;charset=UTF-8'
    headers = {'Authorization': 'Basic %s' % encoded_credentials,
               'Content-Type': content_type}

    resp, content = http.request('%s%s' % (API, BEARER_TOKEN_ENDPOINT), 'POST',
                                 body='grant_type=client_credentials',
                                 headers=headers)

    if resp.status != 200:
        logging.warn('Failed to get Twitter token (status %d)' % resp.status)
        return None

    content = json.loads(content)

    # Verify that a bearer token is present
    if (content.get('token_type', None) != 'bearer'
            or 'access_token' not in content):
        logging.warn('Failed to get Twitter token (bad response)')
        return None

    bearer_token = content['access_token']

    # Write the new token to memcache and datastore
    memcache.set(TWITTER_API_TOKEN, bearer_token)
    ApiToken(id=TWITTER_API_TOKEN, bearer_token=bearer_token).put()

    return bearer_token

