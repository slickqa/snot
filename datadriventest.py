from nose.tools import istest
from nose.tools import assert_not_equal
from snot import Requirements

__author__ = 'Jason Corbett'


@istest
def test_data_driven():
    test_data = [
        ['Test1', 'arg2', Requirements(['one', 'two'])],
        ['Test2', 'arg2', 'foo'],
        ['Test3', 'arg2', 'bar'],
    ]
    for data in test_data:
        yield ddt, data[0], data[1], data[2]


def ddt(test_name, argument, requirements):
    """Test: {0}"""
    assert_not_equal(test_name, argument, "The test name \"{}\" should not equal the argument \"{}\"".format(test_name,
                                                                                                             argument))


class DataDrivenTestClass(object):

    @istest
    def test_data_driven_inside_class(self):
        test_data = [
            ['Test1', 'Test1'],
            ['Test1', 'Test2'],
            ['Test1', 'Test3']
        ]
        for data in test_data:
            yield self.verify_not_equals, data[0], data[1]

    def verify_not_equals(self, first, second):
        """Verify {0} does not equal {1}"""
