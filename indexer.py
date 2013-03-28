#!/usr/bin/env python
"""Indexer: Part of Medusa (MEDia USage Assistant), by Stephen Smart.

The Indexer traverses the specified directories (Film, Television, etc)
inside the Source mount in search of media files that match the file
extension criteria, as specified in the configger.

It then indexes found media into the database following a naming convention,
and removes database entries that no longer exist on the harddrive.
"""

import argparse

from medusa import (logger as log,
                    lister,
                    databaser)

# Parse command-line arguments.
#------------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--directories",
                        action = "append", required = True,
                        help = "Film, Television, or Music.")
    # The path is taken as Unicode to support foreign characters.
    parser.add_argument("-s", "--source_mount",
                        action = "store", type = unicode, required = True)

    return parser.parse_args()

# Main.
#------------------------------------------------------------------------------

def main():
    """Parses command-line arguments. Lists directories and adds new files to
    the database. Checks for database entries that no longer exist on the
    harddrive and deletes them.
    """

    options = parse_arguments()

    database = databaser.Database()

    index = Index(options, database)

    for drc in options.directories:
        # Get the full path to the directory.
        directory = options.source_mount + "/" + drc

        listing = lister.Listing()

        # And list all files in it.
        listing.list_directories_recursive([directory])

        index.index_all(listing.files)

# The Indexer.
#------------------------------------------------------------------------------

class Index(object):
    """Inserts and Deletes media into/from the database."""

    def __init__(self, options, database):
        """Receives the command-line options and database connection."""

        self.options = options

        self.database = database

        # Used to check extensions and match file naming convention.
        self.naming = lister.Naming()

    def index_all(self, index_list):
        """Inserts all media in the index list into the database, unless
        it already exists in the database.
        """

        with self.database:
            for fle in index_list:
                # The directory (e.g. Film) determines the database table.
                directory = self.check_directory(fle)

                for drc in self.options.directories:
                    if directory == drc:
                        # File system is upper case, database is lower.
                        directory = directory.lower()

                        # Parse the file name to get a useful dictionary.
                        _query = "parse_" + directory + "_name"

                        data = getattr(self.naming, _query)(fle)

                        # Check it is there already, if not: add it.
                        if not getattr(self.database,
                                       "check_" + directory)(data):
                            getattr(self.database, "insert_" + directory)(data)

    def delete_all(self, delete_list):
        """Deletes all media in the delete list from the database."""

        with self.database:
            for fle in delete_list:
                directory = self.check_directory(fle)

                for drc in self.options.directories:
                    if directory == drc:
                        directory = directory.lower()

                        data = getattr(self.naming, "parse_" + directory)(fle)

                        # Check it is there first, if it is, delete.
                        if getattr(self.database,
                                   "check_" + directory)(data):
                            getattr(self.database,
                                    "delete_" + directory)(data)

    def check_directory(self, directory):
        """Checks that the directory is one that was passed by the user."""

        for drc in self.options.directories:
            if "%s/%s/" % (self.options.source_mount, drc) in directory:
                return drc

# Run.
#------------------------------------------------------------------------------

if __name__ == "__main__":
    log.write("Indexer launched.")

    main()

    log.write("Indexer exited.")

