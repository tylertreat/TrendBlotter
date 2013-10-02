import time
import unittest

from mock import call
from mock import patch

from blotter.core.aggregation import content


@patch('blotter.core.aggregation.content.memcache')
class TestAggregateContent(unittest.TestCase):

    def setUp(self):
        self.old_sources = content.SOURCES
        content.SOURCES = {
            'CNN': {
                'feeds': {
                    'Top Stories': 'http://rss.cnn.com/rss/cnn_topstories.rss',
                    'World': 'http://rss.cnn.com/rss/cnn_world.rss',
                },
                'options': {
                    'use_og': True
                }
            }
        }

    def tearDown(self):
        content.SOURCES = self.old_sources

    @patch('blotter.core.aggregation.content._add_content_to_trend')
    @patch('blotter.core.aggregation.content._find_content_image_url')
    @patch('blotter.core.aggregation.content._calculate_score')
    def test_from_cache(self, mock_calc_score, mock_find_image,
                        mock_add_content, mock_memcache):
        """Verify aggregate_content crawls the RSS feeds from memcache for each
        data source when available, retrieves relevant, and updates the Trend
        entity.
        """

        mock_entries = [{'link': 'foo'}, {'link': 'bar'}]
        mock_memcache.get.return_value = mock_entries
        mock_calc_score.side_effect = [10, 5, 0, 0]
        mock_find_image.return_value = 'image.jpg'

        trend = 'trend'
        location = 'United States'
        timestamp = time.time()

        content.aggregate_content(trend, location, timestamp)

        expected = [call('CNN-Top Stories'), call('CNN-World')]
        self.assertEqual(expected, mock_memcache.get.call_args_list)

        expected = 2 * [call(trend, mock_entries[0]),
                        call(trend, mock_entries[1])]
        self.assertEqual(expected, mock_calc_score.call_args_list)

        expected = [call(mock_entries[0]['link'], use_og=True),
                    call(mock_entries[1]['link'], use_og=True)]
        self.assertEqual(expected, mock_find_image.call_args_list)

        mock_add_content.assert_called_once_with(
            '%s-%s-%s' % (trend, location, timestamp),
            [
                {
                    'link': 'foo',
                    'source': 'CNN',
                    'score': 10,
                    'image': 'image.jpg'
                },
                {
                    'link': 'bar',
                    'source': 'CNN',
                    'score': 5,
                    'image': 'image.jpg'
                }
            ])

    @patch('blotter.core.aggregation.content._add_content_to_trend')
    @patch('blotter.core.aggregation.content._find_content_image_url')
    @patch('blotter.core.aggregation.content._calculate_score')
    @patch('blotter.core.aggregation.content.feedparser.parse')
    def test_no_cache(self, mock_parse, mock_calc_score, mock_find_image,
                      mock_add_content, mock_memcache):
        """Verify aggregate_content crawls the RSS feeds for each data source
        retrieves relevant, and updates the Trend entity. When a feed is
        fetched, its entries are cached for 3600 seconds.
        """

        mock_entries = [{'link': 'foo'}, {'link': 'bar'}]
        mock_memcache.get.return_value = None
        mock_parse.return_value = {'entries': mock_entries}
        mock_calc_score.side_effect = [10, 5, 0, 0]
        mock_find_image.return_value = 'image.jpg'

        trend = 'trend'
        location = 'United States'
        timestamp = time.time()

        content.aggregate_content(trend, location, timestamp)

        expected = [call('CNN-Top Stories'), call('CNN-World')]
        self.assertEqual(expected, mock_memcache.get.call_args_list)

        expected = [call('http://rss.cnn.com/rss/cnn_topstories.rss'),
                    call('http://rss.cnn.com/rss/cnn_world.rss')]
        self.assertEqual(expected, mock_parse.call_args_list)

        expected = [call('CNN-Top Stories', mock_entries, time=3600),
                    call('CNN-World', mock_entries, time=3600)]
        self.assertEqual(expected, mock_memcache.set.call_args_list)

        expected = 2 * [call(trend, mock_entries[0]),
                        call(trend, mock_entries[1])]
        self.assertEqual(expected, mock_calc_score.call_args_list)

        expected = [call(mock_entries[0]['link'], use_og=True),
                    call(mock_entries[1]['link'], use_og=True)]
        self.assertEqual(expected, mock_find_image.call_args_list)

        mock_add_content.assert_called_once_with(
            '%s-%s-%s' % (trend, location, timestamp),
            [
                {
                    'link': 'foo',
                    'source': 'CNN',
                    'score': 10,
                    'image': 'image.jpg'
                },
                {
                    'link': 'bar',
                    'source': 'CNN',
                    'score': 5,
                    'image': 'image.jpg'
                }
            ])

    @patch('blotter.core.aggregation.content._add_content_to_trend')
    @patch('blotter.core.aggregation.content._find_content_image_url')
    @patch('blotter.core.aggregation.content._calculate_score')
    def test_query_from_cache(self, mock_calc_score, mock_find_image,
                              mock_add_content, mock_memcache):
        """Verify aggregate_content properly handles query data sources."""

        content.SOURCES = {
            'QUERY': {
                'feeds': {
                    'Google News':
                    'https://news.google.com/news/feeds?q=%s&geo=%s&output=rss'
                },
                'options': {
                    'use_og': True
                }
            }
        }

        mock_entries = [{'link': 'foo', 'title': 'Cool Story Bro - CNN'},
                        {'link': 'bar', 'title': 'Bro Cool Story - BBC'}]
        mock_memcache.get.return_value = mock_entries
        mock_calc_score.side_effect = [10, 5]
        mock_find_image.side_effect = ['image.jpg', None]

        trend = 'trend'
        location = 'Canada'
        timestamp = time.time()

        content.aggregate_content(trend, location, timestamp)

        mock_memcache.get.assert_called_once_with(
            'QUERY-Google News-%s-%s' % (trend, location))

        expected = [call(trend, mock_entries[0]), call(trend, mock_entries[1])]
        self.assertEqual(expected, mock_calc_score.call_args_list)

        expected = [call(mock_entries[0]['link'], use_og=True),
                    call(mock_entries[1]['link'], use_og=True)]
        self.assertEqual(expected, mock_find_image.call_args_list)

        mock_add_content.assert_called_once_with(
            '%s-%s-%s' % (trend, location, timestamp),
            [
                {
                    'link': 'foo',
                    'source': 'CNN',
                    'score': 10,
                    'image': 'image.jpg'
                }
            ])

