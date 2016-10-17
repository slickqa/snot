import nose, nose.plugins, nose.case, nose.config
from slickqa import SlickQA, Testcase, ResultStatus, RunStatus, Step, Result, make_result_updatable, make_testrun_updatable
from slickqa.connection import SlickConnection

import re
import os
import sys
import logging
import docutils.core
import datetime
import traceback
import itertools
import importlib
import time
from io import StringIO
from unittest import SkipTest
try:
    from ConfigParser import SafeConfigParser
except:
    from configparser import SafeConfigParser

__author__ = 'jcorbett'


log = logging.getLogger('nose.plugins.snot')

current_result = None
testrun = None
config = None

REQUIRES_ATTRIBUTE = 'slick_requires'


class PassedOnRetry(Exception):
    pass


def requires(*args):
    def _wrap_with_requires(f):
        if hasattr(f, REQUIRES_ATTRIBUTE):
            (getattr(f, REQUIRES_ATTRIBUTE)).extend(args)
        else:
            setattr(f, REQUIRES_ATTRIBUTE, args)
        return f
    return _wrap_with_requires


def add_file(path, fileobj=None):
    """
    Upload a file to slick, adding it to the current test result.  If no test is running, this will do nothing!

    :param path: The path to the specified file
    :return: Nothing
    """
    if current_result is not None:
        current_result.add_file(path, fileobj)


def add_file_to_testrun(path, fileobj=None):
    """
    Upload a file to slick, adding it to the current testrun.  If there is no current slick testrun this will do
    nothing!

    :param path: The path to the specified file
    :return: Nothing
    """
    if testrun is not None:
        testrun.add_file(path, fileobj)


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
                try:
                    setattr(self, node.firstChild.firstChild.nodeValue, node.childNodes[1].firstChild.firstChild.nodeValue)
                except:
                    sys.stderr.write("Problem parsing comment for test: {}".format(self.name))


def parse_config(files):
    parser = SafeConfigParser()
    parser.read(files)
    return parser


def call_function(function_name):
    module = None
    if '.' not in sys.path:
        sys.path.append('.')
    if '.' in function_name:
        last_dot_index = function_name.rindex('.')
        module = function_name[:last_dot_index]
        function_name = function_name[last_dot_index + 1:]
    if module is None:
        module = globals()
    else:
        module = importlib.import_module(module)
    if hasattr(module, function_name):
        func = getattr(module, function_name)
        return func()
    else:
        raise Exception("could not find " + function_name + " to run.")


def get_tests(testsuite):
    tests = []
    for test in testsuite:
        if hasattr(test, '__iter__'):
            if hasattr(test, 'test_generator') and test.test_generator is not None:
                test.test_generator, gen = itertools.tee(test.test_generator)
                tests.extend(get_tests(test))
                test.test_generator = gen
            else:
                tests.extend(get_tests(test))
        else:
            tests.append(test)
    return tests


class LogCapturingHandler(logging.Handler):

    ignore = ['nose', 'slick', 'requests']

    def __init__(self):
        super(LogCapturingHandler, self).__init__()

    def pylevel_to_slicklevel(self, loglevel):
        if loglevel == logging.DEBUG:
            return "DEBUG"
        elif loglevel == logging.INFO:
            return "INFO"
        elif loglevel == logging.WARN:
            return "WARN"
        elif loglevel > logging.WARN:
            return "ERROR"
        else:
            return "DEBUG"

    def emit(self, record):
        for ignore_name in LogCapturingHandler.ignore:
            if record.name.startswith(ignore_name) and not record.name.startswith('slickwd'):
                return
        msg = self.format(record)
        if current_result is not None:
            if record.exc_info is None:
                current_result.add_log_entry(msg,
                                             level=self.pylevel_to_slicklevel(record.levelno),
                                             loggername=record.name)
            else:
                excmessage = ''
                if hasattr(record.exc_info[1], 'message'):
                    excmessage = record.exc_info[1].message
                current_result.add_log_entry(msg,
                                             level=self.pylevel_to_slicklevel(record.levelno),
                                             loggername=record.name,
                                             exceptionclassname=record.exc_info[0].__name__,
                                             exceptionmessage=excmessage,
                                             stacktrace=traceback.format_tb(record.exc_info[2]))


