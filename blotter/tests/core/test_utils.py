import unittest

from mock import Mock
from mock import patch

from blotter.core import utils


class TestChunk(unittest.TestCase):

    def test_empty_list(self):
        """Ensure an empty list is returned when an empty list is passed."""
        from blotter.core.aggregation.trends import chunk

        self.assertEqual([], chunk([], 10).next())

    def test_bad_chunk_size(self):
        """Ensure an empty list is returned when a bad chunk size is passed."""
        from blotter.core.aggregation.trends import chunk

        self.assertEqual([], chunk([1, 2, 3, 4, 5], 0).next())

    def test_chunking_equal_groups(self):
        """Ensure the list is chunked properly into equal groups when it can be
        evenly divided.
        """
        from blotter.core.aggregation.trends import chunk

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
        from blotter.core.aggregation.trends import chunk

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


@patch('blotter.core.utils.urllib2')
class TestRequest(unittest.TestCase):

    def test_request(self, mock_urllib):
        """Verify request calls urlopen with the correct URL and returns the
        response.
        """

        mock_urllib.Request.return_value = Mock()
        mock_urllib.urlopen.return_value = Mock()
        url = 'http://foo.com'

        actual = utils.request(url)

        self.assertEqual(mock_urllib.urlopen.return_value, actual)
        mock_urllib.Request.assert_called_once_with(
            url,
            headers={'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) '
                                    'AppleWebKit/534.30 (KHTML, like Gecko) '
                                    'Ubuntu/11.04 Chromium/12.0.742.112 '
                                    'Chrome/12.0.742.112 Safari/534.30')})
        mock_urllib.urlopen.assert_called_once_with(
            mock_urllib.Request.return_value)

