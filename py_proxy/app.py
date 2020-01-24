"""The main application entrypoint module."""
import os

import pyramid.config
from pkg_resources import resource_filename
from whitenoise import WhiteNoise

from py_proxy.sentry_filters import SENTRY_FILTERS

REQUIRED_PARAMS = ["client_embed_url", "nginx_server", "legacy_via_url"]


def load_settings(settings):
    """Load application settings from a dict or environment variables.

    Checks that the required parameters are either filled out in the provided
    dict, or that the required values can be loaded from the environment.

    :param settings: Settings dict
    :raise ValueError: If a required parameter is not filled
    :return: A dict of settings
    """
    for param in REQUIRED_PARAMS:
        value = settings[param] = settings.get(param, os.environ.get(param.upper()))

        if value is None:
            raise ValueError(f"Param {param} must be provided.")

    # Configure sentry
    settings["h_pyramid_sentry.filters"] = SENTRY_FILTERS

    return settings


def create_app(_=None, **settings):
    """Configure and return the WSGI app."""
    config = pyramid.config.Configurator(settings=load_settings(settings))

    config.include("pyramid_jinja2")
    config.include("py_proxy.views")
    config.include("h_pyramid_sentry")

    app = WhiteNoise(
        config.make_wsgi_app(),
        index_file=True,
        root=resource_filename("py_proxy", "static"),
        prefix="/",
    )

    return app
