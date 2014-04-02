#!/usr/bin/env python

"""
Various functions that relate to a specific category.
"""

import os

from lib.head.database import Database
from lib.medusa.communicate import Communicate

#------------------------------------------------------------------------------

def format_media_name(data):
    name = os.path.basename(data.get("paths", [])[0])
    category = data.get("category", "").lower()

    if category == "television":
        data["season"] = str(data["name_two"]).zfill(2)
        data["episode"] = str(data["name_three"]).zfill(2)

        name = "%(name_one)s - S%(season)sE%(episode)s - %(name_four)s" % data

    if category == "film":
        name = "%(name_one)s (%(year)s)" % data
        name = "%s - %s" % (name, ", ".join(data["name_two"]))

    return name

#------------------------------------------------------------------------------

def parse_film(matches):
    data = {}

    title, year, directors_ = matches.groups()

    directors = []

    for director in directors_.split(", "):
        directors.append(director)

    data["name_one"] = title
    data["name_two"] = directors
    data["name_three"] = ""
    data["name_four"] = ""
    data["year"] = int(year)

    return data

def parse_television(matches):
    data = {}

    if len(matches.groups()) == 5:
        show, year, season, show, episode = matches.groups()
        title = ""

    else:
        show, year, season, show, episode, title = matches.groups()

    data["name_one"] = show
    data["name_two"] = int(season)
    data["name_three"] = int(episode)
    data["name_four"] = title
    data["year"] = int(year)

    return data

def parse_music(matches):
    data = {}

    if len(matches.groups()) == 3:
        artist, album, title = matches.groups()
        year = 0

    else:
        artist, album, year, title = matches.groups()

    data["name_one"] = artist
    data["name_two"] = album
    data["name_three"] = title
    data["name_four"] = ""
    data["year"] = int(year)

    return data

#------------------------------------------------------------------------------

def queue_tracks(snake, value):
    """
    Queue up the remaining tracks of an album.
    """

    # If we get no tracks, this probably wasn't an album.
    tracks = Database().select_next_tracks(value)

    if tracks:
        queue_up = False

        for track in tracks:
            track_id = track["id"]

            if not queue_up:
                # Don't begin queuing until we have passed the user selected
                # track.
                #
                if track_id == int(value):
                    queue_up = True

                continue

            Communicate().send([snake], {"action": ["queue", [track_id]]})
