from flask import render_template

from ripl.core.api.blueprint import blueprint


# Error handlers
@blueprint.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@blueprint.route('/')
def index():
    return render_template('index.html')

