"""Create a flask app blueprint."""

import flask

from blotter.core.api.blueprint import blueprint

# Imported to register urls
from blotter.core.api import controller


def create_app(config="blotter.settings"):
    app = flask.Flask(__name__)

    app.config.from_object(config)

    app.register_blueprint(blueprint)

    # Enable jinja2 loop controls extension
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')

    return app
