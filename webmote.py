#!/usr/bin/env python

"""
Webmote: Part of Medusa (MEDia USage Assistant), by Stephen Smart.

The Webmote provides a web interface which is designed for use on
devices ranging from desktop computers to mobile phones.

It uses the Werkzeug based microframework Flask to route pages which are
served on a Gevent WSGI server.

Through this interface the user is able to browse all of their database
indexed media in addition to a dynamically generated listing of new and
temporarily downloaded/stored media files.

Media playback can be started and controlled through the web interface. The
Webmote communicates user requests through to the appropriate Receiver using
socket connections. The playback's elapsed time is updated to the browser
through a WebSocket.

Paths to the Downloads and Temporary directories can be optionally passed
through using '-d' and '-t' command-line arguments.

Currently supports Film and Television directories, with Music not yet
implemented. All directories are handled separately due to their discrepant
file naming schemes and folder structures.
"""

import os.path
from time import (strptime,
                  strftime)
import argparse

import simplejson as json
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from gevent import sleep as gevent_sleep
import flask

from medusa import (configger as config,
                    logger as log,
                    lister,
                    databaser,
                    communicator)

#------------------------------------------------------------------------------

web = flask.Flask(__name__,
                  static_folder=config.static_folder,
                  template_folder=config.template_folder)

#------------------------------------------------------------------------------

naming = lister.Naming()
database = databaser.Database()
communicate = communicator.Communicate()

#------------------------------------------------------------------------------

def main():
    """Check Receivers, launch web server."""

    log.write("Checking Receivers.")

    with database:
        receivers = database.select_receivers()

    check_alive_receivers(receivers)

    log.write("Starting web server.")

    # Run the web server using Gevent with a WebSocket handler available.
    #
    server = WSGIServer((config.webmote_ip, config.webmote_port),
                        web,
                        handler_class=WebSocketHandler,
                        log=log)
    server.serve_forever()

#------------------------------------------------------------------------------

def check_alive_receivers(receivers):
    """
    Check to make sure that all Receivers passed through will respond to
    a socket communication request. If the request fails, clear the database
    entry.

    Return a list of all alive (responding) Receivers.
    """

    if not receivers:
        return []

    alive_receivers = []

    for rcv in receivers:
        try:
            communicate.receiver_hostname = rcv["host"]

            with communicate:
                communicate.send("get_status")

                # The content of the status check is not important.
                communicate.receive()

            alive_receivers.append(rcv)

        except IOError as error:
            log.error("Clearing dead Receiver '%s': %s." % (rcv["host"], error))

            # This removes the Receiver database entry entirely.
            api("delete", rcv["host"])

    return alive_receivers

def count_active_receivers():
    """
    Return a count of how many Receivers are listed as being active
    (having media loaded) in the database.

    The returned Receiver hostname is only relevant when the active Receiver
    count is one. Otherwise it is never used.
    """

    active_count = 0

    active_receiver = None

    with database:
        # Get all alive Receivers.
        receivers = database.select_receivers()

        for rcv in receivers:
            # Get status information for the Receiver.
            info = database.select_receiver(rcv["host"])

            # A not null status (e.g. 'playing') indicates active media.
            #
            if info["status"]:
                active_count += 1

                # Store this in case only one is active, so we can redirect.
                active_receiver = rcv["host"]

    return active_count, active_receiver

def begin_playing_receiver(receiver, directory, media_info):
    """
    Update the database for a Receiver with information on the newly
    playing media, and update the play time history for that media.
    """

    database.update_receiver_media(receiver, directory, media_info)

    database.update_receiver_status(receiver, "playing")

    # Updates the last played time stamp for the media.
    database.update_media_played(directory, media_info)

    database.update_media_elapsed(directory, media_info, 0)

def clear_receiver(receiver):
    """
    Clear the Receiver's active status from the Receiver database by
    updating it to have empty entries in the relevant columns.
    """

    database.update_receiver_media(receiver, "", "")

    database.update_receiver_status(receiver, "")

def format_time(time):
    """Convert the time into a user friendly string."""

    return strptime(time, "%Y-%m-%d %H:%M:%S")

