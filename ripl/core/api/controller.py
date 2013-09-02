import logging

from flask import render_template

from furious.async import Async

from ripl.core.api.blueprint import blueprint
from ripl.core.aggregation import AGGREGATION_QUEUE
from ripl.core.aggregation.aggregator import aggregate


# Error handlers
@blueprint.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@blueprint.route('/')
def index():
    """Render the index page."""

    return render_template('index.html')


@blueprint.route('/aggregate')
def aggregate_trends():
    """Insert a task that will Kick off the trend aggregation process. This is
    intended to be called by a cron job.
    """

    Async(target=aggregate, queue=AGGREGATION_QUEUE).start()
    logging.debug('Inserted aggregate Async')

    return '', 200

