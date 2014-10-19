#!/usr/bin/env python

"""
Proxy function calls exposed to Snakes during communication.
"""

#------------------------------------------------------------------------------

class Proxy(object):

    _snakes = {}

    def update(self, message):
        snake, status = message

        self._snakes[snake] = status
