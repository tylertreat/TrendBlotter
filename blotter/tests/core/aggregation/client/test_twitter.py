import base64
import json
import unittest
import urllib

from mock import Mock
from mock import patch
from mock import PropertyMock

from blotter import settings
from blotter.core.aggregation import ApiRequestException
from blotter.core.aggregation.client import twitter


class TestGetTrendsByLocation(unittest.TestCase):

    @patch('blotter.core.aggregation.client.twitter._make_authorized_get')
    def test_bad_response(self, mock_get):
        """Ensure that an ApiRequestException is raised when a non-200 status
        code is returned from Twitter.
        """

        mock_get.return_value = (Mock(status=500), None)
        location_woeid = 1234
        location_name = 'Canada'

        location = Mock()
        type(location).name = PropertyMock(return_value=location_name)
        type(location).woeid = PropertyMock(return_value=location_woeid)

        with self.assertRaises(ApiRequestException) as ctx:
            twitter.get_trends_by_location(location)

        from blotter.core.aggregation.client.twitter import TRENDS_ENDPOINT

        mock_get.assert_called_once_with(TRENDS_ENDPOINT % location_woeid)
        self.assertIsInstance(ctx.exception, ApiRequestException)

    @patch('blotter.core.aggregation.client.twitter._make_authorized_get')
    def test_happy_path(self, mock_get):
        """Ensure that the correct value is returned on a successful request.
        """

        content = \
            """[
                    {
                        "trends": [
                            {
                                "name": "#ReasonsToLive",
                                "url": "http://twitter.com\
                                        /search?q=%23ReasonsToLive",
                                "promoted_content": null,
                                "query": "%23ReasonsToLive",
                                "events": null
                            },
                            {
                                "name": "#BenjLexieMarjLoveTriangle",
                                "url": "http://twitter.com/search\
                                        ?q=%23BenjLexieMarjLoveTriangle",
                                "promoted_content": null,
                                "query": "%23BenjLexieMarjLoveTriangle",
                                "events": null
                            }
                        ],
                        "as_of": "2013-09-02T07:14:24Z",
                        "created_at": "2013-09-02T06:56:28Z",
                        "locations": [
                            {
                                "name": "Winnipeg",
                                "woeid": 2972
                            }
                        ]
                    }
                ]"""

        mock_get.return_value = (Mock(status=200), content)

        location_woeid = 2972
        location_name = 'Worldwide'

        location = Mock()
        type(location).name = PropertyMock(return_value=location_name)
        type(location).woeid = PropertyMock(return_value=location_woeid)

        actual = twitter.get_trends_by_location(location)

        from blotter.core.aggregation.client.twitter import TRENDS_ENDPOINT

        mock_get.assert_called_once_with(TRENDS_ENDPOINT % location_woeid)
        self.assertEqual(('#BenjLexieMarjLoveTriangle', 1), actual[0])
        self.assertEqual(('#ReasonsToLive', 2), actual[1])


class TestGetLocationsWithTrends(unittest.TestCase):

    @patch('blotter.core.aggregation.client.twitter._make_authorized_get')
    def test_bad_response(self, mock_get):
        """Ensure that an ApiRequestException is raised when a non-200 status
        code is returned from Twitter.
        """

        mock_get.return_value = (Mock(status=500), None)

        with self.assertRaises(ApiRequestException) as ctx:
            twitter.get_locations_with_trends()

        from blotter.core.aggregation.client.twitter \
            import TRENDS_LOCATIONS_ENDPOINT

        mock_get.assert_called_once_with(TRENDS_LOCATIONS_ENDPOINT)
        self.assertIsInstance(ctx.exception, ApiRequestException)

    @patch('blotter.core.aggregation.client.twitter._make_authorized_get')
    def test_happy_path(self, mock_get):
        """Ensure that the correct value is returned on a successful request.
        """

        content = """[
                        {
                            "name": "Worldwide",
                            "placeType": {
                                "code": 19,
                                "name": "Supername"
                            },
                            "url": "http://where.yahooapis.com/v1/place/1",
                            "parentid": 0,
                            "country": "",
                            "woeid": 1,
                            "countryCode": null
                        },
                        {
                            "name": "Winnipeg",
                            "placeType": {
                                "code": 7,
                                "name": "Town"
                            },
                            "url": "http://where.yahooapis.com/v1/place/2972",
                            "parentid": 23424775,
                            "country": "Canada",
                            "woeid": 2972,
                            "countryCode": "CA"
                        }
                    ]"""

        mock_get.return_value = (Mock(status=200), content)

        actual = twitter.get_locations_with_trends()

        from blotter.core.aggregation.client.twitter \
            import TRENDS_LOCATIONS_ENDPOINT

        mock_get.assert_called_once_with(TRENDS_LOCATIONS_ENDPOINT)
        self.assertEqual(json.loads(content), actual)

    @patch('blotter.core.aggregation.client.twitter._make_authorized_get')
    def test_happy_path_with_excludes(self, mock_get):
        """Ensure that the correct value is returned on a successful request
        with excludes.
        """

        content = """[
                        {
                            "name": "Worldwide",
                            "placeType": {
                                "code": 19,
                                "name": "Supername"
                            },
                            "url": "http://where.yahooapis.com/v1/place/1",
                            "parentid": 0,
                            "country": "",
                            "woeid": 1,
                            "countryCode": null
                        },
                        {
                            "name": "Winnipeg",
                            "placeType": {
                                "code": 7,
                                "name": "Town"
                            },
                            "url": "http://where.yahooapis.com/v1/place/2972",
                            "parentid": 23424775,
                            "country": "Canada",
                            "woeid": 2972,
                            "countryCode": "CA"
                        }
                    ]"""

        mock_get.return_value = (Mock(status=200), content)

        actual = twitter.get_locations_with_trends(exclude=[7])

        from blotter.core.aggregation.client.twitter \
            import TRENDS_LOCATIONS_ENDPOINT

        mock_get.assert_called_once_with(TRENDS_LOCATIONS_ENDPOINT)
        self.assertEqual(json.loads(content)[:1], actual)


