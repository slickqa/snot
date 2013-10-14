"""
The purpose of this file is to test the various types of tests that nose
allows, with various types of options and inputs.  We want to verify that
all tests with the name (should fail) actually do fail, and all results
get reported.
"""
__author__ = 'jcorbett'

import nose
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