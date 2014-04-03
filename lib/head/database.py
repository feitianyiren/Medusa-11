#!/usr/bin/env python

"""
Query and modify the SQLite database of media items and viewing history.

Select results will be cached until the cache is expired due to an insert.
"""

from collections import OrderedDict
import os
import sqlite3
import time

from lib.medusa.config import config
from lib.medusa.log import log

#------------------------------------------------------------------------------

class Database(object):

    _cache = {}

    def __init__(self):
        self.database = DatabaseConnection()

    #--------------------------------------------------------------------------

    def select_category(self, category):
        log.info("Perfoming category select: %s", category)

        data = self._cache.get(category, {})

        if data:
            log.info("Returning category select from cache")

            return data

        with self.database:
            data = self.database.select_media_by_category(category)

        self._cache[category] = data

        log.info("Returning category select from database")

        return data

    def select_media(self, media_id):
        log.info("Perfoming media ID select: %s", media_id)

        data = {}

        for key in self._cache.keys():
            data = self._cache[key].get(media_id, {})

            if data:
                break

        if data:
            log.info("Returning media select from cache")

            return data

        with self.database:
            data = self.database.select_media_by_id(media_id)

        if data.get(media_id):
            category = data[media_id]["category"]

            if not self._cache.get(category):
                self._cache[category] = {}

            self._cache[category][media_id] = data[media_id]

        log.info("Returning media select from database")

        return data.get(media_id)

    def select_all_media(self):
        log.info("Perfoming all media select")

        with self.database:
            data = self.database.select_media()

        return data

    def select_like_media(self, term):
        log.info("Perfoming search with term: %s", term)

        with self.database:
            data = self.database.select_media_like_term(term)

        return data

    def select_new(self):
        log.info("Perfoming new media select")

        with self.database:
            data = self.database.select_media_by_modified()

        return data

    def select_viewed(self, media_id=None):
        log.info("Perfoming viewed media select")

        with self.database:
            if media_id:
                data = self.database.select_viewed_by_id(media_id)

                if data:
                    data = data[0]

            else:
                data = self.database.select_viewed()

        return data

    def select_latest_viewed_by_show(self, show):
        log.info("Perfoming latest viewed select for show: %s", show)

        with self.database:
            data = self.database.select_latest_viewed_by_show(show)

        if data:
            return data["id"]

    def select_next_tracks(self, media_id):
        log.info("Perfoming select next tracks for media: %s", media_id)

        try:
            media_id = int(media_id)

            with self.database:
                data = self.database.select_media_by_id(media_id)[media_id]

        except Exception as excp:
            log.error("Select next tracks failed: %s", excp)

            return []

        if data["category"] != "Music":
            return []

        artist = data["name_one"]
        album = data["name_two"]

        with self.database:
            data = self.database.select_tracks(artist, album)

        return data

    #--------------------------------------------------------------------------

    def insert_media(self, media):
        if isinstance(media, dict):
            media = [media]

        inserted = False

        with self.database:
            for data in media:
                check = self.database.select_media_by_paths(data)

                if not check:
                    log.warn("Inserting new media: %s", data)

                    self.database.insert_media(data)
                    inserted = True

        if inserted:
            self.clear_cache()

    def insert_viewed(self, media_id):
        log.warn("Inserting viewed media: %s", media_id)

        with self.database:
            self.database.insert_viewed(media_id)

    #--------------------------------------------------------------------------            

    def update_viewed(self, media_id, elapsed):
        log.warn("Updating elapsed for %s: %s", media_id, elapsed)

        with self.database:
            self.database.update_viewed(media_id, elapsed)

    #--------------------------------------------------------------------------

    def delete_media(self, media_ids):
        with self.database:
            for media_id in media_ids:
                log.warn("Deleting media: %s", media_id)

                self.database.delete_media_by_id(media_id)

        if media_ids:
            self.clear_cache()

    def delete_viewed(self, media_id):
        log.warn("Deleting viewed: %s", media_id)

        with self.database:
            self.database.delete_viewed(media_id)

    #--------------------------------------------------------------------------

    @classmethod
    def clear_cache(cls, category=None, media_id=None):
        if media_id:
            if not category:
                return

            log.warn("Clearing cache for media ID: %s", media_id)

            for category in cls._cache.keys():
                if cls._cache[category].get(media_id):
                    del cls._cache[category][media_id]

        elif category:
            log.warn("Clearing cache for category: %s", category)
            del cls._cache[category]

        else:
            log.warn("Clearing cache for all categories")
            cls._cache = {}

#------------------------------------------------------------------------------

