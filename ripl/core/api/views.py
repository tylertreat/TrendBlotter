from flask import render_template

from ripl.core.api.blueprint import blueprint
from ripl.core.aggregator import aggregate
from ripl.core.decorators import admin_required


# Error handlers
@blueprint.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@blueprint.route('/')
def index():
    """Render the index page."""

    return render_template('index.html')


@blueprint.route('/aggregate')
@admin_required
def aggregate_trends():
    """Kick off the trend aggregation process. This is intended to be called by
    a cron job.
    """

    aggregate()

