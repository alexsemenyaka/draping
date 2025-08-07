"""
preps
"""
import asyncio
import functools
from typing import Callable

log_g_sync = []
def simple_decorator_factory(name: str, log: list = log_g_sync) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log.append(name)
            return func(*args, **kwargs)
        return wrapper
    return decorator

deco_g1 = simple_decorator_factory("deco1")
deco_g2 = simple_decorator_factory("deco2")
deco_g3 = simple_decorator_factory("deco3")
def my_func_g():
    log_g_sync.append("my_func_run")

class MyClass:
    _log = []
    def instance_method(self): self._log.append("instance_method_run")
    @classmethod
    def class_method(cls): cls._log.append("class_method_run")
    @staticmethod
    def static_method(): MyClass._log.append("static_method_run")


log_g_async = []
def async_decorator_factory(name: str, log: list = log_g_async) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            log.append(name)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

deco_g_async1 = async_decorator_factory("deco_async1")
deco_g_async2 = async_decorator_factory("deco_async2")
async def my_func_g_async():
    log_g_async.append("my_func_g_async_run")

class MyAsyncClass:
    _log = []
    async def instance_method(self): await asyncio.sleep(0); self._log.append("instance_method_run")
    @classmethod
    async def class_method(cls): await asyncio.sleep(0); cls._log.append("class_method_run")
    @staticmethod
    async def static_method(): await asyncio.sleep(0); MyAsyncClass._log.append("static_method_run")
