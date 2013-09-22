"""This module is responsible for aggregating trend data from social media.
Currently, Twitter is the only data source but others may be added ad hoc.

Some important considerations:
    - Twitter limits applications to 15 API calls per 15 minutes for the trends
      and locations endpoints. We need to avoid hitting this ceiling, which
      means we can't simply fetch all locations and fan out on them in
      parallel.
"""

import logging

from google.appengine.ext import ndb

from furious import context
from furious.errors import Abort

from ripl.core.aggregation import AGGREGATION_QUEUE
from ripl.core.aggregation import ApiRequestException
from ripl.core.aggregation import CONTENT_QUEUE
from ripl.core.aggregation import Location
from ripl.core.aggregation.client import twitter
from ripl.core.aggregation.content import aggregate_content


BATCH_SIZE = 15
THROTTLE_TIME = 60 * 16

# Places to exclude from aggregation, see
# http://developer.yahoo.com/geo/geoplanet/guide/concepts.html#placetypes
EXCLUDE_TYPES = [7, 8, 9, 10, 11, 22, 31]


def aggregate():
    """Kick off the trend aggregation process."""

    logging.debug('Aggregation process started')

    # Only aggregate data for coarse-grained locations, e.g. countries
    locations = twitter.get_locations_with_trends(exclude=EXCLUDE_TYPES)
    logging.debug('Fetched %d locations from Twitter' % len(locations))

    # Fan out on locations, 15 per batch. Due to Twitter's 15 minute request
    # window, we space these batches out by 16 minutes.
    with context.new() as ctx:
        for i, batch in enumerate(chunk(locations, BATCH_SIZE)):
            ctx.add(target=aggregate_for_locations, args=(batch,),
                    queue=AGGREGATION_QUEUE,
                    task_args={'countdown': THROTTLE_TIME * i})

    logging.debug('Inserted %d fan-out tasks' % ctx.insert_success)


def aggregate_for_locations(locations):
    """Collect trend data for the given locations, specified as dicts, and
    persist it to the datastore.
    """

    locations = _location_dicts_to_entities(locations)

    # TODO: there's no reason to put locations that already exist since they
    # won't change.
    ndb.put_multi(locations)

    for location in locations:
        try:
            trends = twitter.get_trends_by_location(location.woeid)
            if trends:
                logging.debug('Persisting %d trends for %s' % (len(trends),
                                                               location.name))
                ndb.put_multi(trends)
                _aggregate_trend_content(trends, location)

        except ApiRequestException as e:
            logging.error('Could not fetch trends for %s' % location.name)
            logging.exception(e)

            # Fail fast if we've hit the request window limit
            if e.status == 429:
                logging.warn('Request limit window hit, aborting')
                raise Abort()


def _aggregate_trend_content(trends, location):
    """Insert tasks to aggregate content for the given trends."""

    with context.new() as ctx:
        for trend in trends:
            ctx.add(target=aggregate_content, queue=CONTENT_QUEUE,
                    args=(trend.name, location.woeid, trend.unix_timestamp()))


def chunk(the_list, chunk_size):
    """Chunks the given list into lists of size chunk_size."""

    if not the_list or chunk_size <= 0:
        yield []
        return

    for i in xrange(0, len(the_list), chunk_size):
        yield the_list[i:i + chunk_size]


def _location_dicts_to_entities(locations):
    """Convert the list of location dicts to location entities."""

    return [Location(id=loc['woeid'], name=loc['name'], woeid=loc['woeid'],
                     type_name=loc['placeType']['name'],
                     type_code=loc['placeType']['code'],
                     parent_id=loc['parentid'], country=loc['country'],
                     country_code=loc['countryCode']) for loc in locations]