class DatabaseConnection(object):

    def __init__(self):
        self.database = os.path.join(config.base_path,
                                     config.get("files", "database"))

        if not os.path.exists(self.database):
            self.create_database()

    def __enter__(self):
        self._open_connection()

    def __exit__(self, type, value, traceback):
        self._close_connection()

    def _open_connection(self):
        log.info("Opening database connection")

        self.connection = sqlite3.connect(self.database)
        self.connection.text_factory = str
        self.connection.row_factory = self._dictionary_factory
        self.cursor = self.connection.cursor()

    def _close_connection(self):
        log.info("Closing database connection")

        self.connection.commit()
        self.cursor.close()
        self.connection.close()

    @staticmethod
    def _sanitise(value):
        encoding = config.get("head", "encoding")

        if isinstance(value, list):
            return "|%s" % "|".join(v.encode(encoding) for v in value)

        elif isinstance(value, str):
            return value.encode(encoding)

        return value

    @staticmethod
    def _dictionary_factory(cursor, row):
        result = {}

        for index, column in enumerate(cursor.description):
            value = row[index]

            try:
                value = value.decode(config.get("head", "encoding"))

            except Exception:
                pass

            if isinstance(value, unicode):
                if value.startswith("|"):
                    value = value.split("|")[1:]

            result[column[0]] = value

        return result

    #--------------------------------------------------------------------------

    def create_database(self):
        log.warn("Creating database")

        self._open_connection()

        self.cursor.execute("""CREATE TABLE
                               media
                               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                category TEXT,
                                paths TEXT,
                                name_one TEXT,
                                name_two TEXT,
                                name_three TEXT,
                                name_four TEXT,
                                year INTEGER,
                                extension TEXT,
                                modified INTEGER)
                            """)

        self.cursor.execute("""CREATE TABLE
                               viewed
                               (id TEXT,
                                viewed INTEGER,
                                elapsed INTEGER)
                            """)

        self._close_connection()

        log.warn("Created database")

    #--------------------------------------------------------------------------

    def select_media(self):
        self.cursor.execute("""
                            SELECT *
                            FROM media
                            """)

        return self.cursor.fetchall()

    def select_media_by_id(self, media_id):
        result = {}

        self.cursor.execute("""
                            SELECT *
                            FROM media
                            LEFT JOIN viewed USING (id)
                            WHERE id = ?
                            """, (media_id,))

        rows = self.cursor.fetchall()

        if rows:
            row = rows[0]
            key = row.pop("id")
            result[key] = row

        return result

    def select_media_by_category(self, category):
        results = OrderedDict()

        self.cursor.execute("""
                            SELECT *
                            FROM media
                            WHERE category = ?
                            ORDER BY name_one ASC,
                            cast(name_two as unsigned) ASC,
                            cast(name_three as unsigned) ASC,
                            name_four ASC
                            """, (category.title(),))

        rows = self.cursor.fetchall()

        for row in rows:
            key = row.pop("id")
            results[key] = row

        return results

    def select_media_like_term(self, term):
        like_term = "%%%s%%" % term

        self.cursor.execute("""
                            SELECT *
                            FROM media
                            WHERE (name_one LIKE ?)
                            OR (name_two LIKE ?)
                            OR (name_three LIKE ?)
                            OR (name_four LIKE ?)
                            OR (year = ?)
                            ORDER BY year DESC
                            """, (like_term,
                                  like_term,
                                  like_term,
                                  like_term,
                                  term))

        return self.cursor.fetchall()

    def select_media_by_modified(self):
        self.cursor.execute("""
                            SELECT *
                            FROM media
                            ORDER BY modified DESC
                            LIMIT 10
                            """)

        return self.cursor.fetchall()

    def select_media_by_paths(self, data):
        self.cursor.execute("""
                            SELECT *
                            FROM media
                            WHERE category = ?
                            AND paths = ?
                            """, (data["category"],
                                  self._sanitise(data["paths"])))

        return self.cursor.fetchall()

    def select_viewed(self):
        self.cursor.execute("""
                            SELECT id,
                            viewed,
                            elapsed
                            FROM viewed
                            ORDER BY viewed DESC
                            LIMIT 100
                            """)

        return self.cursor.fetchall()

    def select_viewed_by_id(self, media_id):
        self.cursor.execute("""
                            SELECT viewed,
                            elapsed
                            FROM viewed
                            WHERE id = ?
                            """, (media_id,))

        return self.cursor.fetchall()

    def select_latest_viewed_by_show(self, show):
        self.cursor.execute("""
                            SELECT id
                            FROM viewed
                            JOIN media USING (id)
                            WHERE name_one = ?
                            ORDER BY viewed DESC
                            LIMIT 1
                            """, (show,))

        return self.cursor.fetchone()

    def select_tracks(self, artist, album):
        self.cursor.execute("""
                            SELECT *
                            FROM media
                            WHERE name_one = ?
                            AND name_two = ?
                            ORDER BY name_three ASC
                            """, (artist, album))

        return self.cursor.fetchall()

    #--------------------------------------------------------------------------

    def insert_media(self, data):
        category = data.get("category")

        if not category:
            return

        paths = self._sanitise(data["paths"])
        name_one = self._sanitise(data["name_one"])
        name_two = self._sanitise(data["name_two"])
        name_three = self._sanitise(data["name_three"])
        name_four = self._sanitise(data["name_four"])
        year = data["year"]
        extension = data["extension"]
        modified = data["modified"]

        self.cursor.execute("""
                            INSERT INTO media (
                                category,
                                paths,
                                name_one,
                                name_two,
                                name_three,
                                name_four,
                                year,
                                extension,
                                modified)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (category,
                                  paths,
                                  name_one,
                                  name_two,
                                  name_three,
                                  name_four,
                                  year,
                                  extension,
                                  modified))

    def insert_viewed(self, media_id):
        media_id = media_id
        viewed = int(time.time())

        self.cursor.execute("""
                            INSERT OR IGNORE INTO viewed (
                                id,
                                viewed)
                            VALUES (?, ?)
                            """, (media_id,
                                  viewed))

        self.cursor.execute("""
                            UPDATE viewed
                            SET viewed = ?
                            WHERE id = ?
                            """, (media_id,
                                  viewed))

    #--------------------------------------------------------------------------

    def update_viewed(self, media_id, elapsed):
        media_id = media_id
        elapsed = int(elapsed)

        self.cursor.execute("""
                            UPDATE viewed
                            SET elapsed = ?
                            WHERE id = ?
                            """, (elapsed,
                                  media_id))

    #--------------------------------------------------------------------------

    def delete_viewed(self, media_id):
        self.cursor.execute("""
                            DELETE FROM viewed
                            WHERE id = ?
                            """, (media_id,))

    def delete_media_by_id(self, media_id):
        self.cursor.execute("""
                            DELETE FROM media
                            WHERE id = ?
                            """, (media_id,))
