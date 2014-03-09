#!/usr/bin/env python

import os

from PyQt4 import QtCore
from PyQt4 import QtGui
import requests

from lib.medusa.config import config
from lib.medusa.log import log
from lib.snake import vlc

#------------------------------------------------------------------------------

class Control(QtGui.QWidget):

    _queue = []
    _play = QtCore.pyqtSignal()
    _stop = QtCore.pyqtSignal()

    def __init__(self):
        super(Control, self).__init__()

        self.name = ""
        self.media_path = ""
        self.downloads_path = ""
        self.communicate = None
        self.media_id = None

        self.volume_increment = config.getint("snake", "volume_increment")
        self.volume_max = config.getint("snake", "volume_max")
        self.volume_min = config.getint("snake", "volume_min")

        self.setup()

    def setup(self):
        arguments = [
            "--video-title-show",
            "--video-title-timeout", "1",
            "--sub-source marq",
            "--verbose", "-1"
        ]

        self.instance = vlc.Instance(" ".join(arguments))
        self.player = self.instance.media_player_new()

        overlay_time = config.getint("snake", "overlay_time") * 1000

        settings = {
            vlc.VideoMarqueeOption.Position: vlc.Position.TopRight,
            vlc.VideoMarqueeOption.Timeout: overlay_time,
            vlc.VideoMarqueeOption.Size: 16,
            vlc.VideoMarqueeOption.marquee_X: 16,
            vlc.VideoMarqueeOption.marquee_Y: 16
        }

        for option, setting in settings.items():
            self.player.video_set_marquee_int(option, setting)

    #--------------------------------------------------------------------------

    def play(self, item=None):
        if self.media_id:
            self.stop()

        if item:
            self._add_to_queue(item)

        if self._queue:
            item = self._queue.pop(0)

        else:
            return

        self.media_id = item[0]
        name = item[1]
        elapsed = item[2]
        path = item[3]

        self._insert_viewed(self.media_id)
        self.player.set_media(self.instance.media_new(path))
        self.player.play()
        self._play.emit()

        if elapsed:
            self.jump(elapsed)

        self.overlay(name)

    def pause(self):
        if self._get_state() == "playing":
            self.overlay("Paused")

        else:
            self.overlay("Resumed")

        self.player.pause()

    def stop(self):
        self._update_elapsed()
        self.player.stop()
        self.media_id = None
        self._stop.emit()
        self._send_update()
        self.play()

    def volume_up(self):
        self._set_volume(self._get_volume() + self.volume_increment)
        self.overlay("Volume Increased")

    def volume_down(self):
        self._set_volume(self._get_volume() - self.volume_increment)
        self.overlay("Volume Decreased")

    def mute(self):
        if int(self.player.audio_get_mute()) == 1:
            self.overlay("Unmuted")

        else:
            self.overlay("Muted")

        self.player.audio_toggle_mute()

    def jump(self, seconds):
        elapsed, total = self._get_time()

        if elapsed > int(seconds):
            self.overlay("Jumped Backward")

        else:
            self.overlay("Jumped Forward")

        self.player.set_time(int(seconds) * 1000)

    def subtitle(self, track):
        self.player.video_set_spu(int(track))

        if int(track) == -1:
            self.overlay("Disabled Subtitles")

        else:
            self.overlay("Changed Subtitle Track")

    def audio(self, track):
        self.player.audio_set_track(int(track))

        if int(track) == -1:
            self.overlay("Disabled Audio")

        else:
            self.overlay("Changed Audio Track")

    #--------------------------------------------------------------------------

    def state(self):
        self._send_update()

        return self._get_state()

    def overlay(self, text):
        self.player.video_set_marquee_string(vlc.VideoMarqueeOption.Text, text)

    def queue(self, item):
        self._add_to_queue(item)

    def empty_queue(self):
        log.info("Emptying queue")

        self._queue = []

    #--------------------------------------------------------------------------

    def _add_to_queue(self, item):
        if str(item).isdigit():
            media_id = int(item)
            data = self._call_api(["media", media_id])
            name = data.get("name_one", "")
            elapsed = int(data.get("elapsed") or 0)
            paths = sorted(data["paths"])

            for path in paths:
                path = self._build_media_path(path)

                self._queue.append((media_id, name, elapsed, path))

        else:
            path = self._build_downloads_path(item)

            self._queue.append((item, item, 0, path))

    def _get_state(self):
        return str(self.player.get_state()).lstrip("State.").lower()

    def _get_time(self):
        time_elapsed = int(self.player.get_time()) / 1000
        time_total = int(self.player.get_length()) / 1000

        return time_elapsed, time_total

    def _get_volume(self):
        return int(self.player.audio_get_volume())

    #--------------------------------------------------------------------------

    def _set_volume(self, volume):
        log.info("Setting volume to %s", volume)

        if volume > self.volume_max:
            volume = self.volume_max

        if volume < self.volume_min:
            volume = self.volume_min

        self.player.audio_set_volume(volume)

    #--------------------------------------------------------------------------

    def _call_api(self, bits):
        url = "http://%s:%s/%s/%s" % (config.get("head", "host"),
                                      config.get("ports", "head"),
                                      config.get("head", "api_base"),
                                      "/".join(str(b) for b in bits))

        try:
            return requests.get(url).json()

        except Exception as excp:
            log.error("API call to %s failed: %s", url, excp)

            return {}

    def _send_update(self):
        elapsed, total = self._get_time()

        update = {
            "media_id": self.media_id or "",
            "state": self._get_state(),
            "elapsed": elapsed,
            "total": total,
            "mute": int(self.player.audio_get_mute()) == 1,
            "queue": self._queue,
            "audio": self.player.audio_get_track_description(),
            "subtitles": self.player.video_get_spu_description()
        }

        self.communicate.send({"update": [self.name, update]})

    def _insert_viewed(self, media_id):
        self._call_api(["viewed", self.media_id])

    def _update_elapsed(self):
        if not self.media_id:
            return

        threshold = config.getint("snake", "resume_threshold")
        elapsed, total = self._get_time()

        if elapsed < threshold:
            self._call_api(["viewed", self.media_id, "delete"])

            return

        if (total - elapsed) < threshold:
            elapsed = 0

        self._call_api(["elapsed", self.media_id, elapsed])

    #--------------------------------------------------------------------------

    def _build_media_path(self, path):
        return unicode(os.path.join(self.media_path, path))

    def _build_downloads_path(self, name):
        for root, directories, files in os.walk(self.downloads_path):
            for file_ in files:
                if name == file_:
                    return unicode(os.path.join(root, file_))
