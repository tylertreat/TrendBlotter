import json
import unittest

from mock import call
from mock import Mock
from mock import patch
from mock import PropertyMock

from furious.errors import Abort

from blotter.core.aggregation import ApiRequestException
from blotter.core.aggregation import Location


class TestAggregate(unittest.TestCase):

    @patch('blotter.core.aggregation.trends.twitter.get_locations_with_trends')
    @patch('blotter.core.aggregation.trends.context')
    def test_happy_path(self, mock_context, mock_get_locations):
        """Ensure we insert fan out tasks for locations in batches."""
        from blotter.core.aggregation.trends import aggregate

        content = """[
                        {
                            "name": "worldwide",
                            "placetype": {
                                "code": 19,
                                "name": "supername"
                            },
                            "url": "http://where.yahooapis.com/v1/place/1",
                            "parentid": 0,
                            "country": "",
                            "woeid": 1,
                            "countrycode": null
                        },
                        {
                            "name": "mexico",
                            "placetype": {
                                "code": 12,
                                "name": "country"
                            },
                            "url": \
                                "http://where.yahooapis.com/v1/place/23424900",
                            "parentid": 1,
                            "country": "mexico",
                            "woeid": 23424900,
                            "countrycode": "mx"
                        },
                        {
                            "name": "united kingdom",
                            "placetype": {
                                "code": 12,
                                "name": "country"
                            },
                            "url": \
                                "http://where.yahooapis.com/v1/place/23424975",
                            "parentid": 1,
                            "country": "united kingdom",
                            "woeid": 23424975,
                            "countrycode": "gb"
                        },
                        {
                            "name": "united states",
                            "placetype": {
                                "code": 12,
                                "name": "country"
                            },
                            "url": \
                                "http://where.yahooapis.com/v1/place/23424977",
                            "parentid": 1,
                            "country": "united states",
                            "woeid": 23424977,
                            "countrycode": "us"
                        },
                        {
                            "name": "united states",
                            "placetype": {
                                "code": 12,
                                "name": "country"
                            },
                            "url": \
                                "http://where.yahooapis.com/v1/place/23424977",
                            "parentid": 1,
                            "country": "united states",
                            "woeid": 23424977,
                            "countrycode": "us"
                        }
                    ]"""

        mock_get_locations.return_value = json.loads(content) * 6
        context = Mock()
        context.insert_success = 2
        mock_context.new.return_value.__enter__.return_value = context

        aggregate()

        from blotter.core.aggregation.trends import EXCLUDE_TYPES

        mock_get_locations.assert_called_once_with(exclude=EXCLUDE_TYPES)
        mock_context.new.assert_called_once_with()
        self.assertEqual(2, context.add.call_count)


@patch('blotter.core.aggregation.trends.ndb.put_multi')
@patch('blotter.core.aggregation.trends._get_trends_by_location')
@patch('blotter.core.aggregation.trends._location_dicts_to_entities')
class TestAggregateForLocations(unittest.TestCase):

    def setUp(self):
        locations = """[
                        {
                            "name": "worldwide",
                            "placetype": {
                                "code": 19,
                                "name": "supername"
                            },
                            "url": "http://where.yahooapis.com/v1/place/1",
                            "parentid": 0,
                            "country": "",
                            "woeid": 1,
                            "countrycode": null
                        },
                        {
                            "name": "mexico",
                            "placetype": {
                                "code": 12,
                                "name": "country"
                            },
                            "url": \
                                "http://where.yahooapis.com/v1/place/23424900",
                            "parentid": 1,
                            "country": "mexico",
                            "woeid": 23424900,
                            "countrycode": "mx"
                        },
                        {
                            "name": "united kingdom",
                            "placetype": {
                                "code": 12,
                                "name": "country"
                            },
                            "url": \
                                "http://where.yahooapis.com/v1/place/23424975",
                            "parentid": 1,
                            "country": "united kingdom",
                            "woeid": 23424975,
                            "countrycode": "gb"
                        },
                        {
                            "name": "united states",
                            "placetype": {
                                "code": 12,
                                "name": "country"
                            },
                            "url": \
                                "http://where.yahooapis.com/v1/place/23424977",
                            "parentid": 1,
                            "country": "united states",
                            "woeid": 23424977,
                            "countrycode": "us"
                        },
                        {
                            "name": "united states",
                            "placetype": {
                                "code": 12,
                                "name": "country"
                            },
                            "url": \
                                "http://where.yahooapis.com/v1/place/23424977",
                            "parentid": 1,
                            "country": "united states",
                            "woeid": 23424977,
                            "countrycode": "us"
                        }
                    ]"""

        self.locations = json.loads(locations)

    @patch('blotter.core.aggregation.trends._aggregate_trend_content')
    def test_happy_path(self, aggregate_content, to_entities, get_trends,
                        put_multi):
        """Ensure we persist Location and Trend entities."""
        from blotter.core.aggregation.trends import aggregate_for_locations

        mock_locations = [Mock(woeid=loc['woeid'], name=loc['name'])
                          for loc in self.locations]
        to_entities.return_value = mock_locations
        mock_trends = [Mock(name='%d' % x) for x in xrange(10)]
        get_trends.return_value = mock_trends

        aggregate_for_locations(self.locations)

        to_entities.assert_called_once_with(self.locations)
        expected = [call(location) for location in mock_locations]
        self.assertEqual(expected, get_trends.call_args_list)
        expected = [call(mock_locations), call(mock_trends), call(mock_trends),
                    call(mock_trends), call(mock_trends), call(mock_trends)]
        self.assertEqual(expected, put_multi.call_args_list)
        expected = [call(mock_trends, loc) for loc in mock_locations]
        self.assertEqual(expected, aggregate_content.call_args_list)

    def test_abort_on_429(self, to_entities, get_trends, put_multi):
        """Ensure we bail if we get an HTTP 429 status code."""
        from blotter.core.aggregation.trends import aggregate_for_locations

        mock_locations = [Mock(woeid=loc['woeid'], name=loc['name'])
                          for loc in self.locations]
        to_entities.return_value = mock_locations

        def mock_get_trends(location):
            raise ApiRequestException('oh snap', 429)

        get_trends.side_effect = mock_get_trends

        with self.assertRaises(Abort) as ctx:
            aggregate_for_locations(self.locations)

        to_entities.assert_called_once_with(self.locations)
        get_trends.assert_called_once_with(mock_locations[0])
        put_multi.assert_called_once_with(mock_locations)
        self.assertIsInstance(ctx.exception, Abort)


