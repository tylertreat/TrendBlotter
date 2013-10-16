import logging

from google.appengine.api import memcache

from flask import render_template
from flask import Response

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


@blueprint.route('/image/<image_key>')
def get_image(image_key):
    """Serve the content image with the given key."""
    import cloudstorage as gcs

    if not image_key:
        logging.error("No image key provided")
        return

    image = memcache.get(image_key)

    if image:
        return Response(image, mimetype='image/jpeg')

    image = gcs.open('/content_images/%s' % image_key)
    data = image.read()
    response = Response(data, mimetype='image/jpeg')
    image.close()

    # TODO: Memcache cannot handle images greater than 1MB
    memcache.set(image_key, data)

    return response


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

