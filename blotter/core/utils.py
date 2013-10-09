import urllib2

from werkzeug.urls import url_fix


def chunk(the_list, chunk_size):
    """Chunks the given list into lists of size chunk_size.

    Args:
        the_list: the list to chunk into sublists.
        chunk_size: the size to chunk the list by.

    Returns:
        generator that yields the chunked sublists.
    """

    if not the_list or chunk_size <= 0:
        yield []
        return

    for i in xrange(0, len(the_list), chunk_size):
        yield the_list[i:i + chunk_size]


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

