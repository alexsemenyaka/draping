"""
draping: Apply and remove decorators to the fumctions (both sync and async) on-fly
"""
import sys
import re
import functools
import inspect
import threading

from typing import Any, Callable, Optional


_patch_lock = threading.Lock()


def _get_parent_and_name(func_obj: Callable) -> tuple[Any, str]:
    """
    Finds the parent object (class or module) of a function or method.
    """
    if not callable(func_obj):
        raise TypeError(f"Object of type {type(func_obj)} is not a function or method.")
    if "<locals>" in func_obj.__qualname__:
        raise TypeError(
            f"Cannot dynamically patch function '{func_obj.__qualname__}' "
            "because it is a local function defined inside another function. "
            "Only module-level or class-level functions can be draped."
        )
    try:
        path = func_obj.__qualname__.split('.')
        func_name = path[-1]
        module_name = func_obj.__module__
        module = sys.modules[module_name]
        if len(path) == 1:
            return module, func_name
        parent = module
        for part in path[:-1]:
            parent = getattr(parent, part)
        return parent, func_name
    except (AttributeError, KeyError) as e:  # pragma: no cover
        raise TypeError(f"Could not determine parent for {func_obj}") from e


def _deconstruct_chain(func_obj: Callable) -> dict:
    """Deconstructs a function's decorator chain into its core components."""
    parent, func_name = _get_parent_and_name(func_obj)
    original_attr = inspect.getattr_static(parent, func_name)
    is_staticmethod = isinstance(original_attr, staticmethod)
    is_classmethod = isinstance(original_attr, classmethod)
    chain, current = [], original_attr
    while current:
        chain.append(current)
        current = getattr(current, '__wrapped__', None)
    original_func = chain.pop() if chain else original_attr
    wrappers = list(reversed(chain))
    decorators = [getattr(w, '_applied_decorator', None) for w in wrappers]
    descriptor_type = 'static' if is_staticmethod else 'class' if is_classmethod else None
    return {
        "parent": parent, "func_name": func_name, "original_attr": original_attr,
        "original_func": original_func, "decorators": decorators,
        "descriptor_type": descriptor_type,
    }


def decorate(
    decorator: Callable, *functions: Callable,
    decorate_again: bool = False, raise_on_error: bool = True
) -> tuple[bool, ...]:
    """Dynamically applies a decorator to one or more functions or methods.

    This function monkey-patches the given functions in their original
    modules or classes, wrapping them with the provided decorator. The operation
    is thread-safe and correctly handles regular functions, instance methods,
    class methods, and static methods.

    Args:
        decorator (Callable): The decorator to apply. This should be a
            callable that takes a function and returns a new function.
        *functions (Callable): A variable number of functions or methods
            to be decorated.
        decorate_again (bool): If False (default), this function will traverse
            the existing wrapper chain and avoid re-applying the same decorator
            instance if it's already present. If True, the decorator will be
            applied again, creating a nested stack.
        raise_on_error (bool): If True (default), raises TypeError or
            AttributeError on failure. If False, suppresses such exceptions
            and returns False in the result tuple for the failed function.

    Returns:
        tuple[bool, ...]: A tuple of booleans, where each value indicates
        whether the corresponding function was successfully decorated (True)
        or not (False).

    Raises:
        TypeError: If an object passed in `functions` is not a callable or
            its parent module/class cannot be determined. Raised only if
            `raise_on_error` is True.
        AttributeError: If a function name cannot be found on its determined
            parent object. Raised only if `raise_on_error` is True.
    """
    results = []
    for func_obj in functions:
        try:
            with _patch_lock:
                parent, func_name = _get_parent_and_name(func_obj)
                original_attr = inspect.getattr_static(parent, func_name)
                is_staticmethod = isinstance(original_attr, staticmethod)
                is_classmethod = isinstance(original_attr, classmethod)
                func_to_decorate = original_attr.__func__ if (is_staticmethod or is_classmethod) else original_attr

                if not decorate_again:
                    current_func = original_attr
                    already_decorated = False
                    while hasattr(current_func, '__wrapped__'):
                        if getattr(current_func, '_applied_decorator', None) is decorator:
                            already_decorated = True
                            break
                        current_func = current_func.__wrapped__
                    if already_decorated:
                        results.append(False)
                        continue

                decorated_function = decorator(func_to_decorate)
                functools.update_wrapper(decorated_function, func_to_decorate)
                setattr(decorated_function, '_applied_decorator', decorator)

                final_obj = decorated_function
                if is_staticmethod:
                    final_obj = staticmethod(decorated_function)
                elif is_classmethod:
                    final_obj = classmethod(decorated_function)
                
                setattr(parent, func_name, final_obj)
                results.append(True)
        except (TypeError, AttributeError):
            if raise_on_error:
                raise
            results.append(False)
    return tuple(results)


