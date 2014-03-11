#!/usr/bin/env python

"""
The Medusa web interface page routes.
"""

from collections import OrderedDict

import flask

from lib.head.database import Database
from lib.head.proxy import Proxy
from lib.medusa.config import config
from lib.view import retrieve

#------------------------------------------------------------------------------

pages = flask.Blueprint("pages", __name__)

#------------------------------------------------------------------------------

@pages.route("/")
def index():
    for key, value in Proxy._snakes.items():
        if value.get("media_id"):
            return flask.redirect("/medusa/playing/%s" % key)

    return flask.redirect("/medusa/browse")

@pages.route("/browse")
def browse():
    categories = config.getlist("browse", "categories")
    continue_ = retrieve.get_continue_media()

    return flask.render_template("browse.html",
                                 categories=categories,
                                 continue_=continue_)

@pages.route("/browse/film")
def browse_film():
    items = Database().select_category("film")

    return flask.render_template("browse.html",
                                 category="film",
                                 items=items)

@pages.route("/browse/television")
def browse_television():
    items = OrderedDict()
    shows = []
    data = Database().select_category("television")

    for key, value in data.items():
        show = value["name_one"]

        if show not in shows:
            shows.append(show)
            items[key] = value

    return flask.render_template("browse.html",
                                 category="television",
                                 items=items)

@pages.route("/browse/television/<show>")
def browse_show(show):
    seasons = set()
    data = Database().select_category("television")

    for key, value in data.items():
        if value["name_one"] == show:
            seasons.add(value["name_two"])

    seasons = sorted(seasons)

    continue_ = retrieve.get_continue_media_by_show(show)

    return flask.render_template("browse.html",
                                 show=show,
                                 seasons=seasons,
                                 continue_=continue_)

@pages.route("/browse/television/<show>/<season>")
def browse_season(show, season):
    episodes = []
    data = Database().select_category("television")

    for key, value in data.items():
        if value["name_one"] == show and value["name_two"] == season:
            info = value
            info["id"] = key
            episodes.append(info)

    episodes = sorted(episodes, key=lambda k: int(k["name_three"]))

    return flask.render_template("browse.html",
                                 show=show,
                                 season=season,
                                 episodes=episodes)

@pages.route("/media/<int:media_id>")
def media(media_id):
    database = Database()

    item = database.select_media(media_id)

    if item["category"].lower() == "television":
        item["season"] = str(item["name_two"]).zfill(2)
        item["episode"] = str(item["name_three"]).zfill(2)
        item["previous"], item["next"] = retrieve.get_nearby_episodes(media_id)

    data = database.select_viewed(media_id)

    if data:
        item["viewed"] = retrieve.get_viewed_date(data["viewed"])
        item["elapsed"] = data["elapsed"]

    queue = True if retrieve.get_playing_snakes() else False

    return flask.render_template("media.html", item=item, queue=queue)

@pages.route("/media/new/<name>")
def media_new(name):
    item = {}
    item["category"] = "new"
    item["name"] = name

    return flask.render_template("media.html", item=item)

@pages.route("/new")
def new():
    items = retrieve.get_new_items()

    return flask.render_template("browse.html",
                                 category="new",
                                 items=items)

@pages.route("/playing")
@pages.route("/playing/<snake>")
@pages.route("/playing/<snake>/<advanced>")
def playing(snake=None, advanced=None):
    if not snake:
        if Proxy._snakes:
            return flask.redirect("/medusa/playing/%s" % Proxy._snakes.keys()[0])

        else:
            return flask.redirect("/medusa")

    return flask.render_template("playing.html",
                                 advanced=advanced)

@pages.route("/viewed")
def viewed():
    items = retrieve.get_viewed_items()

    return flask.render_template("browse.html",
                                 category="viewed",
                                 items=items)

@pages.route("/admin")
@pages.route("/admin/<snake>")
def admin(snake=None):
    return flask.render_template("admin.html",
                                 snake=snake)
