"""Provide local variables of everything set in the YAML configuration file,
as well as a few other useful bits of global information.
"""

def read_config(config_file):
    from yaml import load

    with open(config_file, "r") as fle:
        config = load(fle)

    return config

# Get the base path of this Medusa installation.
from os.path import join, abspath, dirname
base_path = join(dirname(abspath(__file__)), "..")

# Read in the configuration file.
config_file = join(base_path, "files/medusa.cfg")
locals().update(read_config(config_file))

# Get the full path to the database and log files.
database_file = join(base_path, database_file)
log_file = join(base_path, log_file)

# Get the operating system.
from sys import platform

# Get the hostname.
from socket import gethostname
hostname = gethostname()
