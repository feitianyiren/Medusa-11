#!/usr/bin/env python

import os
from ConfigParser import ConfigParser

#------------------------------------------------------------------------------

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
CONFIG_FILE = os.path.join(BASE_PATH, "cfg/medusa.cfg")

#------------------------------------------------------------------------------

def _getlist(self, section, option):
    return [v.strip() for v in self.get(section, option).split(",")]

ConfigParser.getlist = _getlist

#------------------------------------------------------------------------------

config = ConfigParser()
config.base_path = BASE_PATH
config.read(CONFIG_FILE)
