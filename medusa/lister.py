"""Part of Medusa (MEDia USage Assistant).

Provides recursive directory listings which are filtered for specific
media extensions, as specified in the Configger.

"""

from os import path, listdir
import re
import unicodedata
from itertools import ifilter

import configger as config

class Listing(object):
    def __init__(self):
        self.files = set()

    def list_directory(self, directory):
        # Ignore hidden files.
        for f in filter(lambda x: not x.startswith("."), listdir(directory)):
            # And ignore files in the ignore list.
            if f not in config.ignore_files:
                yield "%s/%s" % (directory, f)                     

    def list_directories_recursive(self, paths):
        for p in ifilter(None, paths):
            if path.isdir(p):
                for f in self.list_directory(p):
                    if path.isdir(f):
                        self.list_directories_recursive({f})

                    else:
                        self.files.add(f)

            else:
                self.files.add(p)

class Naming(object):
    def __init__(self):
        pass

    def clean_string(self, string):
        """Normalizes Unicode data to create a clean database entry."""

        string_split = []

        for c in unicodedata.normalize("NFD", string):
            if unicodedata.category(c) != "Mn":
                string_split.append(c)

        string = "".join(string_split)

        return string

    def check_video_extension(self, extension):
        if extension.lower() in config.video_extensions:
            return True

        return False

    def check_audio_extension(self, extension):
        if extension.lower() in config.audio_extensions:
            return True

        return False

    def parse_film_name(self, film):
        """Parses a Film file name to get information ready for the database.

        The naming convention is:

        {Title} ({Year}) - {Director}.{Extension}

        or:

        {Title} ({Year}) - Part 1 - {Director}.{Extension}

        """

        data = dict.fromkeys(("title",
                              "title_clean",
                              "director",
                              "director_clean",
                              "year",
                              "extension"),
                              False)

        # Can't do much with raw DVDs.
        if "VIDEO_TS" in film:
            return data

        filename, extension = path.splitext(path.basename(film))

        extension = extension.strip(".")

        # Pull the year out.
        match = re.search("\(\d{4}\) - ", filename)
        year = match.group(0)

        filename = filename.split(year)

        # Get rid of the 'Part' part.
        if "Part " in filename[1]:
            filename[1] = re.sub("Part \d* - ", "", filename[1])

        if self.check_video_extension(extension):
            data["title"] = filename[0].strip()
            data["title_clean"] = self.clean_string(data["title"])
            data["director"] = filename[1].strip(" - ")
            data["director_clean"] = self.clean_string(data["director"])
            data["year"] = year.strip("(").strip(") - ")
            data["extension"] = extension

        return data

    def parse_television_name(self, episode):
        """Parses a Television episode file name to get information ready
        for the database.

        The naming convention is:

        {Show} ({Year})/S{Season}/{Show} - {Episode} - {Title}.{Extension}

        """

        # Get us started with the keys but no values.
        data = dict.fromkeys(("title",
                              "show",
                              "year",
                              "season",
                              "episode",
                              "extension"),
                              False)

        # Pull out the year.
        match = re.search("\(\d{4}\)", episode)
        year = match.group(0).strip("(").strip(")")

        # And then the season.
        match = re.search("\/S\d\d\/", episode)
        season = match.group(0).strip("/S").strip("/")

        filename, extension = path.splitext(path.basename(episode))

        filename = filename.split(" - ")

        extension = extension.strip(".")

        if self.check_video_extension(extension):
            data["title"] = " - ".join(filename[2:])
            data["show"] = filename[0]
            data["year"] = year
            data["season"]  = season
            data["episode"] = filename[1]
            data["extension"] = extension

        return data

    def build_new_path(self, media_info, downloads_mount, temporary_mount):
        """Returns the full file path to a New media file."""

        media_file = ""

        listing = Listing()

        # If neither optional mounts are provided, this will be empty.
        listing.list_directories_recursive([downloads_mount,
                                            temporary_mount])

        for f in listing.files:
            if media_info in f:
                # Prepend the directory to the file information.
                if "Completed" in f:
                    f = f.replace(downloads_mount, "")

                    media_file = "Downloads-" + f

                elif "Brothel" in f:
                    f = f.replace(temporary_mount, "")

                    media_file = "Temporary-" + f

                break

        return media_file

    def build_film_path(self, data):
        """Returns the file path to a Film."""

        media_directory = path.join(data["directory"].title(), data["title"])

        media_base = "%s (%s) - %s.%s" % (data["title"],
                                          data["year"],
                                          data["director"],
                                          data["extension"])

        return path.join(media_directory, media_base)

    def build_episode_path(self, data):
        """Returns the file path to a Television episode."""

        show   = "%s (%s)" % (data["show"], data["year"])
        season = "S%s" % data["season_padded"]

        media_directory = path.join(data["directory"].title(), show, season)
 
        media_base = "%s - %s - %s.%s" % (data["show"],
                                          data["episode_padded"],
                                          data["title"],
                                          data["extension"])           

        return path.join(media_directory, media_base)
