import urllib2

from werkzeug.urls import url_fix


def request(url):
    """Make an HTTP GET request to the given URL.

    Args:
        url: the URL to request.

    Returns:
        urllib2 response.
    """

    url = url_fix(url)

    request = urllib2.Request(
        url, headers={'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) '
                                     'AppleWebKit/534.30 (KHTML, like Gecko) '
                                     'Ubuntu/11.04 Chromium/12.0.742.112 '
                                     'Chrome/12.0.742.112 Safari/534.30')})

    return urllib2.urlopen(request)

