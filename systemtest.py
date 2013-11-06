"""
The purpose of this file is to test the various types of tests that nose
allows, with various types of options and inputs.  We want to verify that
all tests with the name (should fail) actually do fail, and all results
get reported.
"""
__author__ = 'jcorbett'

import nose
import unittest
from nose.tools import istest
import snot
import sys
import logging

from asserts import *

@istest
def basic_passing_test():
    pass

@istest
def add_file_test():
    """This test will add this python file to the result

    Add a file using snot's add_file(path) method.  Will require
    manual validation that the file was uploaded.

    :component: File Upload
    :author: Jason Corbett
    :steps:
        1. Call snot's add_file function with the path to the current file
    :expectedResults:
        1. The current python source file should be uploaded
    """
    this_file = __file__
    if this_file.endswith('pyc'):
        this_file = this_file.strip('c')
    snot.add_file(this_file)

@istest
def test_stdout_logging_captured():
    """

    Make sure that stdout, and logging are captured and uploaded
    as a file.  Manual Verification required.

    :component: File Upload
    :author: Jason Corbett
    :steps:
        1. print a sample message to stdout
        2. log a sample logging message
    :expectedResults:
        1. Nose Capture.txt has sample stdout message
        2. Nose Capture.txt has sample logging message
    """
    print "A Stdout Message"
    log = logging.getLogger("systemtests.test_stdout_stderr_logging_captured")
    log.info("A Logging Message")
    assert_true(False, "This test will always fail, so that we can see capturing")

class ClassicUnittest(unittest.TestCase):

    def setUp(self):
        self.log = logging.getLogger("systemtest.ClassicUnittest")
        self.log.debug("Inside setUp")

    def test_unittest_example(self):
        """Basic Unittest Testcase

        This test is here to make sure that tests written using python's standard unittest framework
        can be executed by nose and reported by slick.

        :component: DocStringMetaData
        :author: Jason Corbett
        :steps:
            1. Run this test
        :expectedResults:
            1. You see a debug message inside setup, an info message inside the test (showing the python version), and another debug message from tearDown
        """

        self.log.info("Inside unittest for Python %s", sys.version)

    def test_simple_skip_example(self):
        """Simple Skip Example Test

        This test checks what happens when a test raises a skip Exception from unittest.

        :component: NosePlugin
        :author: Jason Corbett
        """
        self.log.debug("This test should skip")
        raise unittest.SkipTest("We always want to skip this test")

    def test_logging_exception(self):
        """Logging an exception Test

        This test makes sure the logging capability in slick can log an exception properly.

        :component: NosePlugin
        :author: Jason Corbett
        :steps:
            1. Raise and exception in a try block, logging it in the except blog
        :expectedResults:
            1. The result should contain a logging entry that shows the log message with the exception information.
        """
        try:
            raise Exception("A generic exception")
        except:
            self.log.warn("An exception was raised!", exc_info=sys.exc_info())

    def tearDown(self):
        self.log.debug("Inside tearDown")





@istest
def generator_test():
    inputs = ["first", "second", "third"]
    expected = ["first", "not second", "third"]
    for i in range(len(inputs)):
        yield check_expected_equals_input, inputs[i], expected[i]

def check_expected_equals_input(data, expected):
    """Generator Test

    This test takes an input data and compares it to expected.

    :component: NosePlugin
    :author: Jason Corbett

    :steps:
        1. Compare the data against the expected
    :expectedResults:
        1. The two should be equal
    """
    assert_equal(data, expected)