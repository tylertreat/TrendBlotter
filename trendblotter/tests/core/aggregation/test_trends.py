import json
import unittest

from mock import call
from mock import Mock
from mock import patch

from furious.errors import Abort

from trendblotter.core.aggregation import ApiRequestException
from trendblotter.core.aggregation import Location


class TestAggregate(unittest.TestCase):

    @patch(('trendblotter.core.aggregation.trends.twitter.'
            'get_locations_with_trends'))
    @patch('trendblotter.core.aggregation.trends.context')
    def test_happy_path(self, mock_context, mock_get_locations):
        """Ensure we insert fan out tasks for locations in batches."""
        from trendblotter.core.aggregation.trends import aggregate

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

        from trendblotter.core.aggregation.trends import EXCLUDE_TYPES

        mock_get_locations.assert_called_once_with(exclude=EXCLUDE_TYPES)
        mock_context.new.assert_called_once_with()
        self.assertEqual(2, context.add.call_count)


@patch('trendblotter.core.aggregation.trends.ndb.put_multi')
@patch('trendblotter.core.aggregation.trends.twitter.get_trends_by_location')
@patch('trendblotter.core.aggregation.trends._location_dicts_to_entities')
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

    @patch('trendblotter.core.aggregation.trends._aggregate_trend_content')
    def test_happy_path(self, aggregate_content, to_entities, get_trends,
                        put_multi):
        """Ensure we persist Location and Trend entities."""
        from trendblotter.core.aggregation.trends \
            import aggregate_for_locations

        mock_locations = [Mock(woeid=loc['woeid'], name=loc['name'])
                          for loc in self.locations]
        to_entities.return_value = mock_locations
        mock_trends = [Mock(name='%d' % x) for x in xrange(10)]
        get_trends.return_value = mock_trends

        aggregate_for_locations(self.locations)

        to_entities.assert_called_once_with(self.locations)
        expected = [call(loc.name, loc.woeid) for loc in mock_locations]
        self.assertEqual(expected, get_trends.call_args_list)
        expected = [call(mock_locations), call(mock_trends), call(mock_trends),
                    call(mock_trends), call(mock_trends), call(mock_trends)]
        self.assertEqual(expected, put_multi.call_args_list)
        expected = [call(mock_trends, loc) for loc in mock_locations]
        self.assertEqual(expected, aggregate_content.call_args_list)

    def test_abort_on_429(self, to_entities, get_trends, put_multi):
        """Ensure we bail if we get an HTTP 429 status code."""
        from trendblotter.core.aggregation.trends \
            import aggregate_for_locations

        mock_locations = [Mock(woeid=loc['woeid'], name=loc['name'])
                          for loc in self.locations]
        to_entities.return_value = mock_locations

        def mock_get_trends(name, woeid):
            raise ApiRequestException('oh snap', 429)

        get_trends.side_effect = mock_get_trends

        with self.assertRaises(Abort) as ctx:
            aggregate_for_locations(self.locations)

        to_entities.assert_called_once_with(self.locations)
        get_trends.assert_called_once_with(mock_locations[0].name,
                                           mock_locations[0].woeid)
        put_multi.assert_called_once_with(mock_locations)
        self.assertIsInstance(ctx.exception, Abort)


class TestChunk(unittest.TestCase):

    def test_empty_list(self):
        """Ensure an empty list is returned when an empty list is passed."""
        from trendblotter.core.aggregation.trends import chunk

        self.assertEqual([], chunk([], 10).next())

    def test_bad_chunk_size(self):
        """Ensure an empty list is returned when a bad chunk size is passed."""
        from trendblotter.core.aggregation.trends import chunk

        self.assertEqual([], chunk([1, 2, 3, 4, 5], 0).next())

    def test_chunking_equal_groups(self):
        """Ensure the list is chunked properly into equal groups when it can be
        evenly divided.
        """
        from trendblotter.core.aggregation.trends import chunk

        the_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        chunk_size = 3
        full = []

        for group in chunk(the_list, chunk_size):
            self.assertEqual(chunk_size, len(group))
            full.extend(group)

        self.assertEqual(the_list, full)

    def test_chunking_equal_groups_but_one(self):
        """Ensure the list is chunked properly into equal groups except for the
        last when it cannot be evenly divided.
        """
        from trendblotter.core.aggregation.trends import chunk

        the_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        chunk_size = 3
        full = []

        for i, group in enumerate(chunk(the_list, chunk_size)):
            if i == 3:
                self.assertEqual(1, len(group))
            else:
                self.assertEqual(chunk_size, len(group))
            full.extend(group)

        self.assertEqual(the_list, full)


class TestLocationDictsToEntities(unittest.TestCase):

    def test_location_dicts_to_entities(self):
        """Ensure that the list of location dicts is converted to a list of
        location entities.
        """
        from trendblotter.core.aggregation.trends \
            import _location_dicts_to_entities

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

