# tests/test_helpers.py

import pytest
import re
from draping import (
    start_with, not_start_with, contain, not_contain, positive_re, negative_re
)

class TestClass:
    def add_user(self): pass
    def pay_bill(self): pass
    def report_error(self): pass
    def _private(self): pass
    def __dunder__(self): pass

    @classmethod
    def cls_add(cls): pass

    @staticmethod
    def stat_pay(): pass

def func_contain_sub(): pass

@pytest.fixture
def funcs_list():
    return [TestClass.add_user, TestClass.pay_bill, TestClass.report_error, func_contain_sub]

class TestHelpers:
    def test_get_callables_errors(self):
        with pytest.raises(TypeError):
            start_with(123)  # Not class or list/tuple

    def test_start_with(self, funcs_list):
        assert start_with(TestClass, "add", "pay") == (TestClass.add_user, TestClass.pay_bill)
        assert start_with(funcs_list, "report") == (TestClass.report_error,)
        assert start_with(TestClass) == ()  # No prefixes: empty

    def test_not_start_with(self, funcs_list):
        assert not_start_with(TestClass, "add", "pay") == (TestClass._private, TestClass.cls_add, TestClass.report_error, TestClass.stat_pay)
        assert not_start_with(funcs_list, "_") == tuple(funcs_list)  # No private in list
        assert not_start_with(TestClass) == (TestClass._private, TestClass.add_user, TestClass.cls_add, TestClass.pay_bill, TestClass.report_error, TestClass.stat_pay)  # No prefixes: all

    def test_contain(self, funcs_list):
        assert contain(TestClass, "add", "error") == (TestClass.add_user, TestClass.cls_add, TestClass.report_error)
        assert contain(funcs_list, "sub") == (func_contain_sub,)
        assert contain(TestClass) == ()  # No substrings: empty

    def test_not_contain(self, funcs_list):
        assert not_contain(TestClass, "add", "pay") == (TestClass._private, TestClass.report_error)
        assert not_contain(funcs_list, "error") == (TestClass.add_user, TestClass.pay_bill, func_contain_sub)
        assert not_contain(TestClass) == (TestClass._private, TestClass.add_user, TestClass.cls_add, TestClass.pay_bill, TestClass.report_error, TestClass.stat_pay)  # No substrings: all

    def test_positive_re(self, funcs_list):
        assert positive_re(TestClass, r'^add', r'error$') == (TestClass.add_user, TestClass.report_error)
        assert positive_re(funcs_list, r'con.*sub') == (func_contain_sub,)
        assert positive_re(TestClass) == ()  # No patterns: empty
        with pytest.raises(re.error):  # Invalid regex
            positive_re(TestClass, r'[')

    def test_negative_re(self, funcs_list):
        assert negative_re(TestClass, r'^add', r'pay') == (TestClass._private, TestClass.cls_add, TestClass.report_error)
        assert negative_re(funcs_list, r'error$') == (TestClass.add_user, TestClass.pay_bill, func_contain_sub)
        assert negative_re(TestClass) == (TestClass._private, TestClass.add_user, TestClass.cls_add, TestClass.pay_bill, TestClass.report_error, TestClass.stat_pay)  # No patterns: all
        with pytest.raises(re.error):  # Invalid regex
            negative_re(TestClass, r'[')
