__author__ = 'jcorbett'

import nose, nose.plugins

import os
import logging
import docutils.core

log = logging.getLogger('nose.plugins.snot')


class DocStringMetadata(object):

    def __init__(self, func):
        if hasattr(func, '__doc__'):
            self.dom = docutils.core.publish_doctree(func.__doc__).asdom()
            if self.dom is not None and self.dom.firstChild is not None and self.dom.firstChild.nodeName == 'document':
                document = self.dom.firstChild
                if document.hasChildNodes() and document.firstChild.nodeName == 'paragraph':
                    self.name = document.firstChild.firstChild.nodeValue
                    if len(document.childNodes) > 1:
                        for node in document.childNodes[1:]:
                            self.process_node(node)

    def process_node(self, node):
        if node.nodeName == 'block_quote':
            for child_node in node.childNodes:
                self.process_node(child_node)
        if node.nodeName == 'field_list':
            for child_node in node.childNodes:
                self.process_node(child_node)
        if node.nodeName == 'paragraph':
            if hasattr(self, 'purpose'):
                self.purpose = self.purpose + '\n\n' + node.firstChild.nodeValue
            else:
                self.purpose = node.firstChild.nodeValue
        if node.nodeName == 'field':
            if node.firstChild.firstChild.nodeValue == 'expectedResults' and node.childNodes[1].firstChild.nodeName == 'enumerated_list':
                self.expectedResults = []
                for list_item in node.childNodes[1].firstChild.childNodes:
                    self.expectedResults.append(list_item.firstChild.firstChild.nodeValue)
            if node.firstChild.firstChild.nodeValue == 'steps' and node.childNodes[1].firstChild.nodeName == 'enumerated_list':
                self.steps = []
                for list_item in node.childNodes[1].firstChild.childNodes:
                    self.steps.append(list_item.firstChild.firstChild.nodeValue)
            elif node.firstChild.firstChild.nodeValue == 'tags':
                setattr(self, node.firstChild.firstChild.nodeValue, node.childNodes[1].firstChild.firstChild.nodeValue.split(", "))
            else:
                setattr(self, node.firstChild.firstChild.nodeValue, node.childNodes[1].firstChild.firstChild.nodeValue)


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



