import base64
import unittest
import urllib

from mock import Mock
from mock import patch

from ripl.core.aggregation.client import twitter


class TestGetBearerToken(unittest.TestCase):

    def setUp(self):
        self.consumer_key = 'key'
        self.consumer_secret = 'secret'

    @patch('ripl.core.aggregation.client.twitter.memcache')
    def test_from_memcache(self, mock_memcache):
        """Ensure that the bearer token is returned from memcache when present
        and force_refresh is False.
        """

        expected = 'foo'
        mock_memcache.get.return_value = expected

        actual = twitter.get_bearer_token(self.consumer_key,
                                          self.consumer_secret)

        from ripl.core.aggregation.client.twitter import TWITTER_API_TOKEN

        mock_memcache.get.assert_called_once_with(TWITTER_API_TOKEN)
        self.assertEqual(expected, actual)

    @patch('ripl.core.aggregation.client.twitter.ApiToken')
    @patch('ripl.core.aggregation.client.twitter.memcache')
    def test_from_datastore(self, mock_memcache, mock_api_token):
        """Ensure that the bearer token is returned from the datastore when
        present and force_refresh is False.
        """

        expected = 'foo'
        mock_memcache.get.return_value = None
        mock_api_token.get_by_id.return_value = Mock(bearer_token=expected)

        actual = twitter.get_bearer_token(self.consumer_key,
                                          self.consumer_secret)

        from ripl.core.aggregation.client.twitter import TWITTER_API_TOKEN

        mock_memcache.get.assert_called_once_with(TWITTER_API_TOKEN)
        mock_api_token.get_by_id.assert_called_once_with(TWITTER_API_TOKEN)
        mock_memcache.set.assert_called_once_with(TWITTER_API_TOKEN, expected)
        self.assertEqual(expected, actual)

    @patch('ripl.core.aggregation.client.twitter.Http.request')
    @patch('ripl.core.aggregation.client.twitter.ApiToken')
    @patch('ripl.core.aggregation.client.twitter.memcache')
    def test_exchange_ok(self, mock_memcache, mock_api_token, mock_request):
        """Ensure that the bearer token is fetched from Twitter when not
        already present in memcache or datastore.
        """

        expected = 'foo'
        mock_memcache.get.return_value = None
        mock_api_token.get_by_id.return_value = None
        response = '{"token_type": "bearer", "access_token": "%s"}' % expected
        mock_request.return_value = (Mock(status=200), response)

        actual = twitter.get_bearer_token(self.consumer_key,
                                          self.consumer_secret)

        from ripl.core.aggregation.client.twitter import API
        from ripl.core.aggregation.client.twitter import BEARER_TOKEN_ENDPOINT
        from ripl.core.aggregation.client.twitter import TWITTER_API_TOKEN

        content_type = 'application/x-www-form-urlencoded;charset=UTF-8'
        key = urllib.quote(self.consumer_key)
        secret = urllib.quote(self.consumer_secret)
        credentials = '%s:%s' % (key, secret)
        credentials = base64.b64encode(credentials)

        mock_memcache.get.assert_called_once_with(TWITTER_API_TOKEN)
        mock_api_token.get_by_id.assert_called_once_with(TWITTER_API_TOKEN)
        mock_request.assert_called_once_with(
            '%s%s' % (API, BEARER_TOKEN_ENDPOINT), 'POST',
            body='grant_type=client_credentials',
            headers={'Authorization': 'Basic %s' % credentials,
                     'Content-Type': content_type})
        mock_memcache.set.assert_called_once_with(TWITTER_API_TOKEN, expected)
        mock_api_token.put.assert_called_once()
        self.assertEqual(expected, actual)

    @patch('ripl.core.aggregation.client.twitter.Http.request')
    @patch('ripl.core.aggregation.client.twitter.ApiToken')
    @patch('ripl.core.aggregation.client.twitter.memcache')
    def test_exchange_non_200(self, mock_memcache, mock_api_token,
                              mock_request):
        """Ensure that None is returned when a non-200 response status is
        given by Twitter.
        """

        mock_memcache.get.return_value = None
        mock_api_token.get_by_id.return_value = None
        mock_request.return_value = (Mock(status=500), None)

        actual = twitter.get_bearer_token(self.consumer_key,
                                          self.consumer_secret)

        from ripl.core.aggregation.client.twitter import API
        from ripl.core.aggregation.client.twitter import BEARER_TOKEN_ENDPOINT
        from ripl.core.aggregation.client.twitter import TWITTER_API_TOKEN

        content_type = 'application/x-www-form-urlencoded;charset=UTF-8'
        key = urllib.quote(self.consumer_key)
        secret = urllib.quote(self.consumer_secret)
        credentials = '%s:%s' % (key, secret)
        credentials = base64.b64encode(credentials)

        mock_memcache.get.assert_called_once_with(TWITTER_API_TOKEN)
        mock_api_token.get_by_id.assert_called_once_with(TWITTER_API_TOKEN)
        mock_request.assert_called_once_with(
            '%s%s' % (API, BEARER_TOKEN_ENDPOINT), 'POST',
            body='grant_type=client_credentials',
            headers={'Authorization': 'Basic %s' % credentials,
                     'Content-Type': content_type})
        self.assertFalse(mock_memcache.set.called)
        self.assertFalse(mock_api_token.put.called)
        self.assertEqual(None, actual)

    @patch('ripl.core.aggregation.client.twitter.Http.request')
    @patch('ripl.core.aggregation.client.twitter.ApiToken')
    @patch('ripl.core.aggregation.client.twitter.memcache')
    def test_exchange_bad_response(self, mock_memcache, mock_api_token,
                                   mock_request):
        """Ensure that None is returned when an invalid response is given by
        Twitter.
        """

        mock_memcache.get.return_value = None
        mock_api_token.get_by_id.return_value = None
        response = '{"token_type": "woops"}'
        mock_request.return_value = (Mock(status=200), response)

        actual = twitter.get_bearer_token(self.consumer_key,
                                          self.consumer_secret)

        from ripl.core.aggregation.client.twitter import API
        from ripl.core.aggregation.client.twitter import BEARER_TOKEN_ENDPOINT
        from ripl.core.aggregation.client.twitter import TWITTER_API_TOKEN

        content_type = 'application/x-www-form-urlencoded;charset=UTF-8'
        key = urllib.quote(self.consumer_key)
        secret = urllib.quote(self.consumer_secret)
        credentials = '%s:%s' % (key, secret)
        credentials = base64.b64encode(credentials)

        mock_memcache.get.assert_called_once_with(TWITTER_API_TOKEN)
        mock_api_token.get_by_id.assert_called_once_with(TWITTER_API_TOKEN)
        mock_request.assert_called_once_with(
            '%s%s' % (API, BEARER_TOKEN_ENDPOINT), 'POST',
            body='grant_type=client_credentials',
            headers={'Authorization': 'Basic %s' % credentials,
                     'Content-Type': content_type})
        self.assertFalse(mock_memcache.set.called)
        self.assertFalse(mock_api_token.put.called)
        self.assertEqual(None, actual)

    @patch('ripl.core.aggregation.client.twitter.Http.request')
    @patch('ripl.core.aggregation.client.twitter.ApiToken')
    @patch('ripl.core.aggregation.client.twitter.memcache')
    def test_force_refresh(self, mock_memcache, mock_api_token, mock_request):
        """Ensure that we bypass caching when force_refresh is True."""

        expected = 'foo'
        response = '{"token_type": "bearer", "access_token": "%s"}' % expected
        mock_request.return_value = (Mock(status=200), response)

        actual = twitter.get_bearer_token(self.consumer_key,
                                          self.consumer_secret,
                                          force_refresh=True)

        from ripl.core.aggregation.client.twitter import API
        from ripl.core.aggregation.client.twitter import BEARER_TOKEN_ENDPOINT
        from ripl.core.aggregation.client.twitter import TWITTER_API_TOKEN

        content_type = 'application/x-www-form-urlencoded;charset=UTF-8'
        key = urllib.quote(self.consumer_key)
        secret = urllib.quote(self.consumer_secret)
        credentials = '%s:%s' % (key, secret)
        credentials = base64.b64encode(credentials)

        self.assertFalse(mock_memcache.get.called)
        self.assertFalse(mock_api_token.get_by_id.called)
        mock_request.assert_called_once_with(
            '%s%s' % (API, BEARER_TOKEN_ENDPOINT), 'POST',
            body='grant_type=client_credentials',
            headers={'Authorization': 'Basic %s' % credentials,
                     'Content-Type': content_type})
        mock_memcache.set.assert_called_once_with(TWITTER_API_TOKEN, expected)
        mock_api_token.put.assert_called_once()
        self.assertEqual(expected, actual)


