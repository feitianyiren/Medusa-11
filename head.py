#!/usr/bin/env python

"""
Medusa's Head serves the web interface, API, and communicates instructions
to the Snakes (media players).
"""

import os

import flask

from lib.head.api import api
from lib.head.index import Index
from lib.head.proxy import Proxy
from lib.medusa.communicate import Communicate
from lib.medusa.config import config
from lib.medusa.log import log
from lib.view.pages import pages

#------------------------------------------------------------------------------

PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib/view")
API_BASE = config.get("head", "api_base")
URL_BASE = config.get("head", "url_base")

#------------------------------------------------------------------------------

app = flask.Flask(__name__,
                  template_folder="%s/templates" % PATH,
                  static_folder="%s/static" % PATH,
                  static_url_path="/%s/static" % URL_BASE)

app.register_blueprint(api, url_prefix="/%s/%s" % (URL_BASE, API_BASE))
app.register_blueprint(pages, url_prefix="/%s" % URL_BASE)

#------------------------------------------------------------------------------

@app.route("/")
def root():
    return flask.redirect("/%s" % URL_BASE)

#------------------------------------------------------------------------------

def main():
    Index()

    Communicate(proxy=Proxy)

    app.run(host="0.0.0.0", port=config.getint("ports", "head"))

#------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        log.warn("Head initialised")

        main()

    finally:
        log.warn("Head exited")
