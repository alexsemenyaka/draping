import functools
import inspect
import threading
from typing import Any, Callable, List, Tuple

_patch_lock = threading.Lock()


def _get_parent_and_name(func_obj: Callable) -> tuple[Any, str]:
    """Finds the parent object (class or module) of a function or method."""
    if inspect.ismethod(func_obj):
        return func_obj.__self__.__class__, func_obj.__name__
    if inspect.isfunction(func_obj):
        if '.' in func_obj.__qualname__:
            parts = func_obj.__qualname__.split('.')
            func_name = parts.pop()
            class_name = parts.pop()
            module = inspect.getmodule(func_obj)
            parent = getattr(module, class_name, None)
            if parent is None:
                raise TypeError(f"Could not find parent class for {func_obj.__qualname__}")
            return parent, func_name
        else:
            return inspect.getmodule(func_obj), func_obj.__name__
    raise TypeError(f"Cannot determine parent for object of type {type(func_obj)}")


def _deconstruct_chain(func_obj: Callable) -> dict:
    """Deconstructs a function's decorator chain into its core components.

    This helper inspects a potentially decorated function and returns its
    parent object, name, the original undecorated function, a list of
    applied decorator instances, and the descriptor type (if any).

    Args:
        func_obj (Callable): The function or method to deconstruct.

    Returns:
        A dictionary containing the function's structural information.
    """
    parent, func_name = _get_parent_and_name(func_obj)
    original_attr = inspect.getattr_static(parent, func_name)

    is_staticmethod = isinstance(original_attr, staticmethod)
    is_classmethod = isinstance(original_attr, classmethod)
    
    chain = []
    current = original_attr
    while current:
        chain.append(current)
        current = getattr(current, '__wrapped__', None)

    original_func = chain.pop() if chain else original_attr
    wrappers = list(reversed(chain))
    decorators = [getattr(w, '_applied_decorator', None) for w in wrappers]

    descriptor_type = None
    if is_staticmethod:
        descriptor_type = 'static'
    elif is_classmethod:
        descriptor_type = 'class'

    return {
        "parent": parent,
        "func_name": func_name,
        "original_func": original_func,
        "decorators": decorators,
        "descriptor_type": descriptor_type,
    }


def decorate(
    decorator: Callable,
    *functions: Callable,
    decorate_again: bool = False,
    raise_on_error: bool = True
) -> tuple[bool, ...]:
    """Dynamically applies a decorator to functions or methods.

    This function monkey-patches the given functions, wrapping them with the
    provided decorator. It is thread-safe and handles regular functions,
    instance methods, class methods, and static methods correctly.

    Args:
        decorator (Callable): The decorator to apply.
        *functions (Callable): A variable number of functions to be decorated.
        decorate_again (bool): If False (default), avoids re-applying a
            decorator instance if it's already in the function's wrapper
            chain. If True, the decorator will be applied again.
        raise_on_error (bool): If True (default), raises an exception on
            failure. If False, suppresses exceptions and returns False for
            the failed function.

    Returns:
        A tuple of booleans, with each value indicating whether the
        corresponding function was successfully decorated (True) or not (False).
    """
    results = []
    for func_obj in functions:
        try:
            with _patch_lock: # Granular lock for each function
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

                if is_staticmethod:
                    final_obj = staticmethod(decorated_function)
                elif is_classmethod:
                    final_obj = classmethod(decorated_function)
                else:
                    final_obj = decorated_function
                
                setattr(parent, func_name, final_obj)
                results.append(True)

        except (TypeError, AttributeError):
            if raise_on_error:
                raise
            results.append(False)
            
    return tuple(results)


