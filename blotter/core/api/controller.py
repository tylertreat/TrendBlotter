import logging

from flask import render_template

from furious.async import Async

from blotter.core.aggregation import AGGREGATION_QUEUE
from blotter.core.aggregation.trends import aggregate
from blotter.core.api.blueprint import blueprint
from blotter.core.api.trends import get_trends_for_location


# Error handlers
@blueprint.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@blueprint.route('/')
def index():
    """Render the index page."""

    worldwide = get_trends_for_location('Worldwide', 1)[0]
    return render_template('index.html', worldwide=worldwide,
                           trends=_get_trends())


@blueprint.route('/aggregate')
def aggregate_trends():
    """Insert a task that will Kick off the trend aggregation process. This is
    intended to be called by a cron job.
    """

    Async(target=aggregate, queue=AGGREGATION_QUEUE).start()
    logging.debug('Inserted aggregate Async')

    return '', 200


def _get_trends():
    trends_list = []
    locations = ['United States', 'Canada', 'United Kingdom', 'Japan',
                 'Australia', 'Russia', 'Germany', 'France', 'Mexico', 'Kenya',
                 'Singapore', 'Turkey']

    for location in locations:
        trends = get_trends_for_location(location, 1)

        if not trends:
            continue

        trend = trends[0]

        if not trend.best_content:
            continue

        trends_list.append(trend)

    return trends_list

