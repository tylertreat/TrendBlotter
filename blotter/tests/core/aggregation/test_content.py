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
    def test_happy_path_from_cache(self, mock_calc_score, mock_find_image,
                                   mock_add_content, mock_memcache):
        """Verify aggregate_content crawls the RSS feeds from memcache for each
        data source, retrieves relevant, and updates the Trend entity.
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

