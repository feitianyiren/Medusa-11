#!/usr/bin/env python

"""
A Snake is a media player. It receives instructions from Medusa's Head.
"""

import argparse
import sys

from PyQt4 import QtGui

from lib.medusa.communicate import Communicate
from lib.medusa.log import log
from lib.snake.control import Control
from lib.snake.interface import Interface
from lib.snake.proxy import Proxy

#------------------------------------------------------------------------------

def main(options):
    application = QtGui.QApplication(sys.argv)

    control = Control()
    control.name = options.name
    control.media_path = options.media
    control.downloads_path = options.downloads

    Proxy.control = control

    communicate = Communicate(proxy=Proxy, name=options.name, qthread=True)

    control.communicate = communicate

    interface = Interface(control)
    interface.initialise()

    control._send_update()

    application.exec_()

#------------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--name",
                        action="store", required=True)
    parser.add_argument("-m", "--media",
                        action="store", type=unicode, required=True)
    parser.add_argument("-d", "--downloads",
                        action="store", type=unicode)

    return parser.parse_args()

#------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        log.warn("Snake initialised")

        main(parse_arguments())

    finally:
        log.warn("Snake exited")