class TestMakeAuthorizedGet(unittest.TestCase):

    @patch('blotter.core.aggregation.client.twitter._get_bearer_token')
    def test_no_token(self, mock_get_token):
        """Ensure that an ApiRequestException is raised when a bearer token is
        not retrieved.
        """

        mock_get_token.return_value = None

        with self.assertRaises(ApiRequestException) as ctx:
            twitter._make_authorized_get('foo')

        self.assertIsInstance(ctx.exception, ApiRequestException)
        mock_get_token.assert_called_once_with(
            settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)

    @patch('blotter.core.aggregation.client.twitter.Http.request')
    @patch('blotter.core.aggregation.client.twitter._get_bearer_token')
    def test_happy_path(self, mock_get_token, mock_request):
        """Ensure that the correct values are returned when a request is
        successfully made.
        """

        token = 'foo'
        mock_get_token.return_value = token
        endpoint = '/bar'
        expected_response = Mock(status=200)
        expected_content = {'bat': 'man'}
        mock_request.return_value = (expected_response, expected_content)

        resp, content = twitter._make_authorized_get(endpoint)

        headers = {'Authorization': 'Bearer %s' % token}

        from blotter.core.aggregation.client.twitter import API

        mock_get_token.assert_called_once_with(
            settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
        mock_request.assert_called_once_with('%s%s' % (API, endpoint), 'GET',
                                             headers=headers)
        self.assertEqual(resp, expected_response)
        self.assertEqual(content, expected_content)


class TestGetBearerToken(unittest.TestCase):

    @patch('blotter.core.aggregation.client.twitter.memcache')
    def test_from_memcache(self, mock_memcache):
        """Ensure that the bearer token is returned from memcache when present
        and force_refresh is False.
        """

        expected = 'foo'
        mock_memcache.get.return_value = expected

        actual = twitter._get_bearer_token(settings.TWITTER_CONSUMER_KEY,
                                           settings.TWITTER_CONSUMER_SECRET)

        from blotter.core.aggregation.client.twitter import TWITTER_API_TOKEN

        mock_memcache.get.assert_called_once_with(TWITTER_API_TOKEN)
        self.assertEqual(expected, actual)

    @patch('blotter.core.aggregation.client.twitter.ApiToken')
    @patch('blotter.core.aggregation.client.twitter.memcache')
    def test_from_datastore(self, mock_memcache, mock_api_token):
        """Ensure that the bearer token is returned from the datastore when
        present and force_refresh is False.
        """

        expected = 'foo'
        mock_memcache.get.return_value = None
        mock_api_token.get_by_id.return_value = Mock(bearer_token=expected)

        actual = twitter._get_bearer_token(settings.TWITTER_CONSUMER_KEY,
                                           settings.TWITTER_CONSUMER_SECRET)

        from blotter.core.aggregation.client.twitter import TWITTER_API_TOKEN

        mock_memcache.get.assert_called_once_with(TWITTER_API_TOKEN)
        mock_api_token.get_by_id.assert_called_once_with(TWITTER_API_TOKEN)
        mock_memcache.set.assert_called_once_with(TWITTER_API_TOKEN, expected)
        self.assertEqual(expected, actual)

    @patch('blotter.core.aggregation.client.twitter.Http.request')
    @patch('blotter.core.aggregation.client.twitter.ApiToken')
    @patch('blotter.core.aggregation.client.twitter.memcache')
    def test_exchange_ok(self, mock_memcache, mock_api_token, mock_request):
        """Ensure that the bearer token is fetched from Twitter when not
        already present in memcache or datastore.
        """

        expected = 'foo'
        mock_memcache.get.return_value = None
        mock_api_token.get_by_id.return_value = None
        response = '{"token_type": "bearer", "access_token": "%s"}' % expected
        mock_request.return_value = (Mock(status=200), response)

        actual = twitter._get_bearer_token(settings.TWITTER_CONSUMER_KEY,
                                           settings.TWITTER_CONSUMER_SECRET)

        from blotter.core.aggregation.client.twitter import API
        from blotter.core.aggregation.client.twitter \
            import BEARER_TOKEN_ENDPOINT
        from blotter.core.aggregation.client.twitter import TWITTER_API_TOKEN

        content_type = 'application/x-www-form-urlencoded;charset=UTF-8'
        key = urllib.quote(settings.TWITTER_CONSUMER_KEY)
        secret = urllib.quote(settings.TWITTER_CONSUMER_SECRET)
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

    @patch('blotter.core.aggregation.client.twitter.Http.request')
    @patch('blotter.core.aggregation.client.twitter.ApiToken')
    @patch('blotter.core.aggregation.client.twitter.memcache')
    def test_exchange_non_200(self, mock_memcache, mock_api_token,
                              mock_request):
        """Ensure that None is returned when a non-200 response status is
        given by Twitter.
        """

        mock_memcache.get.return_value = None
        mock_api_token.get_by_id.return_value = None
        mock_request.return_value = (Mock(status=500), None)

        actual = twitter._get_bearer_token(settings.TWITTER_CONSUMER_KEY,
                                           settings.TWITTER_CONSUMER_SECRET)

        from blotter.core.aggregation.client.twitter import API
        from blotter.core.aggregation.client.twitter \
            import BEARER_TOKEN_ENDPOINT
        from blotter.core.aggregation.client.twitter import TWITTER_API_TOKEN

        content_type = 'application/x-www-form-urlencoded;charset=UTF-8'
        key = urllib.quote(settings.TWITTER_CONSUMER_KEY)
        secret = urllib.quote(settings.TWITTER_CONSUMER_SECRET)
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

    @patch('blotter.core.aggregation.client.twitter.Http.request')
    @patch('blotter.core.aggregation.client.twitter.ApiToken')
    @patch('blotter.core.aggregation.client.twitter.memcache')
    def test_exchange_bad_response(self, mock_memcache, mock_api_token,
                                   mock_request):
        """Ensure that None is returned when an invalid response is given by
        Twitter.
        """

        mock_memcache.get.return_value = None
        mock_api_token.get_by_id.return_value = None
        response = '{"token_type": "woops"}'
        mock_request.return_value = (Mock(status=200), response)

        actual = twitter._get_bearer_token(settings.TWITTER_CONSUMER_KEY,
                                           settings.TWITTER_CONSUMER_SECRET)

        from blotter.core.aggregation.client.twitter import API
        from blotter.core.aggregation.client.twitter \
            import BEARER_TOKEN_ENDPOINT
        from blotter.core.aggregation.client.twitter import TWITTER_API_TOKEN

        content_type = 'application/x-www-form-urlencoded;charset=UTF-8'
        key = urllib.quote(settings.TWITTER_CONSUMER_KEY)
        secret = urllib.quote(settings.TWITTER_CONSUMER_SECRET)
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

    @patch('blotter.core.aggregation.client.twitter.Http.request')
    @patch('blotter.core.aggregation.client.twitter.ApiToken')
    @patch('blotter.core.aggregation.client.twitter.memcache')
    def test_force_refresh(self, mock_memcache, mock_api_token, mock_request):
        """Ensure that we bypass caching when force_refresh is True."""

        expected = 'foo'
        response = '{"token_type": "bearer", "access_token": "%s"}' % expected
        mock_request.return_value = (Mock(status=200), response)

        actual = twitter._get_bearer_token(settings.TWITTER_CONSUMER_KEY,
                                           settings.TWITTER_CONSUMER_SECRET,
                                           force_refresh=True)

        from blotter.core.aggregation.client.twitter import API
        from blotter.core.aggregation.client.twitter \
            import BEARER_TOKEN_ENDPOINT
        from blotter.core.aggregation.client.twitter import TWITTER_API_TOKEN

        content_type = 'application/x-www-form-urlencoded;charset=UTF-8'
        key = urllib.quote(settings.TWITTER_CONSUMER_KEY)
        secret = urllib.quote(settings.TWITTER_CONSUMER_SECRET)
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

