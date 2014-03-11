#!/usr/bin/env python

"""
Proxy function calls exposed to Snakes during communication.
"""

from collections import defaultdict

#------------------------------------------------------------------------------

class Proxy(object):

    _snakes = defaultdict()

    def update(self, message):
        snake, status = message
        self._snakes[snake] = status