#------------------------------------------------------------------------------

@web.route("/api/<receiver>/<action>")
@web.route("/api/<receiver>/<action>/<option>")
def api(action, receiver, option=None):
    """
    An HTTP API which is used (mainly) by Receivers to update the database
    with their status, such as when they are launched, finish media playback,
    or exit.

    Receivers therefore do not require direct database access.
    """

    with database:
        if action == "insert":
            if not database.check_receiver(receiver):
                database.insert_receiver(receiver, option)

            else:
                clear_receiver(receiver)

        if action == "delete":
            database.delete_receiver(receiver)

        if action == "stop":
            clear_receiver(receiver)

        if action == "begin":
            option = option.partition("-")

            begin_playing_receiver(receiver, option[0], option[2])

    # The returned string is ignored, but cannot be null.
    return "0"

@web.route("/")
def index_page():
    """
    Return a redirect from the Index page.

    If a single Receiver is active, redirect to its Playing (control) page.
    If multiple Receivers are active, redirect to the Receiver page to choose.
    If no Receivers are active, redirect to the Browse page.
    """

    bookmark = False

    if bookmark:
        return flask.render_template("browse.html", directory=None)

    active_count, active_receiver = count_active_receivers()

    if active_count == 1:
        return flask.redirect("/playing/" + active_receiver)

    elif active_count > 1:
        return flask.redirect("/playing")

    else:
        return flask.redirect("/browse")

@web.route("/browse")
@web.route("/browse/<directory>")
def browse_page(directory=None):
    """
    Return the Browse page.

    The Browse page is a shell for holding the results returned from the
    Search page, which is requested by JQuery on page load or live search.

    Contains variables such as directory (Film, New, etc) or
    sub-directory (Show, Artist, etc). This is to help the page request and
    format its dynamic content.
    """

    return flask.render_template("browse.html", directory=directory)

@web.route("/browse/television/<show>")
@web.route("/browse/television/<show>/<season>")
def browse_television_page(show, season=None):
    """Return the Browse page for a Television sub-directory."""

    return flask.render_template("browse.html", directory="television",
                                 show=show, season=season)

@web.route("/browse/music/<artist>")
@web.route("/browse/music/<artist>/<album>")
def browse_music_page(artist, album=None):
    """Return the Browse page for a Music sub-directory."""

    return flask.render_template("browse.html", directory="music",
                                 artist=artist, album = album)

@web.route("/new")
def new_page():
    """
    Return a redirect to the Browse New page.

    This exists for URL naming convention consistency.
    """

    return flask.redirect("/browse/new")

@web.route("/search")
def search_page():
    """
    Return the default Search page.

    This displays a list of base directories (Film, Television, etc), which
    are hard-coded into the HTML at present.
    """

    return flask.render_template("search.html")

@web.route("/search/new")
def search_new_page():
    """
    Return the Search New result page.

    Contains a combined file listing of the Downloads and Temporary
    directories, assuming they have been given as command-line arguments.

    This is neither cached nor indexed. The intent is to provide a way for
    the user to play media before it has been moved and entered into the
    database.

    The list is ordered by file modified time, with the latest appearing
    at the top.

    Not yet implemented: Limit files to only those modified in the last three
    days, and include media entered into the database within the last three days.
    """

    data = []

    listing = lister.Listing()

    listing.list_directories_recursive((options.downloads_mount,
                                        options.temporary_mount))

    for fle in listing.files:
        modified_time = os.path.getmtime(fle)

        filename = os.path.basename(fle)

        extension = os.path.splitext(filename)[1].strip(".")

        # Checks the file extension to make sure it fits our media criteria.
        #
        if naming.check_video_extension(extension):
            data.append((modified_time, filename))

    data.sort(reverse=True)

    return flask.render_template("search.html", directory="new", data=data)

@web.route("/search/film")
@web.route("/search/film/<term>")
def search_film_page(term=""):
    """
    Return the Search Film result page.

    Contains a full or partial list of all Films in the database.

    If a search term is provided, filter by it.

    The HTML page knows how to format the columns correctly straight from the
    database.
    """

    data = []

    # Select all database entries by using a wild card.
    if not term.strip():
        term = "%%"

    # Otherwise filter the selection by a search term + wild card.
    else:
        term = "%s%%" % (term)

    with database:
        data = database.select_films(term)

    return flask.render_template("search.html", directory="film", data=data)

