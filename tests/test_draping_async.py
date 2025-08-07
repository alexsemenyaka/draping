# tests/test_draping_async.py

import pytest
import asyncio
import importlib
from draping import decorate, redecorate, undecorate
import tests.draping_subjects as subjects

@pytest.mark.asyncio
class TestDrapingAsync:
    """Tests for the draping functions with async code."""

    def setup_method(self):
        importlib.reload(subjects)

    async def test_decorate_and_undecorate_simple_async(self):
        await subjects.my_func_g_async()
        assert subjects.log_g_async == ["my_func_g_async_run"]
        subjects.log_g_async.clear()

        assert decorate(subjects.deco_g_async1, subjects.my_func_g_async) == (True,)
        await subjects.my_func_g_async()
        assert subjects.log_g_async == ["deco_async1", "my_func_g_async_run"]
        subjects.log_g_async.clear()
        
        assert undecorate(subjects.my_func_g_async) is True
        await subjects.my_func_g_async()
        assert subjects.log_g_async == ["my_func_g_async_run"]

    async def test_redecorate_async(self):
        decorate(subjects.deco_g_async1, subjects.my_func_g_async)
        await subjects.my_func_g_async()
        assert subjects.log_g_async == ["deco_async1", "my_func_g_async_run"]
        subjects.log_g_async.clear()

        assert redecorate(subjects.deco_g_async1, subjects.deco_g_async2, subjects.my_func_g_async) == (True,)
        await subjects.my_func_g_async()
        assert subjects.log_g_async == ["deco_async2", "my_func_g_async_run"]

    async def test_decorate_all_async_method_types(self):
        instance = subjects.MyAsyncClass()
        class_deco = subjects.async_decorator_factory("async_class_deco", subjects.MyAsyncClass._log)
        
        assert decorate(
            class_deco, subjects.MyAsyncClass.instance_method, subjects.MyAsyncClass.class_method, subjects.MyAsyncClass.static_method
        ) == (True, True, True)

        await instance.instance_method()
        assert subjects.MyAsyncClass._log == ["async_class_deco", "instance_method_run"]
        subjects.MyAsyncClass._log.clear()

        await subjects.MyAsyncClass.class_method()
        assert subjects.MyAsyncClass._log == ["async_class_deco", "class_method_run"]
        subjects.MyAsyncClass._log.clear()

        await instance.static_method()
        assert subjects.MyAsyncClass._log == ["async_class_deco", "static_method_run"]
