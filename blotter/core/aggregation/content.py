"""This module is responsible for aggregating content for trends. The current
implementation works by crawling a selection of RSS feeds to find relevant
articles. In the future, this should probably be replaced by a more search-
engine-like solution.
"""

import hashlib
import logging
import re
import urllib2
import urlparse

from google.appengine.api import blobstore
from google.appengine.api import memcache

from bs4 import BeautifulSoup
import cloudstorage as gcs
import feedparser
from PIL import ImageFile

from blotter.core.aggregation import Trend
from blotter.core.utils import request


SCORE_THRESHOLD = 1


SOURCES = {
    'QUERY': {
        'feeds': {
            'Google News':
            'https://news.google.com/news/feeds?q=%s&geo=%s&output=rss'
        },
        'options': {
            'use_og': True
        }
    },
    'CNN': {
        'feeds': {
            'Top Stories': 'http://rss.cnn.com/rss/cnn_topstories.rss',
            'World': 'http://rss.cnn.com/rss/cnn_world.rss',
            'U.S.': 'http://rss.cnn.com/rss/cnn_us.rss',
            'Business': 'http://rss.cnn.com/rss/money_latest.rss',
            'Politics': 'http://rss.cnn.com/rss/cnn_allpolitics.rss',
            'Crime': 'http://rss.cnn.com/rss/cnn_crime.rss',
            'Technology': 'http://rss.cnn.com/rss/cnn_tech.rss',
            'Health': 'http://rss.cnn.com/rss/cnn_health.rss',
            'Entertainment': 'http://rss.cnn.com/rss/cnn_showbiz.rss',
        },
        'options': {
            'use_og': True
        }
    },
    'BBC': {
        'feeds': {
            'Top Stories': 'http://feeds.bbci.co.uk/news/rss.xml',
            'World': 'http://feeds.bbci.co.uk/news/world/rss.xml',
            'U.K.': 'http://feeds.bbci.co.uk/news/uk/rss.xml',
            'Business': 'http://feeds.bbci.co.uk/news/business/rss.xml',
            'Politics': 'http://feeds.bbci.co.uk/news/politics/rss.xml',
            'Health': 'http://feeds.bbci.co.uk/news/health/rss.xml',
            'Technology': 'http://feeds.bbci.co.uk/news/technology/rss.xml',
            'Sport': 'http://feeds.bbci.co.uk/sport/0/rss.xml?edition=uk'
        },
        'options': {
            'use_og': False
        }
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
    for source, data in SOURCES.iteritems():
        for feed_name, feed_url in data['feeds'].iteritems():
            cache_key = '%s-%s' % (source, feed_name)

            if source == 'QUERY':
                feed_url = feed_url % (urllib2.quote(trend.encode('utf8')),
                                       urllib2.quote(location.encode('utf8')))

                cache_key = '%s-%s-%s-%s' % (source, feed_name, trend,
                                             location)

            entries = memcache.get(cache_key)

            if not entries:
                entries = feedparser.parse(feed_url).get('entries', [])
                memcache.set('%s-%s' % (source, feed_name), entries, time=3600)

            for entry in entries:
                if 'link' not in entry:
                    continue

                if feed_name == 'Google News':
                    source = entry['title'].split(' - ')[-1]

                source_content = {'link': entry['link'], 'source': source,
                                  'score': _calculate_score(trend, entry)}

                if source_content['score'] > SCORE_THRESHOLD:
                    image_url = _find_content_image_url(
                        source_content['link'],
                        use_og=data['options']['use_og'])

                    if not image_url:
                        continue

                    image_hash = hashlib.sha1(image_url).hexdigest()
                    key = _copy_image_to_gcs(image_url, image_hash)

                    if not key:
                        continue

                    source_content['image_key'] = image_hash
                    content.append(source_content)

    # Update the Trend with content
    _add_content_to_trend('%s-%s-%s' % (trend, location, timestamp), content)


def _add_content_to_trend(trend_id, content):
    """Add content to the trend with the given ID.

    Args:
        trend_id: the ID of the Trend to update.
        content: a list of content dicts.
    """

    if content:
        trend = Trend.get_by_id(trend_id)
        logging.debug('Adding %d articles to %s' % (len(content), trend.name))
        trend.content = content
        trend.rating = trend.rating + len(content)
        trend.put()


def _calculate_score(trend, entry):
    """Calculate a score for the given trend and feed entry. The current naive
    implementation works by determining the number of occurrences of the trend
    in the entry title and summary. A score of 0 indicates that the entry is
    not relevant to the trend.

    Args:
        trend: the trend to calculate for.
        entry: the feed entry to calculate a score for.
    """

    regex = re.compile(r'\b%s\b' % trend, re.IGNORECASE)
    count = len(regex.findall(entry.get('title', '')))
    count += len(regex.findall(entry.get('summary', '')))
    return count


def _get_image_size(uri):
    """Retrieve the image dimensions, returned as a tuple (width, height).
    Returns None is the dimensions cannot be determined.
    """

    response = None
    try:
        response = request(uri)
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


def _copy_image_to_gcs(image_url, image_hash):
    """Download the image at the given URL and upload it to the blobstore.

    Args:
        image_url: the URL where the image is located.
        image_hash: a hash identifying the image.

    Returns:
        the uploaded image's blob key or None is the process failed.
    """

    response = request(image_url)
    content_type = response.headers.get('Content-Type')
    content = response.read()

    if content_type and content:
        return _write_to_gcs(content, image_hash, content_type)

    return None


def _write_to_gcs(content, content_hash, mime_type):
    """Write the given data to cloud storage.

    Args:
        content: the file data to write.
        content_hash: a hash identifying the content.
        mime_type: the mime type of the content.

    Returns:
        the blob key for the content.
    """

    gcs_filename = '/content_images/%s' % content_hash

    with gcs.open(gcs_filename, 'w', content_type=mime_type) as gcs_file:
        gcs_file.write(content)

    return blobstore.create_gs_key('/gs%s' % gcs_filename)


def _find_content_image_url(url, use_og=True):
    """Find the URL of the best image to use for the given content URL.

    Args:
        url: the content URL to scrape an image from.
        use_og: attempt to use the Open Graph protocol to find an image.

    Returns:
        an image URL or None if a suitable image was not found.
    """

    response = request(url)
    content_type = response.headers.get('Content-Type')
    content = response.read()

    if content_type and 'html' in content_type and content:
        soup = BeautifulSoup(content, 'lxml')
    else:
        return None

    # Allow the content author to specify the thumbnail, e.g.
    # <meta property="og:image" content="http://...">
    if use_og:
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

    if url is None or soup is None:
        raise StopIteration

    for img in soup.find_all("img", src=True):
        yield urlparse.urljoin(url, img["src"])