@web.route("/search/television")
@web.route("/search/television/<show>")
@web.route("/search/television/<show>/<season>")
def search_television_page(show=None, season=None):
    """
    Return the Search Television result page.

    Contains a full list of shows, seasons or episodes, depending on
    which level of sub-directory the user has browsed to.
    """

    data = []

    with database:
        if show and season:
            data = database.select_episodes(show, season)

        elif show:
            data = database.select_seasons(show)

        else:
            data = database.select_shows()

    return flask.render_template("search.html", directory="television",
                                 show=show, season=season, data=data)

@web.route("/search/music")
@web.route("/search/music/<artist>")
@web.route("/search/music/<artist>/<album>")
def search_music_page(artist=None, album=None):
    """
    Return the Search Music result page.

    Feature not yet implemented.
    """

    data = []

    return flask.render_template("search.html", directory="music",
                                 artist=artist, album=album, data=data)

@web.route("/info/<directory>/<media_info>")
def info_page(directory, media_info):
    """
    Return the Media Info page.

    Contains all databased information on a certain media file, and a
    list of alive Receivers.

    This page presents the option to begin playback on a chosen Receiver.
    It also shows when the media was last played, and if it can be resumed.

    In the case of New media the only information gathered is the already
    passed title and if it has been played before.
    """

    data = {}
    receivers = []

    with database:
        receivers = database.select_receivers()

        # The directory (e.g. Film) tells us which table to select from.
        _query = "select_%s" % (directory)

        data = getattr(database, _query)(media_info)

        if data["date_played"]:
            date_played = format_time(data["date_played"])

            data["date_played"] = strftime("%B %d, %Y", date_played)

    # Add the 'media_info' identifier to the 'data' dictionary to be returned.
    data["media_info"] = media_info

    return flask.render_template("info.html", directory=directory, data=data,
                                 receivers=receivers)

@web.route("/playing")
@web.route("/playing/<receiver>")
def playing_page(receiver=None):
    """
    Return the Playing page.

    If there is only one active Receiver, redirect to its Playing page.
    Otherwise return a list of active Receivers to choose from.

    The Playing page for an active Receiver allows the user to monitor and
    control media playback.

    For a New media file, 'media_info' is the filename. For indexed media
    files it is the database entry ID.
    """

    directory = None
    data = None
    receivers = None
    active = False

    # We have a Receiver, look up its active media.
    if receiver:
        data = {}

        with database:
            info = database.select_receiver(receiver)

            directory = info["directory"]

            # If 'directory' is null, playback must have ended.
            if not directory:
                return flask.redirect("/browse")

            # Do not query database for New files, they are not indexed.
            #
            if directory != "new":
                _query = "select_%s" % (directory)

                data = getattr(database, _query)(info["media_info"])

            # Instead just carry across the already gathered 'media_info'.
            else:
                data["media_info"] = info["media_info"]

            # Add the Receiver status to the 'data' dictionary to be returned.
            data["status"] = info["status"]

    # If there is no Receiver specified, prepare a list of active Receivers.
    #
    else:
        # 'active_receiver' is not used in this instance.
        active_count, active_receiver = count_active_receivers()

        if active_count == 1:
            return flask.redirect("/playing/" + active_receiver)

        # The HTML page knows what to do if 'active' is false.
        elif active_count > 1:
            active = True

        receivers_active = []

        with database:
            # Get all Receivers, regardless of status.
            receivers = database.select_receivers()

            for rcv in receivers:
                info = database.select_receiver(rcv["host"])

                rcv["status"] = info["status"]

                # If 'status' is not null, the Receiver must be active.
                if rcv["status"]:
                    receivers_active.append(rcv)

            # Now we have a list of active Receivers only.
            receivers = receivers_active

    return flask.render_template("playing.html", receiver=receiver,
                                 directory=directory, data=data,
                                 receivers=receivers, active=active)

