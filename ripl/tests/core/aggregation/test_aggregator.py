import json
import unittest

from mock import call
from mock import Mock
from mock import patch

from furious.errors import Abort

from ripl.core.aggregation import ApiRequestException


class TestAggregate(unittest.TestCase):

    @patch(
        'ripl.core.aggregation.aggregator.twitter.get_locations_with_trends')
    @patch('ripl.core.aggregation.aggregator.context')
    def test_happy_path(self, mock_context, mock_get_locations):
        """Ensure we insert fan out tasks for locations in batches."""
        from ripl.core.aggregation.aggregator import aggregate

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
                            "url": "http://where.yahooapis.com/v1/place/23424900",
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
                            "url": "http://where.yahooapis.com/v1/place/23424975",
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
                            "url": "http://where.yahooapis.com/v1/place/23424977",
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
                            "url": "http://where.yahooapis.com/v1/place/23424977",
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

        from ripl.core.aggregation.aggregator import EXCLUDE_TYPES

        mock_get_locations.assert_called_once_with(exclude=EXCLUDE_TYPES)
        mock_context.new.assert_called_once_with()
        self.assertEqual(2, context.add.call_count)


@patch('ripl.core.aggregation.aggregator.ndb.put_multi')
@patch('ripl.core.aggregation.aggregator.twitter.get_trends_by_location')
@patch('ripl.core.aggregation.aggregator._location_dicts_to_entities')
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
                            "url": "http://where.yahooapis.com/v1/place/23424900",
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
                            "url": "http://where.yahooapis.com/v1/place/23424975",
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
                            "url": "http://where.yahooapis.com/v1/place/23424977",
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
                            "url": "http://where.yahooapis.com/v1/place/23424977",
                            "parentid": 1,
                            "country": "united states",
                            "woeid": 23424977,
                            "countrycode": "us"
                        }
                    ]"""

        self.locations = json.loads(locations)

    def test_happy_path(self, to_entities, get_trends, put_multi):
        """Ensure we persist Location and Trend entities."""
        from ripl.core.aggregation.aggregator import aggregate_for_locations

        mock_locations = [Mock(woeid=loc['woeid'], name=loc['name'])
                          for loc in self.locations]
        to_entities.return_value = mock_locations
        mock_trends = [Mock(name='%d' % x) for x in xrange(10)]
        get_trends.return_value = mock_trends

        aggregate_for_locations(self.locations)

        to_entities.assert_called_once_with(self.locations)
        expected = [call(loc.woeid) for loc in mock_locations]
        self.assertEqual(expected, get_trends.call_args_list)
        expected = [call(mock_locations), call(mock_trends), call(mock_trends),
                    call(mock_trends), call(mock_trends), call(mock_trends)]
        self.assertEqual(expected, put_multi.call_args_list)

    def test_abort_on_429(self, to_entities, get_trends, put_multi):
        """Ensure we bail if we get an HTTP 429 status code."""
        from ripl.core.aggregation.aggregator import aggregate_for_locations

        mock_locations = [Mock(woeid=loc['woeid'], name=loc['name'])
                          for loc in self.locations]
        to_entities.return_value = mock_locations

        def mock_get_trends(woeid):
            raise ApiRequestException('oh snap', 429)

        get_trends.side_effect = mock_get_trends

        with self.assertRaises(Abort) as ctx:
            aggregate_for_locations(self.locations)

        to_entities.assert_called_once_with(self.locations)
        get_trends.assert_called_once_with(mock_locations[0].woeid)
        put_multi.assert_called_once_with(mock_locations)
        self.assertIsInstance(ctx.exception, Abort)

