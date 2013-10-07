__author__ = 'jcorbett'

import nose, nose.plugins

import os
import logging

log = logging.getLogger('nose.plugins.snot')

class SlickAsSnotPlugin(nose.plugins.Plugin):
    name = "snot"

    def options(self, parser, env=os.environ):
        super(SlickAsSnotPlugin, self).options(parser, env=env)

    def configure(self, options, conf):
        super(SlickAsSnotPlugin, self).configure(options, conf)
        if not self.enabled:
            return

    def finalize(self, result):
        log.info('Snot plugin finalized!')