@web.route("/playing/<receiver>/<directory>/<media_info>")
def playing_start_page(receiver, directory, media_info):
    """
    Update the database for the Receiver with the basic media information,
    and set the duration elapsed for the media to 0.

    Build the filename of the selected media from its database entry. If it
    is a New file, 'media_info' is already the filename, so only the
    directory needs to be appended, so the Receiver will know where to look.

    Check to see if the media has been played before and has a partial
    elapsed time. If so, passes that information along to the Receiver.

    Communicate the 'play' action along with the filename and elapsed time
    through to the selected Receiver as a tuple in a tuple.

    Return a redirect to the Receiver Playing page to begin monitoring.
    """

    with database:
        # Select all media information from the database to build filename.
        _query = "select_%s" % (directory)

        data = getattr(database, _query)(media_info)

    data["directory"] = directory

    # New files require a filesystem browse, rather than database select.
    #
    if directory == "new":
        media_file = naming.build_new_path(media_info, options.downloads_mount,
                                           options.temporary_mount)

    # Build the media filename based on the below naming conventions.
    #
    elif directory == "film":
        media_file = naming.build_film_path(data)

    elif directory == "television":
        media_file = naming.build_episode_path(data)

    elif directory == "disc":
	media_file = "disc"

    # The action to send through that tells the Receiver to begin playback.
    action = "play"

    # 'time_viewed' indicates resume functionality for partial viewings.
    #
    if data["time_viewed"]:
        time_viewed = data["time_viewed"]

    else:
        time_viewed = None

    # Bundle the file path and viewed time into a tuple for sending.
    media = (media_file, time_viewed, directory, media_info)

    communicate.receiver_hostname = receiver

    with communicate:
        communicate.send((action, media))

    return flask.redirect("/playing/%s" % (receiver))

@web.route("/playing/time/<receiver>")
def playing_time_page(receiver):
    """
    Provide a browser with the currently elapsed time through a WebSocket.

    Subscribe to the Receiver's Watcher process for updates.

    This allows for live monitoring of media playback on the Playing page.
    """

    web_socket = flask.request.environ.get("wsgi.websocket")

    communicate.receiver_hostname = receiver

    # Get the current status to display immediately.
    #
    with communicate:
        communicate.send("get_status")

        try:
            state, time_elapsed, time_total = communicate.receive()

        except Exception as excp:
            state = "Unknown"
            time_elapsed = 0
            time_total = 0

        # Convert from seconds to whole minutes.
        time_elapsed = int(round(int(time_elapsed) / 60))
        time_total = int(round(int(time_total) / 60))

    # Subscribe to status updates from the Receiver.
    subscribe = communicator.Subscribe(receiver)

    # Loop waiting for status updates.
    #
    while True:
        if not web_socket:
            log.error("WebSocket not found.")

            break

        message = {"time_elapsed": time_elapsed, "time_total": time_total}

        try:
            if state != "Opening":
                # Send the message as JSON.
                web_socket.send(json.dumps(message))

        except Exception as excp:
            log.error("Failed to send to WebSocket: %s" % excp)

            break

        log.write("Sent elapsed time (%s minutes) to WebSocket." % time_elapsed)

        if state == "opped":
            # If playback has ended, abandon the socket.
            break

        # Wait for an update.
        state, time_elapsed, time_total = subscribe.receive()

    subscribe.close_socket()

    return "0"

@web.route("/playing/tracks/<receiver>/<track_selection>")
def playing_tracks_page(receiver, track_selection):
    """
    Return the Playing Tracks page.

    Contains a list of either all audio or all subtitle tracks. It is
    requested by JQuery and allows the user to change tracks inside the
    Playing page.
    """

    tracks = []

    # The action can be to get either audio or subtitle tracks.
    action = "get_%s_tracks" % (track_selection)

    communicate.receiver_hostname = receiver

    with communicate:
        communicate.send(action)

        data = communicate.receive()

    i = 0

    for trc in data:
        # Ignore the 'disable' audio track, we have mute for that.
        #
        if (track_selection == "audio") and (trc[1] == "Disable"):
            i += 1

            continue

        if trc != "null":
            tracks.append((i, trc[1]))

            # Record the track ID, as it isn't provided by the VLC API.
            i += 1

    return flask.render_template("tracks.html", receiver=receiver,
                                 track_selection=track_selection,
                                 tracks=tracks)

