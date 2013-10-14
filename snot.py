__author__ = 'jcorbett'

import nose, nose.plugins, nose.case
from slickqa import SlickQA, Testcase, ResultStatus, RunStatus, Step, Result

import re
import os
import logging
import docutils.core
import datetime
import traceback
from StringIO import StringIO


log = logging.getLogger('nose.plugins.snot')

current_result = None

def add_file(path):
    """
    Upload a file to slick, adding it to the current test result.  If no test is running, this will do nothing!

    :param path: The path to the specified file
    :return: Nothing
    """
    if current_result is not None:
        current_result.add_file(path)

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
        parser.add_option("--slick-url", action="store", default=env.get('SLICK_URL'),
                          metavar="SLICK_URL", dest="slick_url",
                          help="the base url of the slick web app [SLICK_URL]")
        parser.add_option("--slick-project-name", action="store", default=env.get('SLICK_PROJECT_NAME'),
                          metavar="SLICK_PROJECT_NAME", dest="slick_project_name",
                          help="the name of the project in slick to use [SLICK_PROJECT_NAME]")
        parser.add_option("--slick-release", action="store", default=env.get('SLICK_RELEASE'),
                          metavar="SLICK_RELEASE", dest="slick_release",
                          help="the release under which to file the results in slick [SLICK_RELEASE]")
        parser.add_option("--slick-build", action="store", default=env.get('SLICK_BUILD'),
                          metavar="SLICK_BUILD", dest="slick_build",
                          help="the build under which to file the results in slick [SLICK_BUILD]")
        parser.add_option("--slick-testplan", action="store", default=env.get('SLICK_TESTPLAN'),
                          metavar="SLICK_TESTPLAN", dest="slick_testplan",
                          help="the testplan to link the testrun to in slick [SLICK_TESTPLAN]")
        parser.add_option("--slick-testrun-name", action="store", default=env.get('SLICK_TESTRUN_NAME'),
                          metavar="SLICK_TESTRUN_NAME", dest="slick_testrun_name",
                          help="the name of the testrun to create in slick [SLICK_TESTRUN_NAME]")

        # Make sure the log capture doesn't show slick related logging statements
        if 'NOSE_LOGFILTER' in env:
            env['NOSE_LOGFILTER'] = env.get('NOSE_LOGFILTER') + ",-slick,-requests,-slick-reporter"
        else:
            env['NOSE_LOGFILTER'] = "-slick,-requests,-slick-reporter"


    def configure(self, options, conf):
        super(SlickAsSnotPlugin, self).configure(options, conf)
        if not self.enabled:
            return
        for required in ['slick_url', 'slick_project_name']:
            if (not hasattr(options, required)) or getattr(options, required) is None or getattr(options, required) == "":
                log.error("You can't use snot without specifying at least the slick url and the project name.")
                self.enabled = False
                return
        self.url = options.slick_url
        self.project_name = options.slick_project_name
        self.release = options.slick_release
        self.build = options.slick_build
        self.testplan = options.slick_testplan
        self.testrun_name = options.slick_testrun_name
        self.slick = SlickQA(self.url, self.project_name, self.release, self.build, self.testplan, self.testplan)

    def prepareTest(self, testsuite):
        if not self.enabled:
            return
        self.results = dict()
        for test in get_tests(testsuite):
            assert isinstance(test, nose.case.Test)
            testmethod = test.test._testMethodName
            if testmethod == 'runTest' and hasattr(test.test, "test"):
                testmethod = 'test'
            testdata = DocStringMetaData(getattr(test.test, testmethod))
            if not hasattr(testdata, 'automationId'):
                testdata.automationId = test.id()
            if not hasattr(testdata, 'automationTool'):
                testdata.automationTool = 'python-nose'
            slicktest = Testcase()
            slicktest.name = testdata.name
            slicktest.automationId = testdata.automationId
            slicktest.automationTool = testdata.automationTool
            for attribute in ['automationConfiguration', 'automationKey', 'author', 'purpose', 'requirements', 'tags']:
                if hasattr(testdata, attribute):
                    setattr(slicktest, attribute, getattr(testdata, attribute))
            slicktest.project = self.slick.project.create_reference()
            if hasattr(testdata, 'component'):
                component = self.slick.get_component(testdata.component)
                if component is None:
                    component = self.slick.create_component(testdata.component)
                slicktest.component = component.create_reference()
            if hasattr(testdata, 'steps'):
                slicktest.steps = []
                for step in testdata.steps:
                    slickstep = Step()
                    slickstep.name = step
                    if hasattr(testdata, 'expectedResults') and len(testdata.expectedResults) > len(slicktest.steps):
                        slickstep.expectedResult = testdata.expectedResults[len(slicktest.steps)]
                    slicktest.steps.append(slickstep)
            self.results[test.address()] = self.slick.file_result(slicktest.name, ResultStatus.NO_RESULT, reason="not yet run", runlength=0, testdata=slicktest, runstatus=RunStatus.TO_BE_RUN)

    def startTest(self, test):
        if not self.enabled:
            return
        if test.address() in self.results:
            result = self.results[test.address()]
            assert isinstance(result, Result)
            result.runstatus = RunStatus.RUNNING
            result.started = datetime.datetime.now()
            result.reason = ""
            if hasattr(result, 'config') and not hasattr(result.config, 'configId'):
                del result.config
            if hasattr(result, 'component') and not hasattr(result.component, 'id'):
                del result.component
            result.update()
            global current_result
            current_result = result

    def addSlickResult(self, test, resultstatus=ResultStatus.PASS, err=None):
        if not self.enabled:
            return
        if test.address() in self.results:
            result = self.results[test.address()]
            assert isinstance(result, Result)
            result.runstatus = RunStatus.FINISHED
            result.status = resultstatus
            result.finished = datetime.datetime.now()
            result.runlength = int((result.finished - result.started).total_seconds() * 1000)
            if err is not None:
                # log capture and stderr/stdout capture are appended to the message.  We don't want those showing up
                # in the reason
                reason_lines = traceback.format_exception(*err)
                message_parts = reason_lines[-1].split('\n')
                reason_lines[-1] = message_parts[0]
                capture = None
                if len(message_parts) > 2:
                    capture = '\n'.join(message_parts[1:])
                result.reason = '\n'.join(reason_lines)

                if capture is not None:
                    capture_fileobj = StringIO(capture)
                    if not result.files:
                        result.files = []
                    stored_file = self.slick.slickcon.files.upload_local_file("Nose Capture.txt", capture_fileobj)
                    result.files.append(stored_file)
                    capture_fileobj.close()

            if hasattr(result, 'config') and not hasattr(result.config, 'configId'):
                del result.config
            if hasattr(result, 'component') and not hasattr(result.component, 'id'):
                del result.component
            result.update()


    def addSuccess(self, test):
        if not self.enabled:
            return
        self.addSlickResult(test)

    def addError(self, test, err):
        if not self.enabled:
            return
        self.addSlickResult(test, ResultStatus.BROKEN_TEST, err)

    def addFailure(self, test, err):
        if not self.enabled:
            return
        self.addSlickResult(test, ResultStatus.FAIL, err)

    def finalize(self, result):
        if not self.enabled:
            return
        self.slick.finish_testrun()


