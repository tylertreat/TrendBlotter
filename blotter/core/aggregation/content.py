"""This module is responsible for aggregating content for trends. The current
implementation works by crawling a selection of RSS feeds to find relevant
articles. In the future, this should probably be replaced by a more search-
engine-like solution.
"""

import logging
import urllib2
import urlparse

from google.appengine.api import memcache

from bs4 import BeautifulSoup
import feedparser
from PIL import ImageFile

from blotter.core.aggregation import scale_trend_rating
from blotter.core.aggregation import Trend


SOURCES = {
    'CNN': {
        'Top Stories': 'http://rss.cnn.com/rss/cnn_topstories.rss',
        'World': 'http://rss.cnn.com/rss/cnn_world.rss',
        'U.S.': 'http://rss.cnn.com/rss/cnn_us.rss',
        'Business': 'http://rss.cnn.com/rss/money_latest.rss',
        'Politics': 'http://rss.cnn.com/rss/cnn_allpolitics.rss',
        'Crime': 'http://rss.cnn.com/rss/cnn_crime.rss',
        'Technology': 'http://rss.cnn.com/rss/cnn_tech.rss',
        'Health': 'http://rss.cnn.com/rss/cnn_health.rss',
        'Entertainment': 'http://rss.cnn.com/rss/cnn_showbiz.rss',
        'Travel': 'http://rss.cnn.com/rss/cnn_travel.rss',
        'Living': 'http://rss.cnn.com/rss/cnn_living.rss'
    }
}


def aggregate_content(trend, location, timestamp):
    """Aggregate content for the given trend.

    Args:
        trend: the trend to collect content for.
        location: the name of the location the trend pertains to.
        timestamp: the unix timestamp of the trend.
    """

    logging.debug('Aggregating content for %s' % trend)

    content = []

    # Parse every feed and look for relevant content
    for source, feeds in SOURCES.iteritems():
        for feed_name, feed_url in feeds.iteritems():
            entries = memcache.get('%s-%s' % (source, feed_name))

            if not entries:
                entries = feedparser.parse(feed_url).get('entries', [])
                memcache.set('%s-%s' % (source, feed_name), entries, time=3600)

            source_content = [{'link': entry['link'], 'source': source,
                               'score': _calculate_score(trend, entry)}
                              for entry in entries if 'link' in entry]

            # Remove irrelevant entries and add the rest to the list
            content.extend([e for e in source_content if e['score'] > 0])

    for entry in content:
        image_url = _find_content_image_url(entry['link'])
        if not image_url:
            continue

        entry['image'] = image_url

    # Update the Trend with content
    if content:
        logging.debug('Adding %d articles to %s' % (len(content), trend))
        trend_entity = Trend.get_by_id(
            '%s-%s-%s' % (trend, location, timestamp))
        trend_entity.content = content
        trend_entity.rating = scale_trend_rating(
            trend_entity.rating + len(content))
        trend_entity.put()


def _calculate_score(trend, entry):
    """Calculate a score for the given trend and feed entry. The current naive
    implementation works by determining the number of occurrences of the trend
    in the entry title and summary. A score of 0 indicates that the entry is
    not relevant to the trend.

    Args:
        trend: the trend to calculate for.
        entry: the feed entry to calculate a score for.
    """

    count = entry.get('title', '').lower().count(trend.lower())
    count += entry.get('summary', '').lower().count(trend.lower())
    return count


def _get_image_size(uri):
    """Retrieve the image dimensions, returned as a tuple (width, height).
    Returns None is the dimensions cannot be determined.
    """

    try:
        response = urllib2.urlopen(uri)
        parser = ImageFile.Parser()

        while True:
            data = response.read(1024)

            if not data:
                break

            parser.feed(data)

            if parser.image:
                return parser.image.size

        return None
    except urllib2.URLError:
        return None
    finally:
        if response:
            response.close()


def _find_content_image_url(url):
    """Find the URL of the best image to use for the given content URL.
    Returns None if a suitable image cannot be found.
    """

    response = urllib2.urlopen(url)
    content_type = response.headers.get('Content-Type')
    content = response.read()

    if content_type and 'html' in content_type and content:
        soup = BeautifulSoup(content)
    else:
        return None

    # Allow the content author to specify the thumbnail, e.g.
    # <meta property="og:image" content="http://...">
    og_image = (soup.find('meta', property='og:image') or
                soup.find('meta', attrs={'name': 'og:image'}))
    if og_image and og_image['content']:
        return og_image['content']

    # <link rel="image_src" href="http://...">
    thumbnail_spec = soup.find('link', rel='image_src')
    if thumbnail_spec and thumbnail_spec['href']:
        return thumbnail_spec['href']

    # Look for the largest image on the page if the author has not provided one
    max_area = 0
    max_url = None

    for image_url in _get_image_urls(url, soup):
        size = _get_image_size(image_url)
        if not size:
            continue

        area = size[0] * size[1]

        # Ignore little images
        if area < 5000:
            continue

        # Ignore excessively long/wide images
        if max(size) / min(size) > 1.5:
            continue

        # Penalize images with "sprite" in their name
        if 'sprite' in image_url.lower():
            area /= 10

        if area > max_area:
            max_area = area
            max_url = image_url

    return max_url


def _get_image_urls(url, soup):
    """Retrieve all image URLs for the given content URL.

    Args:
        url: the content URL to retrieve image URLs for.
        soup: a BeautifulSoup instance for the given URL.
    """

    for img in soup.findAll("img", src=True):
        yield urlparse.urljoin(url, img["src"])