@web.route("/action/<receiver>/<action>")
@web.route("/action/<receiver>/<action>/<option>")
def playing_action_page(receiver, action, option=None):
    """
    Return a redirect to the Receiver Playing page, or Browse page in the
    case of playback having ended.

    Available controls/actions include play, pause, stop, rewind, mute,
    volume, subtitles, audio track, and status.

    If a 'stop' action is received, clear the Receiver database entry and
    determine if the media is eligible for resuming. This means at least 120
    seconds must have elapsed, and more than five percent of playback remains.
    The goal here is to avoid files resuming when they have reached their
    end credit sequence, or only just begun.
    """

    communicate.receiver_hostname = receiver

    with database:
        data = database.select_receiver(receiver)

        if action == "stop":
            clear_receiver(receiver)

            # Check for resume eligibility.
            #
            with communicate:
                communicate.send("get_status")

                state, time_elapsed, time_total = communicate.receive()

            time_remaining = int(time_total) - int(time_elapsed)

            time_five_percent = int(time_total) * 0.05

            if int(time_elapsed) > 120:
                if time_remaining > time_five_percent:
                    database.update_media_elapsed(data["directory"],
                                                  data["media_info"],
                                                  time_elapsed)

        # When already paused: unpause. Updates database accordingly.
        #
        elif action == "pause":
            if data["status"] == "playing":
                database.update_receiver_status(receiver, "paused")

            else:
                database.update_receiver_status(receiver, "playing")

    # Sends the action as a two value tuple.
    with communicate:
        communicate.send((action, option))

    # Playback has ended, so redirect to the Browse page instead.
    if action == "stop":
        redirect_url = "/browse"

    else:
        redirect_url = "/playing/%s" % (receiver)

    return flask.redirect(redirect_url)

@web.route("/viewed")
def viewed_page():
    """
    Return the Viewed page.

    Contains a short list of the most recently played media.
    """

    data = []

    with database:
        viewed_media = database.select_viewed_media()

        for mda in viewed_media:
            # New media uses its filename as the title.
            if mda["media_directory"] == "new":
                title = mda["media_info"]

            # Indexed media builds a more user friendly title.
            else:
                _query = "select_%s" % (mda["media_directory"])

                info = getattr(database, _query)(mda["media_info"])

                if mda["media_directory"] == "film":
                    title = "%s (%s) - %s" % (info["title"], info["year"],
                                              info["director"])

                elif mda["media_directory"] == "television":
                    title = "%s - S%sE%s - %s" % (info["show"],
                                                  info["season_padded"],
                                                  info["episode_padded"],
                                                  info["title"])

            # We need enough information to build a URL to the Info page.
            data.append((mda["media_directory"], mda["media_info"], title))

    return flask.render_template("viewed.html", data=data)

@web.route("/admin")
@web.route("/admin/<receiver>")
def admin_page(receiver=None):
    """
    Return the Admin page.

    Contains information on a Receiver's status, and controls such as
    'restart'.

    Feature not yet complete.
    """

    data = {}
    receivers = []

    with database:
        if receiver:
            data = database.select_receiver(receiver)

        else:
            receivers = database.select_receivers()

    receivers = check_alive_receivers(receivers)

    return flask.render_template("admin.html", receiver=receiver, data=data,
                                 receivers=receivers)

#------------------------------------------------------------------------------

def parse_arguments():
    help = """Launches the Webmote server. Both arguments are optional but
              provide functionality to the 'New' page."""

    parser = argparse.ArgumentParser(description=help)

    parser.add_argument("-d", "--downloads_mount",
                        action="store", type=unicode, default=None)
    parser.add_argument("-t", "--temporary_mount",
                        action="store", type=unicode, default=None)

    return parser.parse_args()

#------------------------------------------------------------------------------

if __name__ == "__main__":
    log.write("Webmote launched.")

    options = parse_arguments()

    main()

    log.write("Webmote exited.")
