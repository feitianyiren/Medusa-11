#!/usr/bin/env python

"""
Scan for new media items in the configured locations, parse filenames using
the user-defined patterns and index matches into the database.
"""

import json
import os
import re
import threading
import time

from lib.head.database import Database
from lib.medusa import categories
from lib.medusa import utilities
from lib.medusa.config import config
from lib.medusa.log import log

#------------------------------------------------------------------------------

EXPRESSIONS = {
    "base": ".*",
    "title": "(.*)",
    "year": "(\d{4})",
    "directors": "(.*)",
    "part": "\d*",
    "show": "(.*)",
    "season": "(\d{2})",
    "episode": "(\d{2})",
    "artist": "(.*)",
    "album": "(.*)"
}
ESCAPES = [" ", "-", "(", ")"]

#------------------------------------------------------------------------------

class Index(object):

    __metaclass__ = utilities.Singleton

    def __init__(self):
        self.thread = IndexThread()
        self.thread.start()

    def index(self):
        self.thread.now = True

    def stop(self):
        self.thread.stop = True

    def restart(self):
        self.thread.stop = False

#------------------------------------------------------------------------------

class IndexThread(threading.Thread):

    def __init__(self):
        super(IndexThread, self).__init__()

        self.database = Database()
        self.naming = self._get_naming()
        self.now = False
        self.stop = False

    def run(self):
        i = 0

        while True:
            i += 5

            if not self.stop:
                if self.now:
                    self.now = False

                    self.index()

                if i >= config.getint("index", "interval"):
                    i = 0

                    self.index()

            time.sleep(5)

    def index(self):
        log.warn("About to index media")

        self.stop = True

        media = []

        for category, value in self.naming.items():
            path = value.get("path")
            names = value.get("names")
            expressions = []

            for name in names:
                expressions.append(self._format_expression(name))

            media.extend(self.find_media(category, path, expressions))

        self.insert_new_media(media)
        self.delete_missing_media()

        self.now = False
        self.stop = False

        log.warn("Finished indexing media")

    #--------------------------------------------------------------------------

    def find_media(self, category, path, expressions):
        media = []
        deep = False

        if category in config.getlist("index", "deep"):
            deep = True

        if category in config.getlist("index", "audio_categories"):
            allowed_formats = config.getlist("index", "audio_formats")

        else:
            allowed_formats = config.getlist("index", "video_formats")

        for root, directories, files in os.walk(unicode(path)):
            data = {}
            paths = []
            data["category"] = category

            for f in files:
                if f.startswith("."):
                    continue

                sub_data = {}
                sub_paths = []
                sub_data["category"] = category

                f = os.path.join(root, f)
                short_path = f.replace("%s/" % os.path.dirname(path), "", 1)
                paths.append(short_path)
                sub_paths.append(short_path)

                extension = os.path.splitext(os.path.basename(f))[-1].replace(".", "", 1)

                if extension not in allowed_formats:
                    continue

                if not deep and data.get("extension"):
                    continue

                data["extension"] = extension
                sub_data["extension"] = extension

                match_path = os.path.splitext(short_path)[0]

                for expression in expressions:
                    matches = expression.match(match_path)

                    if matches:
                        break

                if not matches:
                    log.error("Failed to expression match %s", match_path)
                    
                    continue

                result = getattr(categories,
                                 "parse_%s" % category.lower())(matches)

                data.update(result)
                sub_data.update(result)

                try:
                    modified = int(os.stat(f).st_mtime)

                except Exception:
                    modified = 0

                data["modified"] = modified
                sub_data["modified"] = modified

                if not sub_paths or not sub_data.get("name_one"):
                    continue

                sub_data["paths"] = sub_paths

                if deep:
                    media.append(sub_data)

            if not paths or not data.get("name_one"):
                continue

            data["paths"] = paths

            if not deep:
                media.append(data)

        return media

    def insert_new_media(self, media):
       self.database.insert_media(media)

    def delete_missing_media(self):
        to_delete = set()

        for item in self.database.select_all_media():
            category = item["category"]
            base_path = os.path.dirname(self.naming[category]["path"])

            for path in item["paths"]:
                if not os.path.exists(os.path.join(base_path, path)):
                    to_delete.add(int(item["id"]))

        self.database.delete_media(to_delete)

    #--------------------------------------------------------------------------

    def _get_naming(self):
        naming_path = os.path.join(config.base_path,
                                   config.get("files", "naming"))

        with open(naming_path, "r") as file_:
            naming = json.load(file_)

        return naming

    def _format_expression(self, string):
        for character in ESCAPES:
            string = string.replace(character, "\\%s" % character)

        return re.compile(string.format(**EXPRESSIONS))
