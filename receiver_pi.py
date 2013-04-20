#!/usr/bin/env python

"""Receiver: Part of Medusa (MEDia USage Assistant), by Stephen Smart.

Receives instructions from a Webmote and actions them using OMX Player.

This is a stripped down version of the standard Medusa Receiver, designed
specifically for use on the Raspberry Pi. 
"""

import os
import sys
import argparse
import subprocess

import requests

from medusa import (configger as config,
                    logger as log,
                    communicator)

# Initialize communicator import.
#------------------------------------------------------------------------------

communicate = communicator.Communicate()

# Check and set a PID file.
#------------------------------------------------------------------------------

def prepare_pid(process_name):
    """Check for an existing PID file. If not found or not running, write
    out a new PID file for this process.
    """

    pid = str(os.getpid())
    pid_file = "/tmp/%s.pid" % process_name

    if os.path.isfile(pid_file):
        with open(pid_file, "r") as fle:
            old_pid = fle.readline()

        # Check to see if this PID is actually running and not crashed.
        if os.path.exists("/proc/" + old_pid):
            log.write("%s already running. Exiting." % process_name.title())

            sys.exit(0)

        else:
            os.remove(pid_file)

    with open(pid_file, "w") as fle:
        fle.write(pid)

    return pid_file

# Classes.
#------------------------------------------------------------------------------

class Api(object):
    """Communicate with the Webmote's web API."""

    def __init__(self):
        self.base_url = "http://%s:%s/api/" % (options.webmote, config.webmote_port)

    def action(self, action, option = None):
        if action == "begin":
            option = "%s-%s" % (option[0], option[1])

        action_url = "%s/%s/%s" % (config.hostname,
                                   action,
                                   option)

        url = self.base_url + action_url

        requests.get(url)


class Player(object):
    """Control media playback using OMX Player, internally performing actions
    received from the Webmote.
    """

    def __init__(self):
        self.action = ""
        self.option = ""
        self.state = ""
        self.queue = []

        self.media_player = None

        self.receive()

    def receive(self):
        communicate.listen(use_host_ip = False)

        while True:
            action, option = communicate.accept()

            log.write("Received action '%s' and option '%s'." % (action, option))

            self.process((action, option))

    def process(self, received):
        """Process actions received from the Webmote."""

        self.action, self.option = received

        log.write("Performing action '%s'." % (self.action))

        if self.action == "restart":
            # Not yet implemented.
            return

        if self.action == "get_status":
            communicate.reply(("Unknown", 0, 0))

            return

        try:
            # Attempt to perform the received action.
            action_result = getattr(self, self.action)()

            if action_result:
                communicate.reply(action_result)

        except Exception as error:
            log.error("Failed to perform action '%s': %s." % (self.action, error))

    def play(self):
        """Prepare the media, reset the media player, and begin playback."""

        # Make sure any current playback has stopped.
        self.stop()

        # Play the next item in the queue if one exists.
        if self.option == "next":
            if self.queue:
                media_file, directory, media_info = self.queue.pop(0)

                time_viewed = 0

            else:
                log.write("Cannot play next media, queue is empty.")

                return

        else:
            # Get the full path to the media file.
            media_partial, time_viewed, directory, media_info = self.option

            media = Media(directory, media_info)
            media.get_media_file(media_partial)

            self.queue.extend(media.parts)

            media_file = media.media_file

        api.action("begin", (directory, media_info))

        command = ["omxplayer", "-o", "hdmi"]

        if time_viewed:
            command.extend(["-l", str(time_viewed * 1000)])

        command.append(media_file)

        self.media_player = subprocess.Popen(command, stdin=subprocess.PIPE)

    def pause(self):
        self.media_player.stdin.write("p")

    def rewind(self):
        self.media_player.stdin.write("\x1B[D")

    def stop(self):
        if self.media_player:
            self.media_player.stdin.write("q")

            self.media_player.terminate()

            self.media_player = None            

        self.queue = []


class Media(object):
    """Find and format a path to the media file."""

    def __init__(self, directory, media_info):
        self.directory = directory
        self.media_info = media_info
        self.media_file = ""
        self.parts = []

    def get_media_file(self, media_partial):
        if media_partial == "disc":
            return

        media_mount = options.source_mount

        if "Downloads-" in media_partial:
            media_partial = media_partial.strip("Downloads-/")
            media_mount = options.downloads_mount

        if "Temporary-" in media_partial:
            media_partial = media_partial.strip("Temporary-/")
            media_mount = options.temporary_mount

        media_file = os.path.join(media_mount, media_partial)
        self.media_file = os.path.normpath(media_file)

        if not os.path.exists(self.media_file):
            self.find_media_files()

    def find_media_files(self):
        """Find files that are not named as expected. This can happen when
        a media item is split into parts. Each part after the first will
        be added to the queue.
        """

        media_directory = os.path.dirname(self.media_file)

        for fle in os.listdir(media_directory):
            extension = os.path.splitext(fle)[1]
            extension = extension.lstrip(".").lower()

            if extension in config.video_extensions:
                media_path = os.path.join(media_directory, fle)

                if " - Part 1 - " in fle:
                    self.media_file = media_path

                elif " - Part " in fle:
                    self.parts.append((media_path, self.directory, self.media_info))

# Parse command-line arguments.
#------------------------------------------------------------------------------

def parse_arguments():
    help = """The Downloads and Temporary mounts are optional. They provide
              functionality for the 'New' page."""

    parser = argparse.ArgumentParser(description = help)

    parser.add_argument("-w", "--webmote",
                        action = "store", required = True,
                        help = "The hostname of the Webmote server.")
    parser.add_argument("-n", "--name",
                        action = "store", required = True,
                        help = "A descriptive name for this Receiver.")
    parser.add_argument("-s", "--source_mount",
                        action = "store", type = unicode, required = True,
                        help = "The location of all indexed media.")
    parser.add_argument("-d", "--downloads_mount",
                        action = "store", type = unicode,
                        default = None)
    parser.add_argument("-t", "--temporary_mount",
                        action = "store", type = unicode,
                        default = None)

    return parser.parse_args()

# Run.
#------------------------------------------------------------------------------

if __name__ == "__main__":
    log.write("Receiver launched.")

    pid_file = prepare_pid("receiver")

    options = parse_arguments()

    api = Api()

    try:
        api.action("insert", options.name)

        player = Player()

    finally:
        api.action("delete")

        communicate.close_connection()

        if pid_file:
            os.remove(pid_file)

        log.write("Receiver exited.")

