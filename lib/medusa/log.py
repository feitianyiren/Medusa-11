#!/usr/bin/env python

"""
Log to a file.
"""

import logging as log

from lib.medusa.config import config

#------------------------------------------------------------------------------

FORMAT = "%(asctime)s %(levelname)s %(filename)s %(message)s"

#------------------------------------------------------------------------------

log.basicConfig(filename=config.get("files", "log"),
                format=FORMAT,
                level=log.WARN)
