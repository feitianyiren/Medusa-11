#!/usr/bin/env python

"""
Proxy function calls exposed to the Head during communication.
"""

import traceback

from lib.medusa.log import log

#------------------------------------------------------------------------------

class Proxy(object):

    control = None

    def action(self, message):
        try:
            function, arguments = message
            getattr(self.control, function)(*arguments)

            log.warn("Performed action: %s", function)

        except Exception as excp:
            log.error("Action %s failed: %s", function, excp)
            log.error(traceback.format_exc())
