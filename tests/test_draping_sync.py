# tests/test_draping_sync.py

import pytest
import importlib
from draping import decorate, redecorate, undecorate
import tests.draping_subjects as subjects

class TestDrapingSync:
    """Tests for the synchronous draping functions."""

    def setup_method(self):
        """Перезагружаем модуль с субъектами, чтобы обеспечить чистое состояние для каждого теста."""
        importlib.reload(subjects)

    def test_decorate_and_undecorate_simple(self):
        subjects.my_func_g(); assert subjects.log_g_sync == ["my_func_run"]; subjects.log_g_sync.clear()
        assert decorate(subjects.deco_g1, subjects.my_func_g) == (True,)
        subjects.my_func_g(); assert subjects.log_g_sync == ["deco1", "my_func_run"]; subjects.log_g_sync.clear()
        assert undecorate(subjects.my_func_g) is True
        subjects.my_func_g(); assert subjects.log_g_sync == ["my_func_run"]

    def test_decorate_again_flag(self):
        assert decorate(subjects.deco_g1, subjects.my_func_g) == (True,)
        assert decorate(subjects.deco_g1, subjects.my_func_g, decorate_again=False) == (False,)
        subjects.my_func_g(); assert subjects.log_g_sync.count("deco1") == 1; subjects.log_g_sync.clear()
        assert decorate(subjects.deco_g1, subjects.my_func_g, decorate_again=True) == (True,)
        subjects.my_func_g(); assert subjects.log_g_sync.count("deco1") == 2

    def test_redecorate(self):
        decorate(subjects.deco_g1, subjects.my_func_g)
        subjects.my_func_g(); assert subjects.log_g_sync == ["deco1", "my_func_run"]; subjects.log_g_sync.clear()
        assert redecorate(subjects.deco_g1, subjects.deco_g2, subjects.my_func_g) == (True,)
        subjects.my_func_g(); assert subjects.log_g_sync == ["deco2", "my_func_run"]
    
    def test_undecorate_specific_and_topmost(self):
        decorate(subjects.deco_g1, subjects.my_func_g)
        decorate(subjects.deco_g2, subjects.my_func_g)
        decorate(subjects.deco_g3, subjects.my_func_g)
        
        subjects.my_func_g(); assert subjects.log_g_sync == ["deco3", "deco2", "deco1", "my_func_run"]; subjects.log_g_sync.clear()
        assert undecorate(subjects.my_func_g, subjects.deco_g1, if_topmost=True) is False
        assert undecorate(subjects.my_func_g, subjects.deco_g2) is True
        subjects.my_func_g(); assert subjects.log_g_sync == ["deco3", "deco1", "my_func_run"]; subjects.log_g_sync.clear()
        assert undecorate(subjects.my_func_g, decorator_to_remove=None) is True
        subjects.my_func_g(); assert subjects.log_g_sync == ["deco1", "my_func_run"]

    def test_decorate_all_method_types(self):
        instance = subjects.MyClass()
        class_deco = subjects.simple_decorator_factory("class_deco", subjects.MyClass._log)
        
        assert decorate(
            class_deco, subjects.MyClass.instance_method, subjects.MyClass.class_method, subjects.MyClass.static_method
        ) == (True, True, True)

        instance.instance_method(); assert subjects.MyClass._log == ["class_deco", "instance_method_run"]; subjects.MyClass._log.clear()
        subjects.MyClass.class_method(); assert subjects.MyClass._log == ["class_deco", "class_method_run"]; subjects.MyClass._log.clear()
        instance.static_method(); assert subjects.MyClass._log == ["class_deco", "static_method_run"]

    def test_error_handling(self):
        def unpatched_func(): pass
        assert undecorate(unpatched_func, raise_on_error=False) is False
        with pytest.raises(TypeError): undecorate(unpatched_func, raise_on_error=True)

    def test_undecorate_specific_from_middle_path(self):
        """
        Specifically tests removing a decorator from the middle of the chain
        to cover a specific branch in the undecorate function.
        """
        # A decorator that is not and will not be applied to the chain
        deco_unused = subjects.simple_decorator_factory("deco_unused", subjects.log_g_sync)

        # 1. Setup a clean, three-layer decorator chain
        # Final state is: deco_g3(deco_g2(deco_g1(subjects.my_func_g)))
        decorate(subjects.deco_g1, subjects.my_func_g)
        decorate(subjects.deco_g2, subjects.my_func_g)
        decorate(subjects.deco_g3, subjects.my_func_g)

        # 2. Test the "not found" case explicitly with if_topmost=False
        # This executes the loop but finds no match.
        assert undecorate(subjects.my_func_g, deco_unused, if_topmost=False) is False
        
        # Verify the chain is still intact
        subjects.my_func_g()
        assert subjects.log_g_sync == ["deco3", "deco2", "deco1", "my_func_run"]
        subjects.log_g_sync.clear()

        # 3. Test the "found and removed" case for a middle decorator
        # This executes the loop and successfully finds, pops, and breaks.
        assert undecorate(subjects.my_func_g, subjects.deco_g2, if_topmost=False) is True

        # Verify that only deco2 is gone
        subjects.my_func_g()
        assert subjects.log_g_sync == ["deco3", "deco1", "my_func_run"]

    def test_decorate_and_redecorate_error_handling(self):
        """
        Covers the try/except blocks in both decorate() and redecorate()
        by using decorators that raise exceptions.
        """
        # A decorator that will raise an AttributeError when called
        def attribute_error_decorator(func):
            raise AttributeError("This is a simulated attribute error")

        # A decorator that will raise a TypeError when called
        def type_error_decorator(func):
            raise TypeError("This is a simulated type error")

        # Test that exceptions are raised by default (raise_on_error=True)
        with pytest.raises(AttributeError, match="simulated attribute error"):
            decorate(attribute_error_decorator, subjects.my_func_g)

        with pytest.raises(TypeError, match="simulated type error"):
            decorate(type_error_decorator, subjects.my_func_g)

        # Test that exceptions are suppressed when raise_on_error=False
        result_attr = decorate(attribute_error_decorator, subjects.my_func_g, raise_on_error=False)
        assert result_attr == (False,)

        # Setup: Decorate with a valid decorator first
        good_deco = subjects.simple_decorator_factory("good_deco")
        decorate(good_deco, subjects.my_func_g)

        # Test that exceptions are raised by default when redecorating
        with pytest.raises(AttributeError, match="simulated attribute error"):
            redecorate(good_deco, attribute_error_decorator, subjects.my_func_g)

        with pytest.raises(TypeError, match="simulated type error"):
            redecorate(good_deco, type_error_decorator, subjects.my_func_g)
        
        # Test that exceptions are suppressed when redecorating with raise_on_error=False
        result_redecorate = redecorate(good_deco, attribute_error_decorator, subjects.my_func_g, raise_on_error=False)
        assert result_redecorate == (False,)

    def test_redecorate_decorator_not_found(self):
        """
        Covers the branch in redecorate() where the decorator to be
        replaced is not found on the function.
        """
        decorate(subjects.deco_g1, subjects.my_func_g)

        subjects.my_func_g()
        assert subjects.log_g_sync == ["deco1", "my_func_run"]
        subjects.log_g_sync.clear()

        changed = redecorate(subjects.deco_g2, subjects.deco_g3, subjects.my_func_g)

        assert changed == (False,)
        subjects.my_func_g()
        assert subjects.log_g_sync == ["deco1", "my_func_run"]

    def test_redecorate_no_change_scenarios(self):
        """
        Covers branches in redecorate() where no replacement occurs.
        """
        deco_unused = subjects.simple_decorator_factory("deco_unused")

        decorate(subjects.deco_g1, subjects.my_func_g)
        subjects.my_func_g()
        assert subjects.log_g_sync == ["deco1", "my_func_run"]
        subjects.log_g_sync.clear()

        changed = redecorate(deco_unused, subjects.deco_g2, subjects.my_func_g)
        assert changed == (False,)

        subjects.my_func_g()
        assert subjects.log_g_sync == ["deco1", "my_func_run"]

    def test_raises_error_on_non_callable_object(self):
        """
        Covers the initial `callable()` check in the helper function by passing
        a non-callable object to the draping functions.
        """
        not_a_function = 123  # An integer is not callable
        dummy_decorator = lambda f: f

        # For decorate
        with pytest.raises(TypeError):
            decorate(dummy_decorator, not_a_function)
        assert decorate(dummy_decorator, not_a_function, raise_on_error=False) == (False,)

        # For redecorate
        with pytest.raises(TypeError):
            redecorate(dummy_decorator, dummy_decorator, not_a_function)
        assert redecorate(dummy_decorator, dummy_decorator, not_a_function, raise_on_error=False) == (False,)

        # For undecorate
        with pytest.raises(TypeError):
            undecorate(not_a_function)
        assert undecorate(not_a_function, raise_on_error=False) is False
