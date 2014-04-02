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
                                 page="browse",
                                 categories=categories,
                                 continue_=continue_)

@pages.route("/browse/film")
def browse_film():
    items = Database().select_category("film")

    return flask.render_template("browse.html",
                                 page="browse",
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
                                 page="browse",
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
                                 page="browse",
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
                                 page="browse",
                                 show=show,
                                 season=season,
                                 episodes=episodes)

@pages.route("/browse/music")
def browse_music():
    items = OrderedDict()
    artists = set()
    data = Database().select_category("music")

    for value in data.values():
        artists.add(value["name_one"])

    for artist in sorted(artists):
        items[artist] = {
            "name_one": artist
        }

    return flask.render_template("browse.html",
                                 page="browse",
                                 category="music",
                                 items=items)

@pages.route("/browse/music/<artist>")
def browse_artist(artist):
    albums = set()
    data = Database().select_category("music")

    for key, value in data.items():
        if value["name_one"] == artist:
            albums.add(value["name_two"])

    albums = sorted(albums)

    return flask.render_template("browse.html",
                                 page="browse",
                                 artist=artist,
                                 albums=albums)

@pages.route("/browse/music/<artist>/<album>")
def browse_album(artist, album):
    tracks = []
    data = Database().select_category("music")

    for key, value in data.items():
        if value["name_one"] == artist and value["name_two"] == album:
            info = value
            info["id"] = key
            tracks.append(info)

    tracks = sorted(tracks, key=lambda k: k["name_three"])

    return flask.render_template("browse.html",
                                 page="browse",
                                 artist=artist,
                                 album=album,
                                 tracks=tracks)

@pages.route("/media/<media_id>")
def media(media_id):
    if media_id == "disc":
        item = {
            "category": media_id
        }

    else:
        media_id = int(media_id)

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

    return flask.render_template("media.html",
                                 page="media",
                                 item=item,
                                 queue=queue)

@pages.route("/media/new/<name>")
def media_new(name):
    item = {}
    item["category"] = "new"
    item["name"] = name

    return flask.render_template("media.html",
                                 page="media",
                                 item=item)

@pages.route("/new")
def new():
    items = retrieve.get_new_items()

    return flask.render_template("browse.html",
                                 page="browse",
                                 category="new",
                                 items=items)

@pages.route("/playing")
@pages.route("/playing/<snake>")
@pages.route("/playing/<snake>/<alternative>")
def playing(snake=None, alternative=None):
    if not snake:
        if Proxy._snakes:
            return flask.redirect("/medusa/playing/%s" % Proxy._snakes.keys()[0])

        else:
            return flask.redirect("/medusa")

    return flask.render_template("playing.html",
                                 page="playing",
                                 alternative=alternative)

@pages.route("/viewed")
def viewed():
    items = retrieve.get_viewed_items()

    return flask.render_template("browse.html",
                                 page="browse",
                                 category="viewed",
                                 items=items)

@pages.route("/admin")
@pages.route("/admin/<snake>")
def admin(snake=None):
    return flask.render_template("admin.html",
                                 page="admin",
                                 snake=snake)
