__author__ = 'jcorbett'

import snot
from asserts import *

from nose.tools import istest
from nose.plugins import Plugin

import sys
import unittest

@istest
def test_plugin_inherits_nose_plugin():
    """SlickAsSnot inherits from nose.plugins.Plugin

    Make sure that SlickAsSnot class in the snot namespace is available,
    can be instantiated, and the instance is an instance of nose.plugins.Plugin

    :component: Nose Plugin
    :author: Jason Corbett
    :steps:
        1. Check to see if SlickAsSnotPlugin is an instance of nose.plugins.Plugin
    :expectedResults:
        1. isinstance SlickAsSnotPlugin, nose.plugins.Plugin returns true
    """
    assert_is_instance(snot.SlickAsSnotPlugin(), Plugin)

@istest
def test_parse_doc_string():
    """Test the DocStringMetaData that it can parse a complicated example

    :component: DocStringMetaData
    :author: Jason Corbett
    :steps:
        1. Pass a function with a docstring conforming to the standard to DocStringMetaData
        2. Check for expected attributes
    :expectedResults:
        1. No exception raised
        2. All doc string attributes provided are seen inside DocStringMetaData
    """
    def testfunc():
        """Long Title Test

        Purpose paragraph test 1

        Purpose paragraph test 2

        :component: Component Test
        :author: Author Test
        :steps:
            1. Step 1 Test
            2. Step 2 Test
        :expectedResults:
            1. Step 1 Expected Result
            2. Step 2 Expected Result
        :requirements: Requirements Test
        :automationTool: Automation Tool Test
        :automationId: Automation Id Test
        :automationKey: Automation Key Test
        :automationConfiguration: Automation Configuration Test
        :tags: tags test 1, tags test 2
        """
        pass
    testdata = snot.DocStringMetaData(testfunc)
    assert_equal(u"Long Title Test", testdata.name, "The name should be set to 'Long Title Test'")
    assert_equal(u"Purpose paragraph test 1\n\nPurpose paragraph test 2", testdata.purpose, "The purpose field should have both paragraphs")
    assert_equal(u"Component Test", testdata.component, "The component should be set to 'Component Test'")
    assert_equal(u"Author Test", testdata.author, "The author should be set to 'Author Test'")
    assert_equal(u"Requirements Test", testdata.requirements, "The requirements should be set to 'Requirements Test'")
    assert_equal(u"Automation Tool Test", testdata.automationTool, "The automationTool should be set to 'Automation Tool Test'")
    assert_equal(u"Automation Id Test", testdata.automationId, "The automationId should be set to 'Automation Id Test'")
    assert_equal(u"Automation Key Test", testdata.automationKey, "The automationKey should be set to 'Automation Key Test'")
    assert_equal(u"Automation Configuration Test", testdata.automationConfiguration, "The automationConfiguration should be set to 'Automation Configuration Test'")
    assert_equal([u"tags test 1", u"tags test 2"], testdata.tags, "The tags should be set to ['tags test 1', 'tags test 2']")
    assert_equal([u"Step 1 Test", u"Step 2 Test"], testdata.steps, "The steps should be set to ['Step 1 Test', 'Step 2 Test']")
    assert_equal([u"Step 1 Expected Result", u"Step 2 Expected Result"], testdata.expectedResults, "The expectedResults should be set to ['Step 1 Expected Result', 'Step 2 Expected Result']")

@istest
def test_empty_docstring():
    """Functions with empty doc strings should not cause exceptions.

    Check to make sure that a function without a doc string, still is able to be used
    to get meta data from a function.  Most important is that it not throw an exception.

    :component: DocStringMetaData
    :author: Jason Corbett
    :steps:
        1. Instantiate an instance of DocStringMetaData on a function without a doc string
    :expectedResults:
        1. No exception should be thrown.
    """
    def testfunc():
        pass
    e = None
    try:
        snot.DocStringMetaData(testfunc)
    except:
        e = sys.exc_info()
    assert_is_none(e, "No exception should be thrown during instantiation of DocStringMetaData on an undocumented method")

@istest
def test_name_conversion():
    """Function with empty doc string should have a name converted from the function name

    When getting data about a function (test) without any doc string the name should be converted
    from the function's name.  In particular underscore characters should be converted to spaces,
    "test" at the beginning of the name should be removed, and The first character capitalized.

    :component: DocStringMetaData
    :author: Jason Corbett
    :steps:
        1. Instantiate an instance of DocStringMetaData on a function without a doc string
    :expectedResults:
        1. The name of the function should be converted to the test name
    """
    def test_function_name():
        pass
    testdata = snot.DocStringMetaData(test_function_name)
    assert_equal("Function name", testdata.name, "When a function has no docstring the function name should be converted into a nice name.")

@istest
def test_camel_case_name_conversion():
    """Function with empty doc string should have a name converted from the function name (camel case)

    When getting data about a function (test) without any doc string the name should be converted
    from the function's name.  In particular camel case names should be separated at the upper
    case letters, spaces added, and only the first letter left capitalized.

    :component: DocStringMetaData
    :author: Jason Corbett
    :steps:
        1. Instantiate an instance of DocStringMetaData on a function without a doc string
    :expectedResults:
        1. The name of the function should be converted to the test name
    """
    def testCamelCase():
        pass
    testdata = snot.DocStringMetaData(testCamelCase)
    assert_equal("Camel case", testdata.name, "When a function has no docstring the function name (in camel case) should be converted into a human friendly name.")

@istest
def test_name_conversion_with_docstring():
    """Function with a doc string, and without a first line has the name converted from function name

    When getting data about a function (test) with a doc string but without a name at the top,
    the name should be converted from the function's name.

    :component: DocStringMetaData
    :author: Jason Corbett
    :steps:
        1. Instantiate an instance of DocStringMetaData on a function with a doc string and without a test name
    :expectedResults:
        1. The name of the function should be converted to the test name
    """
    def testCamelCaseWithDocString():
        """
        Purpose Test

        :component: Test Component
        """
        pass
    testdata = snot.DocStringMetaData(testCamelCaseWithDocString)
    assert_equal("Camel case with doc string", testdata.name)
    assert_equal("Purpose Test", testdata.purpose)
    assert_equal("Test Component", testdata.component)

@istest
def test_name_conversion_with_test_at_end():
    """
    If the 'test' part of the name occurs at the end of the function name, the conversion to a nice name
    should catch it and take it out.

    :component: DocStringMetaData
    :author: Jason Corbett
    :steps:
        1. Instantiate an instance of DocStringMetaData on a function with a doc string and without a test name
           but with 'test' at the end of the name
    :expectedResults:
        1. The name of the function should be converted to the test name without test at the end of the name
    """

    def this_is_a_simple_test():
        pass
    testdata = snot.DocStringMetaData(this_is_a_simple_test)
    assert_equal("This is a simple", testdata.name)

class ExampleTests(unittest.TestCase):

    def test_unittest_testcase_method(self):
        pass
