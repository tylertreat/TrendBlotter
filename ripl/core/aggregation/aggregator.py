"""This module is responsible for aggregating trend data from social media.
Currently, Twitter is the only data source but others may be added ad hoc.

Some important considerations:
    - Twitter limits applications to 15 API calls per 15 minutes for the trends
      and locations endpoints. We need to avoid hitting this ceiling, which
      means we can't simply fetch all locations and fan out on them in
      parallel.
"""

import logging

from google.appengine.api import memcache
from google.appengine.ext import ndb

from furious import context
from furious.async import Async
from furious.errors import Abort

from ripl.core.aggregation import AGGREGATION_QUEUE
from ripl.core.aggregation import ApiRequestException
from ripl.core.aggregation import Location
from ripl.core.aggregation.client import twitter


THROTTLE_TIME = 60 * 20
THROTTLE_SWITCH = 'throttle'


def aggregate():
    """Kick off the trend aggregation process."""

    logging.debug('Aggregation process started')

    locations = twitter.get_locations_with_trends()

    # Fan out on Locations
    with context.new() as ctx:
        for location in locations:
            ctx.add(target=aggregate_for_location, args=(location,),
                    queue=AGGREGATION_QUEUE)


def aggregate_for_location(loc):
    """Collect trend data for the given location, specified as a dict, and
    persist it to the datastore.
    """

    if memcache.get(THROTTLE_SWITCH):
        # We're being throttled, so insert a throttled task
        logging.warn('Request limit reached, inserting throttle task')
        Async(target=aggregate_for_location, args=(loc,),
              queue=AGGREGATION_QUEUE,
              task_args={'countdown': THROTTLE_TIME}).start()
        Abort()

    location = Location(id=loc['woeid'], name=loc['name'], woeid=loc['woeid'],
                        type_name=loc['placeType']['name'],
                        type_code=loc['placeType']['code'],
                        parent_id=loc['parentid'], country=loc['country'],
                        country_code=loc['countryCode'])

    ndb.put_async(location)

    try:
        trends = twitter.get_trends_by_location(location.woeid)
        if trends:
            logging.debug('Persisting %d trends for %s' % (len(trends),
                                                           location.name))
            ndb.put_multi_async(trends)
    except ApiRequestException as e:
        if e.status == 429:
            # Hit request window limit, so insert a throttled task
            logging.warn('Request limit reached, inserting throttle task')
            Async(target=aggregate_for_location, args=(loc,),
                  queue=AGGREGATION_QUEUE,
                  task_args={'countdown': THROTTLE_TIME}).start()
            memcache.set(THROTTLE_SWITCH, True, time=THROTTLE_TIME)
            Abort()

        logging.error('Could not fetch trends for %s' % location.name)
        logging.exception(e)

