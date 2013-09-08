import json
import unittest

from mock import Mock
from mock import patch


class TestAggregate(unittest.TestCase):

    @patch(
        'ripl.core.aggregation.aggregator.twitter.get_locations_with_trends')
    @patch('ripl.core.aggregation.aggregator.context')
    def test_happy_path(self, mock_context, mock_get_locations):
        """Ensure we insert fan out tasks for locations in batches."""
        from ripl.core.aggregation.aggregator import aggregate

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
                            "name": "Mexico",
                            "placeType": {
                                "code": 12,
                                "name": "Country"
                            },
                            "url": "http://where.yahooapis.com/v1/place/23424900",
                            "parentid": 1,
                            "country": "Mexico",
                            "woeid": 23424900,
                            "countryCode": "MX"
                        },
                        {
                            "name": "United Kingdom",
                            "placeType": {
                                "code": 12,
                                "name": "Country"
                            },
                            "url": "http://where.yahooapis.com/v1/place/23424975",
                            "parentid": 1,
                            "country": "United Kingdom",
                            "woeid": 23424975,
                            "countryCode": "GB"
                        },
                        {
                            "name": "United States",
                            "placeType": {
                                "code": 12,
                                "name": "Country"
                            },
                            "url": "http://where.yahooapis.com/v1/place/23424977",
                            "parentid": 1,
                            "country": "United States",
                            "woeid": 23424977,
                            "countryCode": "US"
                        },
                        {
                            "name": "United States",
                            "placeType": {
                                "code": 12,
                                "name": "Country"
                            },
                            "url": "http://where.yahooapis.com/v1/place/23424977",
                            "parentid": 1,
                            "country": "United States",
                            "woeid": 23424977,
                            "countryCode": "US"
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


class TestAggregateForLocations(unittest.TestCase):
    # TODO
    pass

