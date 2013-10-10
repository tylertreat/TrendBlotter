import time
import unittest

from mock import call
from mock import Mock
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
    @patch('blotter.core.aggregation.content._copy_image_to_gcs')
    @patch('blotter.core.aggregation.content.hashlib.sha1')
    @patch('blotter.core.aggregation.content._find_content_image_url')
    @patch('blotter.core.aggregation.content._calculate_score')
    def test_from_cache(self, mock_calc_score, mock_find_image,
                        mock_sha1, mock_copy_image, mock_add_content,
                        mock_memcache):
        """Verify aggregate_content crawls the RSS feeds from memcache for each
        data source when available, retrieves relevant, and updates the Trend
        entity.
        """

        mock_entries = [{'link': 'foo'}, {'link': 'bar'}]
        mock_memcache.get.return_value = mock_entries
        mock_calc_score.side_effect = [10, 5, 0, 0]
        image_hash = 'hash'
        mock_sha1.return_value.hexdigest.return_value = image_hash
        mock_copy_image.return_value = 'imagekey'
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
                    'image_key': image_hash
                },
                {
                    'link': 'bar',
                    'source': 'CNN',
                    'score': 5,
                    'image_key': image_hash
                }
            ])

    @patch('blotter.core.aggregation.content._add_content_to_trend')
    @patch('blotter.core.aggregation.content._copy_image_to_gcs')
    @patch('blotter.core.aggregation.content.hashlib.sha1')
    @patch('blotter.core.aggregation.content._find_content_image_url')
    @patch('blotter.core.aggregation.content._calculate_score')
    @patch('blotter.core.aggregation.content.feedparser.parse')
    def test_no_cache(self, mock_parse, mock_calc_score, mock_find_image,
                      mock_sha1, mock_copy_image, mock_add_content,
                      mock_memcache):
        """Verify aggregate_content crawls the RSS feeds for each data source
        retrieves relevant, and updates the Trend entity. When a feed is
        fetched, its entries are cached for 3600 seconds.
        """

        mock_entries = [{'link': 'foo'}, {'link': 'bar'}]
        mock_memcache.get.return_value = None
        mock_parse.return_value = {'entries': mock_entries}
        mock_calc_score.side_effect = [10, 5, 0, 0]
        image_hash = 'hash'
        mock_sha1.return_value.hexdigest.return_value = image_hash
        mock_copy_image.return_value = 'imagekey'
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
                    'image_key': image_hash
                },
                {
                    'link': 'bar',
                    'source': 'CNN',
                    'score': 5,
                    'image_key': image_hash
                }
            ])

    @patch('blotter.core.aggregation.content._add_content_to_trend')
    @patch('blotter.core.aggregation.content._copy_image_to_gcs')
    @patch('blotter.core.aggregation.content.hashlib.sha1')
    @patch('blotter.core.aggregation.content._find_content_image_url')
    @patch('blotter.core.aggregation.content._calculate_score')
    def test_query_from_cache(self, mock_calc_score, mock_find_image,
                              mock_sha1, mock_copy_image, mock_add_content,
                              mock_memcache):
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
        image_hash = 'hash'
        mock_sha1.return_value.hexdigest.return_value = image_hash
        mock_copy_image.return_value = 'imagekey'

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
                    'image_key': image_hash
                }
            ])


@patch('blotter.core.aggregation.content.Trend')
class TestAddContentToTrend(unittest.TestCase):

    def test_no_content(self, mock_trend):
        """Verify _add_content_to_trend does nothing when no content is passed
        in.
        """

        content._add_content_to_trend(42, None)

        self.assertFalse(mock_trend.get_by_id.called)

    def test_add_content(self, mock_trend):
        """Verify the content passed in to _add_content_to_trend is added to
        the Trend.
        """

        trend_id = 42
        mock_content = [{'link': 'foo', 'source': 'CNN', 'image': 'image.jpg'}]
        mock_trend_entity = Mock(name='foo', rating=10)
        mock_trend.get_by_id.return_value = mock_trend_entity

        content._add_content_to_trend(trend_id, mock_content)

        mock_trend_entity.put.assert_called_once_with()


class TestCalculateScore(unittest.TestCase):

    def test_calculate_score(self):
        """Verify _calculate_score correctly calculates trend scores."""

        trend = 'foo'
        entry = {'title': 'This is a Story About Foo, Not Foobar',
                 'summary': 'Foo bar baz buz qux barfoo foobar.'}

        actual = content._calculate_score(trend, entry)

        self.assertEqual(2, actual)