def redecorate(
    deco1: Callable, deco2: Callable, *functions: Callable,
    change_all: bool = True, raise_on_error: bool = True
) -> tuple[bool, ...]:
    """Finds and replaces a decorator instance on a function's wrapper chain.

    This function inspects the chain of decorators on each function, finds all
    applications of `deco1`, and replaces them with `deco2`. The operation
    is thread-safe.

    Args:
        deco1 (Callable): The old decorator instance to find.
        deco2 (Callable): The new decorator instance to replace `deco1` with.
        *functions (Callable): The function(s) to process.
        change_all (bool): If True (default), replaces all occurrences of
            `deco1` in the wrapper chain. If False, only replaces the
            outermost occurrence of `deco1`.
        raise_on_error (bool): If True (default), raises an exception on
            failure. If False, suppresses exceptions and returns False for
            the failed function.

    Returns:
        tuple[bool, ...]: A tuple of booleans, indicating if a replacement
        occurred for each respective function.
    """
    results = []
    for func_obj in functions:
        try:
            with _patch_lock:
                chain_info = _deconstruct_chain(func_obj)
                decorators = chain_info["decorators"]
                if deco1 not in decorators:
                    results.append(False)
                    continue

                new_decorators = []
                changed = False
                replaced_once = False
                for deco in decorators:
                    if deco is deco1 and (change_all or not replaced_once):
                        new_decorators.append(deco2)
                        changed = True
                        replaced_once = True
                    else:
                        new_decorators.append(deco)
                if not changed:
                    results.append(False)
                    continue

                rebuilt_func = chain_info["original_func"]
                # --- FIX IS HERE: Re-apply decorators and TAG them ---
                for deco in new_decorators:
                    if deco:
                        new_wrapper = deco(rebuilt_func)
                        functools.update_wrapper(new_wrapper, rebuilt_func)
                        setattr(new_wrapper, '_applied_decorator', deco)
                        rebuilt_func = new_wrapper
                # --- END OF FIX ---

                descriptor = chain_info["descriptor_type"]
                final_obj = rebuilt_func
                if descriptor == 'static':
                    final_obj = staticmethod(rebuilt_func)
                elif descriptor == 'class':
                    final_obj = classmethod(rebuilt_func)
                
                setattr(chain_info["parent"], chain_info["func_name"], final_obj)
                results.append(True)
        except (TypeError, AttributeError):
            if raise_on_error:
                raise
            results.append(False)
    return tuple(results)


def undecorate(
    func: Callable, decorator_to_remove: Optional[Callable] = None, *,
    if_topmost: bool = False, raise_on_error: bool = True
) -> bool:
    """Dynamically and thread-safely removes a decorator from a function.

    This function can remove either the outermost decorator or a specific
    decorator instance from anywhere in the wrapper chain. It relies on the
    decorators having been applied in a way that preserves the `__wrapped__`
    attribute (e.g., using `@functools.wraps`).

    Args:
        func (Callable): The decorated function or method to undecorate.
        decorator_to_remove (Optional[Callable]): The specific decorator
            instance to remove. If None (default), the outermost decorator
            in the chain is removed.
        if_topmost (bool): A keyword-only argument. If True, the
            `decorator_to_remove` is only removed if it is the absolute
            outermost decorator. If it's found deeper in the chain, no
            action is taken. Defaults to False.
        raise_on_error (bool): If True (default), raises an exception on
            failure. If False, suppresses exceptions and returns False.

    Returns:
        True if a decorator was successfully removed, False otherwise.

    Raises:
        TypeError: If the function cannot be undecorated (e.g., it is not
            decorated, or the decorator did not use `@functools.wraps`).
            Raised only if `raise_on_error` is True.
    """
    try:
        with _patch_lock:
            chain_info = _deconstruct_chain(func)
            decorators = chain_info["decorators"]
            if not decorators: return False

            new_decorators = list(decorators)
            changed = False

            if decorator_to_remove is None:
                new_decorators.pop()
                changed = True
            elif if_topmost:
                if new_decorators and new_decorators[-1] is decorator_to_remove:
                    new_decorators.pop()
                    changed = True
            else:
                for i in range(len(new_decorators) - 1, -1, -1):
                    if new_decorators[i] is decorator_to_remove:
                        new_decorators.pop(i)
                        changed = True
                        break
            
            if not changed: return False

            rebuilt_func = chain_info["original_func"]
            for deco in new_decorators:
                if deco:
                    new_wrapper = deco(rebuilt_func)
                    functools.update_wrapper(new_wrapper, rebuilt_func)
                    setattr(new_wrapper, '_applied_decorator', deco)
                    rebuilt_func = new_wrapper

            descriptor = chain_info["descriptor_type"]
            final_obj = rebuilt_func
            if descriptor == 'static':
                final_obj = staticmethod(rebuilt_func)
            elif descriptor == 'class':
                final_obj = classmethod(rebuilt_func)
            
            setattr(chain_info["parent"], chain_info["func_name"], final_obj)
            return True
    except (TypeError, AttributeError):
        if raise_on_error:
            raise
        return False

