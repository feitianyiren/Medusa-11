#!/usr/bin/env python

import flask

from lib.head.database import Database
from lib.head.index import Index
from lib.head.proxy import Proxy
from lib.medusa.communicate import Communicate
from lib.medusa.log import log

#------------------------------------------------------------------------------

api = flask.Blueprint("api", __name__)

#------------------------------------------------------------------------------

@api.route("/media/<int:media_id>", methods=["GET"])
def media(media_id):
    return flask.jsonify(Database().select_media(media_id))

@api.route("/search", methods=["POST"])
def search():
    media = Database().select_like_media(flask.request.form.get("term", ""))

    return flask.jsonify({"media": media})

@api.route("/snakes", methods=["GET"])
@api.route("/snakes/<queue>", methods=["GET"])
def snakes(queue=None):
    data = {}

    try:
        snakes = Communicate.connections

    except Exception as excp:
        log.error("Failed to get Snakes: %s", excp)

    if queue:
        for snake in snakes.keys():
            if not Proxy._snakes[snake].get("media_id"):
                snakes.pop(snake, None)

    data["snakes"] = snakes.keys()

    return flask.jsonify(data)

@api.route("/snake/<snake>/<action>", methods=["GET"])
@api.route("/snake/<snake>/<action>/<value>", methods=["GET"])
def send(snake, action, value=None):
    if action in ["play", "stop"]:
        send(snake, "empty_queue")

    arguments = [action]

    if value:
        arguments.append([value])

    else:
        arguments.append([])

    try:
        Communicate().send([snake], {"action": arguments})

        return "0"

    except Exception as excp:
        log.error("%s on %s failed: %s", action.title(), snake, excp)

        return "1"

@api.route("/status/<snake>", methods=["GET"])
def status(snake):
    return flask.jsonify(Proxy._snakes.get(snake, {}))

@api.route("/viewed/<media_id>")
@api.route("/viewed/<media_id>/<delete>")
def viewed(media_id, delete=None):
    database = Database()

    if not delete:
        database.insert_viewed(media_id)

    else:
        database.delete_viewed(media_id)

    return "0"

@api.route("/elapsed/<media_id>/<int:elapsed>")
def elapsed(media_id, elapsed):
    Database().update_viewed(media_id, elapsed)

    return "0"

@api.route("/index", methods=["GET"])
def index():
    try:
        Index().index()

        return "0"

    except Exception as excp:
        log.error("Index failed: %s", excp)

        return "1"
