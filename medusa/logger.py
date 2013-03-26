"""Part of Medusa (MEDia USage Assistant).

Provides very basic logging for now, with timestamp and hostname.

"""

import logging

import configger as config

logging.basicConfig(filename = config.log_file,
                    level = logging.INFO,
                    format = "%(asctime)s %(message)s",
                    datefmt = "%d/%m %H:%M:%S")

def write(line):
    logging.info("[%s] %s" % (config.hostname, line))

def error(line):
    logging.info("[%s] ERROR: %s" % (config.hostname, line))
