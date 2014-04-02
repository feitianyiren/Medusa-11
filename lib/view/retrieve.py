#!/usr/bin/env python

"""
Support functions used by the web interface to get and format data.
"""

from collections import OrderedDict
import datetime
import os

from lib.head.database import Database
from lib.head.proxy import Proxy
from lib.medusa import categories
from lib.medusa.config import config

#------------------------------------------------------------------------------

def get_new_items():
    path = config.get("browse", "downloads")
    video_formats = config.getlist("index", "video_formats")

    items = OrderedDict()
    files = []

    for root, directories, files_ in os.walk(unicode(path)):
        for f in files_:
            extension = os.path.splitext(f)[-1].lstrip(".")

            if extension in video_formats:
                modified = os.path.getmtime(os.path.join(root, f))
                files.append((modified, f, None))

    for item in Database().select_new():
        files.append((item["modified"],
                      categories.format_media_name(item),
                      item["id"]))

    for i in enumerate(sorted(files, reverse=True)):
        items[i[0]] = {
            "name_one": i[1][-2],
            "id": i[1][-1]
        }

    return items

def get_viewed_items():
    items = OrderedDict()

    for i in enumerate(Database().select_viewed()):
        media_id = i[1]["id"]
        name = None

        if media_id.isdigit():
            data = Database().select_media(int(media_id))

            if data:
                name = categories.format_media_name(data)

        else:
            name = media_id

        if name:
            items[media_id] = {
                "name_one": name
            }

    return items

def get_viewed_date(time):
    if not time:
        return

    return datetime.datetime.fromtimestamp(int(time)).strftime("%B %d, %Y")

def get_nearby_episodes(media_id):
    episodes = Database().select_category("television")

    index = episodes.keys().index(media_id)
    previous = episodes.keys()[index - 1]
    next = episodes.keys()[index + 1]

    show = episodes[media_id]["name_one"]

    if episodes[previous]["name_one"] != show:
        previous = None

    if episodes[next]["name_one"] != show:
        next = None

    return previous, next

def get_playing_snakes():
    snakes = Proxy._snakes

    for k, v in snakes.items():
        if not v.get("media_id"):
            snakes.pop(k, None)

    return snakes.keys()

def get_continue_media():
    database = Database()
    viewed = database.select_viewed()

    for item in viewed:
        try:
            media_id = int(item.get("id"))
            info = database.select_media(media_id)

        except Exception:
            continue

        if not info:
            return

        info["id"] = media_id
        info["elapsed"] = int(item.get("elapsed") or 0)

        category = info.get("category").lower()

        if category in ["film", "television"]:
            if info["elapsed"] > 0:
                return info

        if category == "television":
            previous, next = get_nearby_episodes(media_id)

            if next:
                info = database.select_media(next)
                info["id"] = next
                info["elapsed"] = 0

                return info

def get_continue_media_by_show(show):
    media_id = Database().select_latest_viewed_by_show(show)

    if not media_id:
        return

    previous, next = get_nearby_episodes(int(media_id))

    return next
