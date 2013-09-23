import logging

from flask import render_template

from furious.async import Async

from ripl.core.api.blueprint import blueprint
from ripl.core.aggregation import AGGREGATION_QUEUE
from ripl.core.aggregation.trends import aggregate
from ripl.core.aggregation.trends import get_trend_for_location


# Error handlers
@blueprint.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@blueprint.route('/')
def index():
    """Render the index page."""

    return render_template('index.html', trends=_get_trends())


@blueprint.route('/aggregate')
def aggregate_trends():
    """Insert a task that will Kick off the trend aggregation process. This is
    intended to be called by a cron job.
    """

    Async(target=aggregate, queue=AGGREGATION_QUEUE).start()
    logging.debug('Inserted aggregate Async')

    return '', 200


def _get_trends():
    trends = {}
    locations = ['Worldwide', 'United States', 'Canada', 'United Kingdom',
                 'Brazil', 'Australia', 'Russia']

    for location in locations:
        trend = get_trend_for_location(location)
        if not trend:
            trends[location.replace(' ', '_')] = {'url': 'n/a', 'name': 'n/a',
                                                  'image_url': 'n/a',
                                                  'source': 'n/a'}
            continue

        content = trend.best_content()
        if not content:
            content = {'link': 'n/a', 'image': 'n/a', 'source': 'n/a'}

        trend = {'url': content['link'], 'name': trend.name,
                 'image_url': content['image'],
                 'source': content['source']}

        trends[location.replace(' ', '_')] = trend

    print trends
    return trends

