__author__ = 'jcorbett'

import nose, nose.plugins, nose.case

import re
import os
import logging
import docutils.core

log = logging.getLogger('nose.plugins.snot')


class DocStringMetaData(object):

    def __init__(self, func):
        if hasattr(func, '__doc__') and func.__doc__ is not None:
            dom = docutils.core.publish_doctree(func.__doc__).asdom()
            if dom is not None and dom.firstChild is not None and dom.firstChild.nodeName == 'document':
                document = dom.firstChild
                if document.hasChildNodes() and document.firstChild.nodeName == 'paragraph':
                    self.name = document.firstChild.firstChild.nodeValue
                    if len(document.childNodes) > 1:
                        for node in document.childNodes[1:]:
                            self.process_node(node)
                else:
                    self.name = self.get_name_from_function_name(func)
                    for node in document.childNodes:
                        self.process_node(node)
        else:
            self.name = self.get_name_from_function_name(func)

    def get_name_from_function_name(self, func):
        if hasattr(func, '__name__') and func.__name__ is not None and func.__name__ != "":
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', func.__name__)
            s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
            return re.sub(r'_', ' ', re.sub(r'_?[tT]est$', '', re.sub(r'^[Tt]est_?', '', s2))).capitalize()

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
            elif node.firstChild.firstChild.nodeValue == 'steps' and node.childNodes[1].firstChild.nodeName == 'enumerated_list':
                self.steps = []
                for list_item in node.childNodes[1].firstChild.childNodes:
                    self.steps.append(list_item.firstChild.firstChild.nodeValue)
            elif node.firstChild.firstChild.nodeValue == 'tags':
                setattr(self, node.firstChild.firstChild.nodeValue, node.childNodes[1].firstChild.firstChild.nodeValue.split(", "))
            else:
                setattr(self, node.firstChild.firstChild.nodeValue, node.childNodes[1].firstChild.firstChild.nodeValue)


def get_tests(testsuite):
    tests = []
    for test in testsuite:
        if hasattr(test, '__iter__'):
            tests.extend(get_tests(test))
        else:
            tests.append(test)
    return tests


class SlickAsSnotPlugin(nose.plugins.Plugin):
    name = "snot"

    def options(self, parser, env=os.environ):
        super(SlickAsSnotPlugin, self).options(parser, env=env)

    def configure(self, options, conf):
        super(SlickAsSnotPlugin, self).configure(options, conf)
        if not self.enabled:
            return

    def prepareTest(self, testsuite):
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        for test in get_tests(testsuite):
            assert isinstance(test, nose.case.Test)
            testmethod = test.test._testMethodName
            if testmethod == 'runTest':
                testmethod = 'test'
            testdata = DocStringMetaData(getattr(test.test, testmethod))
            if not hasattr(testdata, 'automationId'):
                testdata.automationId = test.id()
            if not hasattr(testdata, 'automationTool'):
                testdata.automationTool = 'python-nose'
            log.debug("Found test with automationId '%s' and name '%s'", testdata.automationId, testdata.name)

    def finalize(self, result):
        log.info('Snot plugin finalized!')



