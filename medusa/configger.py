"""
Provide local variables of everything set in the YAML configuration file,
as well as a few other useful bits of global information.
"""

from sys import platform
from os.path import join, abspath, dirname, exists
from socket import gethostname
from yaml import load

#------------------------------------------------------------------------------

def read_config(config_file):
    with open(config_file, "r") as fle:
        config = load(fle)

    return config

#------------------------------------------------------------------------------

# Get the base path of this Medusa installation.
base_path = join(dirname(abspath(__file__)), "..")

# Get the hostname.
hostname = gethostname()

# Read in the configuration file.
#
config_file = join(base_path, "files/medusa_%s.cfg" % hostname.lower())
if not exists(config_file):
    config_file = join(base_path, "files/medusa.cfg")

locals().update(read_config(config_file))

# Get the full path to the database and log files.
#
database_file = join(base_path, database_file)
log_file = join(base_path, log_file)