def _get_callables(obj: Any) -> tuple[Callable, ...]:
    if inspect.isclass(obj):
        return tuple(getattr(obj, name) for name in dir(obj)
                     if callable(getattr(obj, name)) and not name.startswith("__"))
    elif isinstance(obj, (list, tuple)):
        return tuple(f for f in obj if callable(f))
    raise TypeError("First argument must be a class or a list/tuple of callables.")

def start_with(obj: Any, *prefixes: str) -> tuple[Callable, ...]:
    """Filters callables whose names start with any of the given prefixes.

    Args:
        obj: A class (to extract its methods) or a list/tuple of callables.
        *prefixes: One or more string prefixes to match.

    Returns:
        A tuple of filtered callables.
    """
    callables = _get_callables(obj)
    return tuple(f for f in callables if any(f.__name__.startswith(p) for p in prefixes))

def not_start_with(obj: Any, *prefixes: str) -> tuple[Callable, ...]:
    """Filters callables whose names do not start with any of the given prefixes.

    Args:
        obj: A class (to extract its methods) or a list/tuple of callables.
        *prefixes: One or more string prefixes to exclude.

    Returns:
        A tuple of filtered callables.
    """
    callables = _get_callables(obj)
    return tuple(f for f in callables if not any(f.__name__.startswith(p) for p in prefixes))

def contain(obj: Any, *substrings: str) -> tuple[Callable, ...]:
    """Filters callables whose names contain any of the given substrings.

    Args:
        obj: A class (to extract its methods) or a list/tuple of callables.
        *substrings: One or more substrings to match.

    Returns:
        A tuple of filtered callables.
    """
    callables = _get_callables(obj)
    return tuple(f for f in callables if any(s in f.__name__ for s in substrings))

def not_contain(obj: Any, *substrings: str) -> tuple[Callable, ...]:
    """Filters callables whose names do not contain any of the given substrings.

    Args:
        obj: A class (to extract its methods) or a list/tuple of callables.
        *substrings: One or more substrings to exclude.

    Returns:
        A tuple of filtered callables.
    """
    callables = _get_callables(obj)
    return tuple(f for f in callables if not any(s in f.__name__ for s in substrings))

def positive_re(obj: Any, *patterns: str) -> tuple[Callable, ...]:
    """Filters callables whose names match any of the given regex patterns.

    Args:
        obj: A class (to extract its methods) or a list/tuple of callables.
        *patterns: One or more regex patterns (as strings) to match.

    Returns:
        A tuple of filtered callables.
    """
    callables = _get_callables(obj)
    compiled = [re.compile(p) for p in patterns]
    return tuple(f for f in callables if any(c.search(f.__name__) for c in compiled))

def negative_re(obj: Any, *patterns: str) -> tuple[Callable, ...]:
    """Filters callables whose names do not match any of the given regex patterns.

    Args:
        obj: A class (to extract its methods) or a list/tuple of callables.
        *patterns: One or more regex patterns (as strings) to exclude.

    Returns:
        A tuple of filtered callables.
    """
    callables = _get_callables(obj)
    compiled = [re.compile(p) for p in patterns]
    return tuple(f for f in callables if not any(c.search(f.__name__) for c in compiled))
