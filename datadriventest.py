from nose.tools import istest
from nose.tools import assert_not_equal

__author__ = 'Jason Corbett'


@istest
def test_data_driven():
    test_data = [
        ['Test1', 'arg2'],
        ['Test2', 'arg2'],
        ['Test3', 'arg2'],
    ]
    for data in test_data:
        yield ddt, data[0], data[1]


def ddt(test_name, argument):
    """Test: {0}"""
    assert_not_equal(test_name, argument, "The test name \"{}\" should not equal the argument \"{}\"".format(test_name,
                                                                                                             argument))
