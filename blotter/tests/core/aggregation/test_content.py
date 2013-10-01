import time
import unittest

from mock import call
from mock import patch

from blotter.core.aggregation import content


@patch('blotter.core.aggregation.content._get_sources')
@patch('blotter.core.aggregation.content.memcache')
class TestAggregateContent(unittest.TestCase):

    def setUp(self):
        self.old_sources = content.SOURCES
        content.SOURCES = \
            {'CNN': {
                'Top Stories': 'http://rss.cnn.com/rss/cnn_topstories.rss',
                'World': 'http://rss.cnn.com/rss/cnn_world.rss'}
             }

    def tearDown(self):
        content.SOURCES = self.old_sources

    @patch('blotter.core.aggregation.content._add_content_to_trend')
    @patch('blotter.core.aggregation.content._find_content_image_url')
    @patch('blotter.core.aggregation.content._calculate_score')
    def test_happy_path_from_cache(self, mock_calc_score, mock_find_image,
                                   mock_add_content, mock_memcache):
        """Verify aggregate_content crawls the RSS feeds from memcache for each
        data source, retrieves relevant, and updates the Trend entity.
        """

        mock_memcache.get.return_value = [{'link': 'foo'}, {'link': 'bar'}]
        mock_calc_score.side_effect = [10, 0]
        mock_find_image.return_value = 'image.jpg'

        trend = 'trend'
        location = 'United States'
        timestamp = time.time()

        content.aggregate_content(trend, location, timestamp)

        expected = [call('CNN-Top Stories'), call('CNN-World')]
        self.assertEqual(expected, mock_memcache.call_args_list)