@patch('blotter.core.aggregation.content.request')
@patch('blotter.core.aggregation.content.ImageFile.Parser')
class TestGetImageSize(unittest.TestCase):

    def test_get_image_size(self, mock_parser, mock_request):
        """Verify _get_image_size correctly retrieves the image dimensions."""

        mock_data = Mock()
        mock_request.return_value.read.return_value = mock_data
        expected = (500, 500)
        mock_parser.return_value = Mock(image=Mock(size=expected))
        uri = 'http://foo.com/image.jpg'

        actual = content._get_image_size(uri)

        self.assertEqual(expected, actual)
        mock_request.assert_called_once_with(uri)
        mock_parser.assert_called_once_with()
        mock_parser.return_value.feed.assert_called_once_with(mock_data)

    def test_no_data(self, mock_parser, mock_request):
        """Verify _get_image_size returns None when no data is received."""

        mock_request.return_value.read.return_value = None
        mock_parser.return_value = Mock()
        uri = 'http://foo.com/image.jpg'

        actual = content._get_image_size(uri)

        self.assertEqual(None, actual)
        mock_request.assert_called_once_with(uri)
        mock_parser.assert_called_once_with()

    def test_error(self, mock_parser, mock_request):
        """Verify _get_image_size returns None when a URLError is raised."""
        from urllib2 import URLError

        def side_effect(uri):
            raise URLError('Oh snap')

        mock_request.side_effect = side_effect
        mock_parser.return_value = Mock()
        uri = 'http://foo.com/image.jpg'

        actual = content._get_image_size(uri)

        self.assertEqual(None, actual)
        mock_request.assert_called_once_with(uri)
        self.assertFalse(mock_parser.called)


@patch('blotter.core.aggregation.content.request')
class TestFindContentImageUrl(unittest.TestCase):

    def test_bail_on_bad_response(self, mock_request):
        """Verify _find_content_image_url returns None on bad responses."""

        mock_request.return_value = Mock(
            headers={'Content-Type': 'application/json'})

        url = 'http://foo.com'

        actual = content._find_content_image_url(url)

        self.assertEqual(None, actual)
        mock_request.assert_called_once_with(url)

    @patch('blotter.core.aggregation.content.BeautifulSoup')
    def test_use_og_image(self, mock_soup, mock_request):
        """Verify _find_content_image_url returns the og:image URL when enabled
        and present on the page.
        """

        mock_response = Mock(headers={'Content-Type': 'text/html'})
        mock_response.read.return_value = Mock()

        mock_request.return_value = mock_response
        expected = 'http://foo.com/image.jpg'

        mock_soup.return_value.find.return_value = {'content': expected}

        url = 'http://foo.com'

        actual = content._find_content_image_url(url)

        self.assertEqual(expected, actual)
        mock_request.assert_called_once_with(url)
        mock_soup.assert_called_once_with(mock_response.read.return_value,
                                          'lxml')
        mock_soup.return_value.find.assert_called_once_with(
            'meta', property='og:image')

    @patch('blotter.core.aggregation.content.BeautifulSoup')
    def test_use_thumbnail_spec(self, mock_soup, mock_request):
        """Verify _find_content_image_url returns the image_src URL when
        present on the page.
        """

        mock_response = Mock(headers={'Content-Type': 'text/html'})
        mock_response.read.return_value = Mock()

        mock_request.return_value = mock_response
        expected = 'http://foo.com/image.jpg'

        mock_soup.return_value.find.return_value = {'href': expected}

        url = 'http://foo.com'

        actual = content._find_content_image_url(url, use_og=False)

        self.assertEqual(expected, actual)
        mock_request.assert_called_once_with(url)
        mock_soup.assert_called_once_with(mock_response.read.return_value,
                                          'lxml')
        mock_soup.return_value.find.assert_called_once_with(
            'link', rel='image_src')

    @patch('blotter.core.aggregation.content._get_image_size')
    @patch('blotter.core.aggregation.content._get_image_urls')
    @patch('blotter.core.aggregation.content.BeautifulSoup')
    def test_find_largest_image(self, mock_soup, mock_get_images,
                                mock_get_size, mock_request):
        """Verify _find_content_image_url returns the largest image URL if all
        else fails.
        """

        mock_response = Mock(headers={'Content-Type': 'text/html'})
        mock_response.read.return_value = Mock()

        mock_request.return_value = mock_response

        mock_soup.return_value.find.return_value = None
        mock_get_images.return_value = ['http://foo.com/image1.jpg',
                                        'http://foo.com/image2.jpg',
                                        'http://foo.com/image3.jpg',
                                        'http://foo.com/image4.jpg'
                                        'http://foo.com/sprite.jpg']

        mock_get_size.side_effect = [None, (10, 10), (500, 500),
                                     (10000, 100), (510, 500)]

        url = 'http://foo.com'

        actual = content._find_content_image_url(url, use_og=False)

        self.assertEqual(mock_get_images.return_value[2], actual)
        mock_request.assert_called_once_with(url)
        mock_soup.assert_called_once_with(mock_response.read.return_value,
                                          'lxml')
        mock_get_images.assert_called_once_with(url, mock_soup.return_value)

        expected = [call(image_url)
                    for image_url in mock_get_images.return_value]
        self.assertEqual(expected, mock_get_size.call_args_list)


class TestGetImageUrls(unittest.TestCase):

    def test_no_url(self):
        """Verify _get_image_urls yields nothing if None is passed in as a URL.
        """

        for image_url in content._get_image_urls(None, Mock()):
            self.assertTrue(False)

    def test_get_urls(self):
        """Verify _get_image_urls correctly returns the image URLs."""

        url = 'http://foo.com'
        soup = Mock()
        soup.find_all.return_value = [{'src': '/image%d' % x}
                                      for x in range(3)]

        for i, image_url in enumerate(content._get_image_urls(url, soup)):
            self.assertEqual('%s/image%d' % (url, i), image_url)

        soup.find_all.assert_called_once_with('img', src=True)

