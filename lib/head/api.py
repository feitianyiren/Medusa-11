#!/usr/bin/env python

"""
The API routes through which the Head mediates interaction between the web
interface, Snakes, and the database.
"""

import flask

from lib.head import support

#------------------------------------------------------------------------------

api = flask.Blueprint("api", __name__)

#------------------------------------------------------------------------------

@api.route("/media/<int:media_id>", methods=["GET"])
def media(media_id):
    data = support.get_media(media_id)

    return flask.jsonify(data)

@api.route("/search", methods=["POST"])
def search():
    data = support.search_media(flask.request.form.get("term", ""))

    return flask.jsonify(data)

@api.route("/snakes", methods=["GET"])
@api.route("/snakes/<queue>", methods=["GET"])
def snakes(queue=None):
    data = support.get_snakes(queue)

    return flask.jsonify(data)

@api.route("/status/<snake>", methods=["GET"])
def status(snake):
    data = support.get_snake_status(snake)

    return flask.jsonify(data)

#------------------------------------------------------------------------------

@api.route("/snake/<snake>/<action>", methods=["GET"])
@api.route("/snake/<snake>/<action>/<value>", methods=["GET"])
def send(snake, action, value=None):
    result = support.send_to_snake(snake, action, value)

    return result

@api.route("/viewed/<media_id>")
@api.route("/viewed/<media_id>/<delete>")
def viewed(media_id, delete=None):
    result = support.update_viewed(media_id, delete=delete)

    return result

@api.route("/elapsed/<media_id>/<int:elapsed>")
def elapsed(media_id, elapsed):
    result = support.update_viewed(media_id, elapsed=elapsed)

    return result

@api.route("/index", methods=["GET"])
def index():
    result = support.run_index()

    return result