class TestLocationDictsToEntities(unittest.TestCase):

    def test_location_dicts_to_entities(self):
        """Ensure that the list of location dicts is converted to a list of
        location entities.
        """
        from blotter.core.aggregation.trends import _location_dicts_to_entities

        locations = """[
                        {
                            "name": "worldwide",
                            "placeType": {
                                "code": 19,
                                "name": "supername"
                            },
                            "url": "http://where.yahooapis.com/v1/place/1",
                            "parentid": 0,
                            "country": "",
                            "woeid": 1,
                            "countryCode": null
                        },
                        {
                            "name": "mexico",
                            "placeType": {
                                "code": 12,
                                "name": "country"
                            },
                            "url": \
                                "http://where.yahooapis.com/v1/place/23424900",
                            "parentid": 1,
                            "country": "mexico",
                            "woeid": 23424900,
                            "countryCode": "mx"
                        }
                    ]"""

        locations = json.loads(locations)

        actual = _location_dicts_to_entities(locations)

        self.assertIsInstance(actual[0], Location)
        self.assertEqual('worldwide', actual[0].name)
        self.assertEqual(19, actual[0].type_code)
        self.assertEqual('supername', actual[0].type_name)
        self.assertEqual(0, actual[0].parent_id)
        self.assertEqual('', actual[0].country)
        self.assertEqual(None, actual[0].country_code)
        self.assertEqual(1, actual[0].woeid)

        self.assertIsInstance(actual[1], Location)
        self.assertEqual('mexico', actual[1].name)
        self.assertEqual(12, actual[1].type_code)
        self.assertEqual('country', actual[1].type_name)
        self.assertEqual(1, actual[1].parent_id)
        self.assertEqual('mexico', actual[1].country)
        self.assertEqual('mx', actual[1].country_code)
        self.assertEqual(23424900, actual[1].woeid)


@patch('blotter.core.aggregation.trends.get_previous_trend_rating')
@patch('blotter.core.aggregation.trends.gplus.get_trends_by_location')
@patch('blotter.core.aggregation.trends.twitter.get_trends_by_location')
class TestGetTrendsByLocation(unittest.TestCase):

    def test_happy_path(self, mock_twitter, mock_gplus, mock_previous_rating):
        """Verify _get_trends_by_location fetches trends from all sources and
        then reduces the results.
        """
        from blotter.core.aggregation.trends import _get_trends_by_location

        mock_twitter.return_value = [('foo', 1), ('bar', 2), ('baz', 3)]
        mock_gplus.return_value = [('foo', 3), ('bar', 1), ('baz', 6),
                                   ('qux', 2)]
        mock_previous_rating.return_value = None

        location = Mock()
        type(location).name = PropertyMock(return_value='Worldwide')

        actual = _get_trends_by_location(location)

        mock_twitter.assert_called_once_with(location)
        mock_gplus.assert_called_once_with(location)
        self.assertEqual(4, mock_previous_rating.call_count)
        self.assertEqual(4, len(actual))
        self.assertEqual('baz', actual[0].name)
        self.assertEqual(4.5, actual[0].rating)
        self.assertEqual('Worldwide', actual[0].location.id())
        self.assertEqual('foo', actual[1].name)
        self.assertEqual(2.0, actual[1].rating)
        self.assertEqual('Worldwide', actual[1].location.id())
        self.assertEqual('bar', actual[2].name)
        self.assertEqual(1.5, actual[2].rating)
        self.assertEqual('Worldwide', actual[2].location.id())
        self.assertEqual('qux', actual[3].name)
        self.assertEqual(2.0, actual[3].rating)
        self.assertEqual('Worldwide', actual[3].location.id())

