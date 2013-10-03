import unittest

from mock import Mock
from mock import patch

from blotter.core import utils


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

