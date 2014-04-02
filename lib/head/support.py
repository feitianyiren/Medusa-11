#!/usr/bin/env python

"""
Various functions used to support the API.
"""

from lib.head.database import Database
from lib.head.index import Index
from lib.head.proxy import Proxy
from lib.medusa import categories
from lib.medusa.communicate import Communicate
from lib.medusa.config import config
from lib.medusa.log import log

#------------------------------------------------------------------------------

def get_media(media_id):
    return Database().select_media(media_id)

def search_media(term):
    return {"media": Database().select_like_media(term)}

#------------------------------------------------------------------------------

def get_snakes(queue):
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

    return data

def get_snake_status(snake):
    return Proxy._snakes.get(snake, {})

def send_to_snake(snake, action, value=None):
    if action in ["play", "stop"]:
        send_to_snake(snake, "empty_queue")

    arguments = [action]

    if value:
        arguments.append([value])

    else:
        arguments.append([])

    try:
        Communicate().send([snake], {"action": arguments})

        if action == "play":
            categories.queue_tracks(snake, value)

        return "0"

    except Exception as excp:
        log.error("%s on %s failed: %s", action.title(), snake, excp)

        return "1"

#------------------------------------------------------------------------------

def update_viewed(media_id, elapsed=None, delete=False):
    try:
        database = Database()

        try:
            info = database.select_media(int(media_id))

        except Exception:
            info = {}

        if info.get("category") in config.getlist("viewed", "no_history"):
            return "0"

        if elapsed:
            database.update_viewed(media_id, elapsed)

        elif delete:
            database.delete_viewed(media_id)

        else:
            database.insert_viewed(media_id)

        return "0"

    except Exception as excp:
        log.error("Update viewed failed: %s", excp)

        return "1"

#------------------------------------------------------------------------------

def run_index():
    try:
        Index().index()

        return "0"

    except Exception as excp:
        log.error("Index failed: %s", excp)

        return "1"
