#!/usr/bin/env python
"""Indexer: Part of Medusa (MEDia USage Assistant), by Stephen Smart.

The Indexer traverses the specified directories (Film, Television, etc)
inside the Source mount in search of media files that match the file
extension criteria, as specified in the configger.

It then indexes found media into the database following a naming convention,
and removes database entries that no longer exist on the harddrive.
"""

from os import path
from re import sub
import argparse

from medusa import (logger as log,
                    lister,
                    databaser)

# Initialize naming import.
#------------------------------------------------------------------------------

naming = lister.Naming()

# Parse command-line arguments.
#------------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--directories",
                        action = "append", required = True,
                        help = "Film, Television, Music, etc.")
    # This path is taken as Unicode to support foreign characters.
    parser.add_argument("-s", "--source_mount",
                        action = "store", type = unicode, required = True)

    return parser.parse_args()

# Main.
#------------------------------------------------------------------------------

def main():
    """List directories and add new files to the database.

    Then check for database entries that no longer exist on the harddrive and
    delete them.
    """

    options = parse_arguments()

    database = databaser.Database()

    index = Index(options, database)

    for drc in options.directories:
        # Get the full path to the directory.
        directory = path.join(options.source_mount, drc)

        # Get a list of all files contained within the directory.
        listing = lister.Listing()
        listing.list_directories_recursive([directory])

        # And add them to the database if not already found.
        index.index_all(listing.files)

        # Find indexed media that no longer exists on disk.
        delete_list = get_deleted_media(database, directory, listing.files)

        # And delete it from the database.
        index.delete_all(delete_list)

def get_deleted_media(database, directory, files):
    delete_list   = []
    indexed_media = []

    with database:
        # Get a list of all media for the directory.
        if "Film" in directory:
            data = database.select_films("%%")

            for film in data:
                # Format the media to the naming convention.
                media = naming.build_film_path(film).replace("Film/", "")

                indexed_media.append(media)

        elif "Television" in directory:
            data = database.select_all_episodes()

            for episode in data:
                media = naming.build_episode_path(episode).replace("Television/", "")

                indexed_media.append(media)

    # Strip the 'Part' part out, as the database entries don't use it.
    files = [sub("Part \d* - ", "", fle) for fle in files]

    for media in indexed_media:
        media_file = path.join(directory, media)

        if media_file not in files:
            # Media not found on disk, so we should delete it.
            delete_list.append(media_file)

    return delete_list

# The Indexer.
#------------------------------------------------------------------------------

class Index(object):
    """Insert and Delete media into/from the database."""

    def __init__(self, options, database):
        """Receive the command-line options and database connection."""

        self.options = options

        self.database = database

        # Used to check extensions and match to file naming conventions.
        self.naming = lister.Naming()

    def index_all(self, index_list):
        """Insert all media in the index list into the database, unless
        it already exists in the database.
        """

        with self.database:
            for fle in index_list:
                # The directory (e.g. Film) determines the database table.
                directory = self.check_directory(fle)

                for drc in self.options.directories:
                    # Make sure we only operate on the user given directories.
                    if directory == drc:
                        # File system can be upper case, but database is lower.
                        directory = directory.lower()

                        # Parse the file name to get a useful dictionary.
                        _query = "parse_" + directory + "_name"

                        data = getattr(self.naming, _query)(fle)

                        # Check if it is there already, and if not, insert it!
                        if not getattr(self.database,
                                       "check_" + directory)(data):
                            getattr(self.database, "insert_" + directory)(data)

                            log.write("Indexer inserted '%s' into '%s' database." \
                                      % (data["title"], directory))

    def delete_all(self, delete_list):
        """Delete all media in the delete list from the database."""

        with self.database:
            for fle in delete_list:
                directory = self.check_directory(fle)

                for drc in self.options.directories:
                    if directory == drc:
                        directory = directory.lower()

                        data = getattr(self.naming, "parse_" + directory + "_name")(fle)

                        # Check it is there first, and if it is... delete.
                        if getattr(self.database,
                                   "check_" + directory)(data):
                            getattr(self.database, "delete_" + directory)(data)

                            log.write("Indexer deleted '%s' from '%s' database." \
                                      % (data["title"], directory))

    def check_directory(self, directory):
        """Check that the directory is one that was passed by the user."""

        for drc in self.options.directories:
            if path.join(self.options.source_mount, drc) in directory:
                return drc

# Run.
#------------------------------------------------------------------------------

if __name__ == "__main__":
    log.write("Indexer launched.")

    main()

    log.write("Indexer exited.")

