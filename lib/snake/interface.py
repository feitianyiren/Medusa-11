#!/usr/bin/env python

"""
Control the Qt interface that contains the VLC player.
"""

import sys

from PyQt4 import QtCore
from PyQt4 import QtGui

from lib.medusa.config import config

#------------------------------------------------------------------------------

class Interface(QtGui.QMainWindow):

    def __init__(self, control):
        super(Interface, self).__init__()

        self.control = control
        self.player = self.control.player

    #--------------------------------------------------------------------------

    def initialise(self):
        self.build_interface()
        self.connect_player()
        self.connect_slots()

    #--------------------------------------------------------------------------

    def build_interface(self):
        self.window = QtGui.QWidget(self)
        self.setCentralWidget(self.window)

        # Center the window.
        #
        self.setWindowTitle("Medusa")
        self.resize(1280, 720)
        geometry = self.frameGeometry()
        center = QtGui.QDesktopWidget().availableGeometry().center()
        geometry.moveCenter(center)
        self.move(geometry.topLeft())

        # Make the background color black.
        #
        palette = self.window.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        self.window.setPalette(palette)
        self.window.setAutoFillBackground(True)

        # Set up a timer that will update playback status to the Head.
        #
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(config.getint("snake", "update"))
        self.timer.timeout.connect(self.check_status)

    def connect_player(self):
        if sys.platform == "win32":
            self.player.set_hwnd(self.window.winId())

        elif sys.platform == "darwin":
            self.player.set_nsobject(self.window.winId())

        else:
            self.player.set_xwindow(self.window.winId())

    def connect_slots(self):
        self.control._play.connect(self.play)
        self.control._stop.connect(self.stop)

    #--------------------------------------------------------------------------

    def check_status(self):
        """
        Check that VLC is still playing. If it isn't, trigger a stop.
        """

        if self.control.state() not in ("playing", "paused"):
            self.control.stop()

    def play(self):
        # Only show the window if there is a video track.
        #
        if self.control.player.video_get_track_count() > 0:
            self.show()
            self.showFullScreen()

        self.timer.start()

    def stop(self):
        self.timer.stop()
        self.hide()