def redecorate(
    deco1: Callable,
    deco2: Callable,
    *functions: Callable,
    change_all: bool = True,
    raise_on_error: bool = True
) -> tuple[bool, ...]:
    """Finds all applications of deco1 on a function and replaces them with deco2.

    Args:
        deco1 (Callable): The old decorator instance to find.
        deco2 (Callable): The new decorator instance to replace with.
        *functions (Callable): The function(s) to process.
        change_all (bool): If True (default), replaces all occurrences of
            deco1 in the wrapper chain. If False, only replaces the
            outermost occurrence.
        raise_on_error (bool): If True (default), raises an exception on
            failure. If False, suppresses exceptions and returns False for
            the failed function.

    Returns:
        A tuple of booleans, indicating if a replacement occurred for each
        respective function.
    """
    results = []
    for func_obj in functions:
        try:
            with _patch_lock:
                parent, func_name = _get_parent_and_name(func_obj)
                original_attr = inspect.getattr_static(parent, func_name)
                
                # Deconstruct the wrapper chain
                chain = []
                current = original_attr
                while current:
                    chain.append(current)
                    current = getattr(current, '__wrapped__', None)
                
                if len(chain) <= 1: # Not decorated
                    results.append(False)
                    continue

                original_func = chain.pop()
                wrappers = list(reversed(chain)) # Outermost wrapper is last

                # Rebuild the decorator list, swapping deco1 for deco2
                decorators_to_apply = []
                changed = False
                for wrapper in wrappers:
                    applied_deco = getattr(wrapper, '_applied_decorator', None)
                    if applied_deco is deco1:
                        decorators_to_apply.append(deco2)
                        changed = True
                        if not change_all:
                            # Add the rest of the original decorators and stop swapping
                            remaining_wrappers = wrappers[len(decorators_to_apply):]
                            decorators_to_apply.extend(
                                getattr(w, '_applied_decorator', lambda f: w) for w in remaining_wrappers
                            )
                            break
                    else:
                        # Re-apply the original decorator
                        decorators_to_apply.append(applied_deco or (lambda f: wrapper))

                if not changed:
                    results.append(False)
                    continue

                # Reconstruct the function with the new decorator chain
                rebuilt_func = original_func
                for deco in decorators_to_apply:
                    rebuilt_func = deco(rebuilt_func)

                # Handle static/class methods
                is_staticmethod = isinstance(original_attr, staticmethod)
                is_classmethod = isinstance(original_attr, classmethod)
                if is_staticmethod:
                    final_obj = staticmethod(rebuilt_func)
                elif is_classmethod:
                    final_obj = classmethod(rebuilt_func)
                else:
                    final_obj = rebuilt_func
                
                setattr(parent, func_name, final_obj)
                results.append(True)

        except (TypeError, AttributeError):
            if raise_on_error:
                raise
            results.append(False)
            
    return tuple(results)


def undecorate(
    func: Callable,
    decorator_to_remove: Optional[Callable] = None,
    *,
    if_topmost: bool = False,
    raise_on_error: bool = True
) -> bool:
    """Dynamically and thread-safely removes a decorator from a function.

    This function can remove either the outermost decorator or a specific
    decorator instance from anywhere in the wrapper chain.

    Args:
        func (Callable): The decorated function or method to undecorate.
        decorator_to_remove (Optional[Callable]): The specific decorator
            instance to remove. If None (default), the outermost decorator
            is removed.
        if_topmost (bool): If True, `decorator_to_remove` is only removed
            if it is the outermost decorator. If it's found deeper in the
            chain, no action is taken. Defaults to False.
        raise_on_error (bool): If True (default), raises an exception on
            failure. If False, suppresses exceptions and returns False.

    Returns:
        True if a decorator was successfully removed, False otherwise.
    """
    try:
        with _patch_lock:
            chain_info = _deconstruct_chain(func)
            decorators = chain_info["decorators"]

            if not decorators:
                return False  # Not decorated, nothing to do.

            new_decorators = list(decorators)  # Create a mutable copy
            changed = False

            if decorator_to_remove is None:
                # Case 1: Default behavior - remove the outermost decorator.
                new_decorators.pop()
                changed = True
            elif if_topmost:
                # Case 2: Remove the specified decorator only if it's topmost.
                if decorators[-1] is decorator_to_remove:
                    new_decorators.pop()
                    changed = True
            else:
                # Case 3: Find and remove the outermost occurrence of a specific decorator.
                # We iterate backwards to find the last (outermost) instance first.
                for i in range(len(new_decorators) - 1, -1, -1):
                    if new_decorators[i] is decorator_to_remove:
                        new_decorators.pop(i)
                        changed = True
                        break  # Remove only one instance

            if not changed:
                return False

            # Rebuild the function from the inside out with the new decorator chain
            rebuilt_func = chain_info["original_func"]
            for deco in new_decorators:
                if deco:  # A decorator could be None if not tagged
                    rebuilt_func = deco(rebuilt_func)

            # Re-apply the original descriptor (staticmethod, etc.) if it existed
            descriptor = chain_info["descriptor_type"]
            if descriptor == 'static':
                final_obj = staticmethod(rebuilt_func)
            elif descriptor == 'class':
                final_obj = classmethod(rebuilt_func)
            else:
                final_obj = rebuilt_func
            
            # Apply the patch
            setattr(chain_info["parent"], chain_info["func_name"], final_obj)
            return True

    except (TypeError, AttributeError):
        if raise_on_error:
            raise
        return False
