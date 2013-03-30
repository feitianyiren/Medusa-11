"""Part of Medusa (MEDia USage Assistant).

Provides a protocol for using the SQLite3 database.

There are presently 4 tables in the database:

Receivers: Contains information on alive and active Receivers.

Viewed: Contains information on when media was last played and time elapsed.

Film, Television: Contain information on individual media.

Music is yet to be implemented.
"""

import sqlite3

import configger as config

# The SQLite database.
#------------------------------------------------------------------------------

class Database(object):
    def __init__(self):
        self.database_file = config.database_file

    def __enter__(self):
        self.open_connection()

    def __exit__(self, type, value, traceback):
        self.close_connection()

    def open_connection(self):
        """Opens a new database connection and initiates a cursor."""

        self.connection = sqlite3.connect(self.database_file)

        # To support all sorts of foreign characters.
        self.connection.text_factory = str

        # To return a dictionary with column names and rows.
        self.connection.row_factory = self.dictionary_factory

        self.cursor = self.connection.cursor()

    def close_connection(self):
        """Commits and then closes the database cursor and connection."""

        self.connection.commit()

        self.cursor.close()

        self.connection.close()

    @staticmethod
    def dictionary_factory(cursor, row):
        """Builds a dictionary for the row with column names."""

        details = {}

        for index, column in enumerate(cursor.description):
            details[column[0]] = row[index]

        return details

    def decode_string(self, string):
        return string.decode("utf-8")

    def check_receiver(self, host):
        """Checks to see if a Receiver has already been entered into the
        database.

        Returns either True or False.
        """

        self.cursor.execute("""
                            SELECT id
                            FROM receivers
                            WHERE host = ?
                            """, (host,))

        row = self.cursor.fetchone()

        try:
            row["id"]

            return True

        except TypeError:
            return False

    def insert_receiver(self, host, name):
        self.cursor.execute("""
                            INSERT INTO receivers
                            VALUES
                            (null,
                            ?, ?,
                            null, null, null)
                            """, (host,
                                  name))

    def update_receiver_status(self, host, status):
        self.cursor.execute("""
                            UPDATE receivers
                            SET status = ?
                            WHERE host = ?
                            """, (status,
                                  host))

    def update_receiver_media(self, host, media_directory, media_info):
        self.cursor.execute("""
                            UPDATE receivers
                            SET media_directory = ?,
                            media_info = ?
                            WHERE host = ?
                            """, (media_directory,
                                  media_info,
                                  host))

    def select_receiver(self, host):
        self.cursor.execute("""
                            SELECT name,
                            status,
                            media_directory as directory,
                            media_info
                            FROM receivers
                            WHERE host = ?
                            """, (host,))

        row = self.cursor.fetchone()

        if row:
            return row

        else:
            return {}

    def select_receivers(self):
        self.cursor.execute("""
                            SELECT host,
                            name
                            FROM receivers
                            """)

        return self.cursor.fetchall()

    def delete_receiver(self, host):
        self.cursor.execute("""
                            DELETE FROM receivers
                            WHERE host = ?
                            """, (host,))

    def select_viewed_media(self):
        """Returns a dictionary of the last 15 played media."""

        self.cursor.execute("""
                            SELECT media_directory,
                            media_info
                            FROM viewed
                            WHERE date_played NOT NULL
                            ORDER BY date_played DESC
                            LIMIT 15
                            """)

        return self.cursor.fetchall()

    def update_media_played(self, media_directory, media_info):
        # New media is handled separately as it has no auto database entry.
        if media_directory == "new":
            self.cursor.execute("""
                                SELECT media_info
                                FROM viewed
                                WHERE media_directory = "new"
                                AND media_info = ?
                                """, (media_info,))

            row = self.cursor.fetchone()

            # If it already has an entry, great.
            try:
                row["media_info"]

            # If not, give it one.
            except TypeError:
                self.cursor.execute("""
                                    INSERT INTO viewed
                                    VALUES ("new",
                                    ?,
                                    datetime('now', 'localtime'),
                                    null)
                                    """, (media_info,))

                return

        self.cursor.execute("""
                            UPDATE viewed
                            SET date_played = datetime('now', 'localtime')
                            WHERE media_directory = ?
                            AND media_info = ?
                            """, (media_directory,
                                  media_info))

    def update_media_elapsed(self, media_directory, media_info, time_viewed):
        self.cursor.execute("""
                            UPDATE viewed
                            SET time_viewed = ?
                            WHERE media_directory = ?
                            AND media_info = ?
                            """, (time_viewed,
                                  media_directory,
                                  media_info))

    def select_new(self, media_info):
        self.cursor.execute("""
                            SELECT date_played,
                            time_viewed
                            FROM viewed
                            WHERE media_directory = "new"
                            AND media_info = ? 
                            """, (media_info,))

        row = self.cursor.fetchone()

        # Not all New media will have a database entry yet.
        try:
            date_played = row["date_played"]
            time_viewed = row["time_viewed"]

        except TypeError:
            date_played = None
            time_viewed = None

        data = {"date_played": date_played,
                "time_viewed": time_viewed}

        return data

    def select_disc(self, media_info):
        date_played = None
        time_viewed = None

        data = {"date_played": date_played,
                "time_viewed": time_viewed}

        return data

    def select_film(self, media_info):
        self.cursor.execute("""
                            SELECT title,
                            director,
                            year,
                            extension,
                            viewed.date_played,
                            viewed.time_viewed
                            FROM film
                            LEFT OUTER JOIN viewed
                            ON (film.id = viewed.media_info)
                            WHERE viewed.media_directory = "film"
                            AND id = ?
                            """, (media_info,))

        row = self.cursor.fetchone()

        try:
            # 'title' and 'director' are decoded for UTF-8.
            row["title"]    = self.decode_string(row["title"])
            row["director"] = self.decode_string(row["director"])

        except TypeError:
            row = {}

        return row

    def select_television(self, media_info):
        self.cursor.execute("""
                            SELECT title,
                            show,
                            year,
                            season,
                            episode,
                            extension,
                            viewed.date_played,
                            viewed.time_viewed
                            FROM television
                            LEFT OUTER JOIN viewed
                            ON (television.id = viewed.media_info)
                            WHERE viewed.media_directory = "television"
                            AND id = ?
                            """, (media_info,))

        row = self.cursor.fetchone()

        try:
            # 'season' and 'episode' also return two padded versions.
            row["title"]          = self.decode_string(row["title"])
            row["show"]           = self.decode_string(row["show"])
            row["season_padded"]  = str(row["season"]).zfill(2)
            row["episode_padded"] = str(row["episode"]).zfill(2)

        except TypeError:
            row = {}

        return row

    def select_films(self, term):
        data = []

        self.cursor.execute("""
                            SELECT id as media_info,
                            title,
                            director,
                            year,
                            extension
                            FROM film
                            WHERE title like ?
                            OR title_clean like ?
                            OR director like ?
                            OR director_clean like ?
                            ORDER BY title asc
                            """, (term,
                                  term,
                                  term,
                                  term))

        rows = self.cursor.fetchall()

        for row in rows:
            row["directory"] = "Film"
            row["title"]     = self.decode_string(row["title"])
            row["director"]  = self.decode_string(row["director"])

            data.append(row)

        return data

    def select_shows(self):
        data = []

        self.cursor.execute("""
                            SELECT show,
                            year
                            FROM television
                            GROUP BY show
                            ORDER BY show asc
                            """)

        rows = self.cursor.fetchall()

        for row in rows:
            row["show"] = self.decode_string(row["show"])

            data.append(row)

        return data

    def select_seasons(self, show):
        self.cursor.execute("""
                            SELECT season
                            FROM television
                            WHERE show = ?
                            GROUP BY season
                            ORDER BY season asc
                            """, (show,))

        return self.cursor.fetchall()

    def select_episodes(self, show, season):
        data = []

        self.cursor.execute("""
                            SELECT id as media_info,
                            episode,
                            title
                            FROM television
                            WHERE show = ?
                            AND season = ?
                            GROUP BY episode, title
                            ORDER BY episode asc
                            """, (show,
                                  season))

        rows = self.cursor.fetchall()

        for row in rows:
            row["title"] = self.decode_string(row["title"])

            data.append(row)

        return data

    def select_all_episodes(self):
        data = []

        self.cursor.execute("""
                            SELECT id as media_info,
                            title,
                            show,
                            year,
                            season,
                            episode,
                            extension
                            FROM television
                            """)

        rows = self.cursor.fetchall()

        for row in rows:
            row["directory"]      = "Television"
            row["title"]          = self.decode_string(row["title"])
            row["show"]           = self.decode_string(row["show"])
            row["season_padded"]  = str(row["season"]).zfill(2)
            row["episode_padded"] = str(row["episode"]).zfill(2)

            data.append(row)

        return data

    def check_film(self, data):
        """Checks to see if a Film is already in the database. If it is, no
        sense in adding it again.

        """

        found = True

        if data["title"]:
            info = (data["title_clean"],
                    data["director_clean"],
                    data["year"],
                    data["extension"])

            self.cursor.execute("""
                                SELECT id
                                FROM film
                                WHERE title_clean = ?
                                AND director_clean = ?
                                AND year = ?
                                AND extension = ?
                                """, info)

            row = self.cursor.fetchone()

            try:
                row["id"]

            except TypeError:
                found = False

        return found

    def check_television(self, data):
        found = True

        if data["title"]:
            info = (data["title"],
                    data["show"],
                    data["year"],
                    data["season"],
                    data["episode"],
                    data["extension"])

            self.cursor.execute("""
                                SELECT id
                                FROM television
                                WHERE title = ?
                                AND show = ?
                                AND year = ?                               
                                AND season = ?
                                AND episode = ?
                                AND extension = ?
                                """, info)

            row = self.cursor.fetchone()

            try:
                row["id"]

            except TypeError:
                found = False

        return found

    def insert_viewed(self, media_directory):
        """When media is inserted into its directory table (Film, etc), it
        is also entered into the Viewed table with a matching ID, to allow
        for later joining.

        """

        self.cursor.execute("""
                            SELECT last_insert_rowid() as id
                            """)

        row = self.cursor.fetchone()

        self.cursor.execute("""
                            INSERT INTO viewed
                            VALUES (?, ?,
                            null, null)
                            """, (media_directory,
                                  row["id"]))

    def insert_film(self, data):
        info = (data["title"],
                data["title_clean"],
                data["director"],
                data["director_clean"],
                data["year"],
                data["extension"])

        self.cursor.execute("""
                            INSERT INTO film
                            VALUES (null,
                            ?, ?, ?, ?, ?, ?,
                            datetime('now', 'localtime'))
                            """, info)

        # Make an entry in the Viewed table too.
        self.insert_viewed("film")

    def insert_television(self, data):
        if data["title"]:
            info = (data["title"],
                    data["show"],
                    data["year"],
                    data["season"],
                    data["episode"],
                    data["extension"])

            self.cursor.execute("""
                                INSERT INTO television
                                VALUES (null,
                                ?, ?, ?, ?, ?, ?,
                                datetime('now', 'localtime'))
                                """, info)

            self.insert_viewed("television")

    def insert_music(self, data):
        # Not yet implemented.
        print data["title"]

    def delete_film(self, data):
        info = (data["title"],
                data["director"],
                data["year"],
                data["extension"])

        self.cursor.execute("""
                            DELETE FROM film
                            WHERE title = ?
                            AND director = ?
                            AND year = ?
                            AND extension = ?
                            """, info)

    def delete_television(self, data):
        if data["title"]:
            info = (data["title"],
                    data["show"],
                    data["year"],
                    data["season"],
                    data["episode"],
                    data["extension"])

            self.cursor.execute("""
                                DELETE FROM television
                                WHERE title = ?
                                AND show = ?
                                AND year = ?
                                AND season = ?
                                AND episode = ?
                                AND extension = ?
                                """, info)

    def delete_music(self, data):
        # Not yet implemented.
        print data["title"]