class SlickAsSnotPlugin(nose.plugins.Plugin):
    name = "snot"
    score = 1800

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
        parser.add_option("--slick-build-from-function", action="store", default=env.get('SLICK_BUILD_FROM_FUNCTION'),
                          metavar="SLICK_BUILD_FROM_FUNCTION", dest="slick_build_from_function",
                          help="get the slick build from a function.  The parameter should be the module and function name to call [SLICK_BUILD_FROM_FUNCTION].")
        parser.add_option("--slick-testplan", action="store", default=env.get('SLICK_TESTPLAN'),
                          metavar="SLICK_TESTPLAN", dest="slick_testplan",
                          help="the testplan to link the testrun to in slick [SLICK_TESTPLAN]")
        parser.add_option("--slick-testrun-name", action="store", default=env.get('SLICK_TESTRUN_NAME'),
                          metavar="SLICK_TESTRUN_NAME", dest="slick_testrun_name",
                          help="the name of the testrun to create in slick [SLICK_TESTRUN_NAME]")
        parser.add_option("--slick-environment-name", action="store", default=env.get('SLICK_ENVIRONMENT_NAME'),
                          metavar="SLICK_ENVIRONMENT_NAME", dest="slick_environment_name",
                          help="the name of the environment in slick to use in the testrun [SLICK_ENVIRONMENT_NAME]")
        parser.add_option("--slick-testrun-group", action="store", default=env.get('SLICK_TESTRUN_GROUP'),
                          metavar="SLICK_TESTRUN_GROUP", dest="slick_testrun_group",
                          help="the name of the testrun group in slick to add this testrun to (optional) [SLICK_ENVIRONMENT_NAME]")
        parser.add_option("--slick-agent-name", action="store", default=env.get('SLICK_AGENT_NAME'),
                          metavar="SLICK_AGENT_NAME", dest="slick_agent_name",
                          help="what to put in slick's hostname field in the result.")
        schedule_results_default = "normal"
        if 'SLICK_SCHEDULE_RESULTS' in env:
            schedule_results_default = "schedule"
        parser.add_option("--slick-schedule-results", action="store_const", const="schedule", default=schedule_results_default,
                          metavar="SLICK_SCHEDULE_RESULTS", dest="slick_mode",
                          help="Schedule empty results in slick, but do not run the tests")
        parser.add_option("--slick-schedule-add-requirement", action="store", default=env.get("SLICK_SCHEDULE_ADD_REQUIREMENT"),
                          metavar="SLICK_SCHEDULE_ADD_REQUIREMENT", dest="requirement_add",
                          help="Add a requirement to all results when scheduling.")
        parser.add_option("--slick-schedule-new-requires", action="store_true", dest="new_requires",
                          help="apply the requires directly on the result as an attribute.")
        parser.add_option("--slick-testrun-id", action="store", default=env.get('SLICK_TESTRUN_ID'),
                          metavar="SLICK_TESTRUN_ID", dest="slick_testrun_id",
                          help="Instead of creating a new testrun, use an existing one.")
        parser.add_option("--slick-result-id", action="store", default=env.get('SLICK_RESULT_ID'),
                          metavar="SLICK_RESULT_ID", dest="slick_result_id",
                          help="Instead of creating a new result in the testrun, update an existing one.")

        # Make sure the log capture doesn't show slick related logging statements
        if 'NOSE_LOGFILTER' in env:
            env['NOSE_LOGFILTER'] = env.get('NOSE_LOGFILTER') + ",-slick,-requests,-slick-reporter"
        else:
            env['NOSE_LOGFILTER'] = "-slick,-requests,-slick-reporter"

    def configure(self, options, conf):
        super(SlickAsSnotPlugin, self).configure(options, conf)
        global config, testrun
        assert isinstance(conf, nose.config.Config)
        if options.files is not None and len(options.files) > 0:
            config = parse_config(options.files)
        if not self.enabled:
            return
        self.use_existing_testrun = False
        if hasattr(options, 'slick_testrun_id') and hasattr(options, 'slick_result_id') and \
           options.slick_testrun_id is not None and options.slick_result_id is not None:
            self.use_existing_testrun = True
            self.testrun_id = options.slick_testrun_id
            self.result_id = options.slick_result_id
        else:
            for required in ['slick_url', 'slick_project_name']:
                if (not hasattr(options, required)) or getattr(options, required) is None or getattr(options, required) == "":
                    log.error("You can't use snot without specifying at least the slick url and the project name.")
                    self.enabled = False
                    return
        self.url = options.slick_url
        self.project_name = options.slick_project_name
        self.release = options.slick_release
        self.build = options.slick_build
        self.build_function = options.slick_build_from_function
        if self.build_function:
            try:
                self.build = call_function(self.build_function)
            except:
                log.warn("Problem occured calling build information from '%s': ", self.build_function, exc_info=sys.exc_info())
        self.testplan = options.slick_testplan
        self.testrun_name = options.slick_testrun_name
        self.environment_name = options.slick_environment_name
        self.testrun_group = options.slick_testrun_group
        self.mode = options.slick_mode
        self.requirement_add = options.requirement_add
        self.agent_name = options.slick_agent_name
        testrun = None
        if self.use_existing_testrun:
            self.slick = SlickConnection(self.url)
            testrun = self.slick.testruns(options.slick_testrun_id).get()
            make_testrun_updatable(testrun, self.slick)
        else:
            self.slick = SlickQA(self.url, self.project_name, self.release, self.build, self.testplan, self.testrun_name, self.environment_name, self.testrun_group)
            testrun = self.slick.testrun
            if self.mode == 'schedule':
                testrun.attributes = {'scheduled': 'true'}
                testrun.update()
        self.new_requires = options.new_requires
        root_logger = logging.getLogger()
        self.loghandler = LogCapturingHandler()
        root_logger.addHandler(self.loghandler)
        root_logger.setLevel(logging.DEBUG)

    def prepareTest(self, testsuite):
        if not self.enabled:
            return
        self.results = dict()
        for test in get_tests(testsuite):
            assert isinstance(test, nose.case.Test)
            if self.use_existing_testrun:
                result = self.slick.results(self.result_id).get()
                make_result_updatable(result, self.slick)
                self.results[test.id()] = result
            else:
                testmethod = test.test._testMethodName
                if testmethod == 'runTest' and hasattr(test.test, "test"):
                    testmethod = 'test'

                testdata = DocStringMetaData(getattr(test.test, testmethod))
                if not hasattr(testdata, 'automationId'):
                    testdata.automationId = test.id()
                if not hasattr(testdata, 'automationTool'):
                    testdata.automationTool = 'python-nose'
                if not hasattr(testdata, 'automationKey'):
                    # build key
                    address = list(test.address())
                    testfile = os.path.relpath(address[0])
                    module_name = os.path.basename(address[0])[:-3]
                    if module_name == address[1]:
                        address.pop(1)
                    testdata.automationKey = "{0}:{1}".format(testfile, address[1])
                    if len(address) > 2:
                        try:
                            testdata.automationKey = ".".join([testdata.automationKey, ] + address[2:])
                        except:
                            pass
                slicktest = Testcase()
                slicktest.name = testdata.name
                if '{' in testdata.name and '}' in testdata.name and hasattr(test.test, 'arg') and test.test.arg is not None and len(test.test.arg) > 0:
                    slicktest.name = testdata.name.format(*test.test.arg)
                slicktest.automationId = testdata.automationId
                slicktest.automationTool = testdata.automationTool
                result_attributes = {}
                requirements = None
                if self.mode == "schedule" and self.requirement_add is not None and self.requirement_add != "":
                    result_attributes[self.requirement_add] = "required"
                    if self.new_requires:
                        requirements = [self.requirement_add]
                try:
                    actual_test_method = getattr(test.test, testmethod)
                    if hasattr(actual_test_method, REQUIRES_ATTRIBUTE):
                        requires_value = getattr(actual_test_method, REQUIRES_ATTRIBUTE)
                        if self.new_requires:
                            if requirements is None:
                                requirements = []
                            requirements.extend(requires_value)
                        for requirement in requires_value:
                            result_attributes[requirement] = "required"
                except:
                    log.error("Error occurred while trying to build attributes.", exc_info=sys.exc_info)
                if self.mode == 'schedule':
                    result_attributes['scheduled'] = "true"
                try:
                    for attribute in ['automationConfiguration', 'automationKey', 'author', 'purpose', 'requirements', 'tags']:
                        if attribute is not None and hasattr(testdata, attribute) and getattr(testdata, attribute) is not None:
                            data = getattr(testdata, attribute)
                            if '{' in data and '}' in data and test.test.arg is not None and len(test.test.arg) > 0:
                                data = data.format(*test.test.arg)
                            setattr(slicktest, attribute, data)
                    slicktest.project = self.slick.project.create_reference()
                    if hasattr(testdata, 'component'):
                        comp_name = testdata.component
                        if comp_name is not None and '{' in comp_name and '}' in comp_name and hasattr(test.test, 'arg') and test.test.arg is not None and len(test.test.arg) > 0:
                            comp_name = comp_name.format(*test.test.arg)
                        component = self.slick.get_component(comp_name)
                        if component is None:
                            component = self.slick.create_component(comp_name)
                        slicktest.component = component.create_reference()
                    if hasattr(testdata, 'steps'):
                        slicktest.steps = []
                        for step in testdata.steps:
                            slickstep = Step()
                            slickstep.name = step
                            if step is not None and '{' in step and '}' in step and test.test.arg is not None and len(test.test.arg) > 0:
                                slickstep.name = step.format(*test.test.arg)
                            if hasattr(testdata, 'expectedResults') and len(testdata.expectedResults) > len(slicktest.steps):
                                expectedResult = testdata.expectedResults[len(slicktest.steps)]
                                slickstep.expectedResult = expectedResult
                                if expectedResult is not None and '{' in expectedResult and '}' in expectedResult and test.test.arg is not None and len(test.test.arg) > 0:
                                    slickstep.expectedResult = expectedResult.format(*test.test.arg)
                            slicktest.steps.append(slickstep)
                except:
                    log.error("Error occured when parsing for test {}:".format(test.id()), exc_info=sys.exc_info())
                runstatus = RunStatus.TO_BE_RUN
                if self.mode == 'schedule':
                    runstatus = RunStatus.SCHEDULED
                if requirements is not None:
                    requirements.sort()
                self.results[test.id()] = self.slick.file_result(slicktest.name, ResultStatus.NO_RESULT, reason="not yet run", runlength=0, testdata=slicktest, runstatus=runstatus, attributes=result_attributes, requires=requirements)
        if self.enabled and self.mode == 'schedule':
            sys.exit(0)

    def beforeTest(self, test):
        if not self.enabled:
            return
        if self.mode == 'schedule':
            raise SkipTest()

    def startTest(self, test):
        if not self.enabled:
            return
        if test.id() in self.results:
            result = self.results[test.id()]
            assert isinstance(result, Result)
            if self.agent_name is not None:
                result.hostname = self.agent_name
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

    def afterTest(self, test):
        """Clear capture buffer.
        """
        if hasattr(sys.stdout, '__class__') and hasattr(sys.stdout.__class__, '__name__') and sys.stdout.__class__.__name__ == 'StringIO':
            add_file("Nose Capture.txt", sys.stdout)

    def addSlickResult(self, test, resultstatus=ResultStatus.PASS, err=None):
        if not self.enabled:
            return
        if self.mode == 'schedule':
            sys.exit(0)
            return
        if test.id() in self.results:
            result = self.results[test.id()]
            assert isinstance(result, Result)
            result.runstatus = RunStatus.FINISHED
            result.status = resultstatus
            result.finished = datetime.datetime.now()
            result.runlength = int((result.finished - result.started).total_seconds() * 1000)
            if err is not None:
                # log capture and stderr/stdout capture are appended to the message.  We don't want those showing up
                # in the reason
                reason_lines = None
                if sys.version_info[0] == 2:
                    reason_lines = traceback.format_exception(*err)
                else:
                    reason_lines = traceback.format_exception(*err, chain=not isinstance(err[1], str))
                message_parts = reason_lines[-1].split('\n')
                reason_lines[-1] = message_parts[0]
                capture = None
                if len(message_parts) > 2:
                    capture = '\n'.join(message_parts[1:])
                    reason_lines.reverse()
                result.reason = '\n'.join(reason_lines)

            if hasattr(result, 'config') and not hasattr(result.config, 'configId'):
                del result.config
            if hasattr(result, 'component') and not hasattr(result.component, 'id'):
                del result.component
            result.update()
        else:
            log.error("Unrecognized test %s", test.id())

    def addSuccess(self, test):
        if not self.enabled:
            return
        if self.mode == 'schedule':
            sys.exit(0)
            return
        self.addSlickResult(test)

    def addError(self, test, err):
        if not self.enabled:
            return
        if self.mode == 'schedule':
            sys.exit(0)
            return
        if err[0] is SkipTest:
            self.addSlickResult(test, ResultStatus.SKIPPED, err)
        elif err[0] is PassedOnRetry:
            self.addSlickResult(test, ResultStatus.PASSED_ON_RETRY, err)
        else:
            self.addSlickResult(test, ResultStatus.BROKEN_TEST, err)

    def addFailure(self, test, err):
        if not self.enabled:
            return
        if self.mode == 'schedule':
            sys.exit(0)
            return
        self.addSlickResult(test, ResultStatus.FAIL, err)

    def finalize(self, result):
        global testrun
        if not self.enabled or self.mode == 'schedule':
            return
        elif self.use_existing_testrun:
            testrun = self.slick.testruns(testrun.id).get()
            if testrun.resultsByStatus.NO_RESULT == 0:
                # finish testrun
                testrun.runFinished = int(round(time.time() * 1000))
                testrun.state = RunStatus.FINISHED
                self.slick.testruns(testrun).update()
        self.slick.finish_testrun()


