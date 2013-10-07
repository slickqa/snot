__author__ = 'jcorbett'

import snot
from asserts import *

from nose.tools import istest
from nose.plugins import Plugin


@istest
def test_plugin_inherits_nose_plugin():
    """SlickAsSnot inherits from nose.plugins.Plugin"""
    assert_is_instance(snot.SlickAsSnotPlugin(), Plugin)
