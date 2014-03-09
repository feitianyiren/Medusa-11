#!/usr/bin/env python

import os
import socket

#------------------------------------------------------------------------------

def get_hostname():
    return socket.gethostname()

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

class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]
