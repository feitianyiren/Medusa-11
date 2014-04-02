#!/usr/bin/env python

"""
Various utilities used by Medusa.
"""

import socket

#------------------------------------------------------------------------------

def get_hostname():
    return socket.gethostname()

#------------------------------------------------------------------------------

class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]
