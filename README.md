[![PyPI version](https://img.shields.io/pypi/v/draping.svg)](https://pypi.org/project/draping/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/draping.svg)](https://pypi.org/project/draping/)
[![PyPI - License](https://img.shields.io/pypi/l/draping.svg)](https://pypi.org/project/draping/)
[![Coverage Status](https://coveralls.io/repos/github/alexsemenyaka/draping/badge.svg?branch=main)](https://coveralls.io/github/alexsemenyaka/draping?branch=main)
[![CI/CD Status](https://github.com/alexsemenyaka/draping/actions/workflows/ci.yml/badge.svg)](https://github.com/alexsemenyaka/draping/actions/workflows/ci.yml)

## WHAT IT IS

`draping` is a powerful, thread-safe utility module for dynamically applying, removing, and swapping decorators on functions and methods at runtime.

It allows you to perform live "surgery" on your code, which is invaluable for advanced debugging, testing, and even applying hotfixes to running applications without redeployment. It correctly handles synchronous and asynchronous functions, instance methods, class methods, and static methods.

## INTRO

Decorators are a simple but compelling concept in Python. Simply put, by 'decorating' a function or method, we replace it with our own, which then accepts the original function and whatever is passed to it as arguments. Then we are free to do anything, from simply calling the 'decorated' function (in which case our decorator does nothing at all) to completely replacing the functionality of the original function with our own (in which case the original function will do nothing).
This functionality is actively used for debugging, profiling, and controlling code execution, making it convenient to have the fact of profiling clearly visible. That is why a special syntax was invented, which looks like this:

```python
@decorator
def func(*args):
    ...
```

It's simple, straightforward, and elegant.
But sometimes you need to do something more sophisticated. For example, one day, you should strip the decoration from a function. Or you may want to decorate a function from another module.

Of course, these are entirely feasible tasks, and Python's power and flexibility make it easy to solve them. In theory. But as a rule, when they arise, you don't have much time to solve them.
That's why I wrote this module. It allows you to decorate the necessary functions 'on the fly', in a single line, at the moment you need it. Conversely, you can remove the decoration at any time (the standard syntax does not provide this option). What's more, you can replace one decorator with another if the first one is applied to a given function.
These are not features you need every day. But when you do need them, you can take advantage of the flexibility of this module to solve your problems as elegantly and efficiently as possible.


## Features

-   **Dynamic Decoration**: Apply any decorator to any function or method long after it has been defined.
-   **Dynamic Undecoration**: Remove decorators from functions, either the outermost one or a specific instance from deep within a decorator chain.
-   **Dynamic Re-decoration**: Swap an existing decorator on a function with a new one.
-   **Thread-Safe**: All patching operations are protected by a `threading.Lock` to prevent race conditions in multi-threaded applications.
-   **Async Compatible**: Works seamlessly with `async def` functions and methods.
-   **Robust**: Correctly handles instance methods, `@classmethod`, and `@staticmethod`.
-   **Flexible Error Handling**: Choose whether to raise exceptions on failure or receive a simple boolean success/failure status.

## Installation

You can install the package from the Python Package Index (PyPI) using **`pip`**.

```bash
pip install draping
```

---

## Quick Start

```python
from draping import decorate, undecorate

def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Decorator is running!")
        return func(*args, **kwargs)
    return wrapper

def greet(name):
    print(f"Hello, {name}!")

# Run the original function
greet("World")
# > Hello, World!

# Apply the decorator at runtime
decorate(my_decorator, greet)

# Run the function again - it's now decorated
greet("World")
# > Decorator is running!
# > Hello, World!

# Remove the decorator
undecorate(greet)

# The function is back to its original state
greet("World")
# > Hello, World!
```

---

## API Reference & Examples

Below are the detailed signatures and examples for each function.

### `decorate()`

Applies a decorator to one or more functions.

```python
decorate(
    decorator: Callable,
    *functions: Callable,
    decorate_again: bool = False,
    raise_on_error: bool = True
) -> tuple[bool, ...]
```

-   **`decorator`**: The decorator to apply.
-   **`*functions`**: The functions/methods you want to decorate.
-   **`decorate_again`**: If `False` (default), it will not apply the same decorator instance if it's already present. If `True`, it will stack the decorator on top of itself.
-   **Returns**: A tuple of booleans indicating success for each function.

### `undecorate()`

Removes a decorator from a function.

```python
undecorate(
    func: Callable,
    decorator_to_remove: Optional[Callable] = None,
    *,
    if_topmost: bool = False,
    raise_on_error: bool = True
) -> bool
```
-   **`func`**: The decorated function.
-   **`decorator_to_remove`**: The specific decorator instance to remove. If `None` (default), it removes the **outermost** decorator.
-   **`if_topmost`**: If `True`, `decorator_to_remove` is only removed if it is the outermost decorator.
-   **Returns**: `True` if a decorator was removed, `False` otherwise.

### `redecorate()`

Finds and replaces a decorator (`deco1`) with another (`deco2`).

```python
redecorate(
    deco1: Callable,
    deco2: Callable,
    *functions: Callable,
    change_all: bool = True,
    raise_on_error: bool = True
) -> tuple[bool, ...]
```
-   **`deco1`**: The decorator instance to find and remove.
-   **`deco2`**: The new decorator instance to apply in its place.
-   **`change_all`**: If `True` (default), replaces all instances of `deco1`. If `False`, replaces only the outermost instance.
-   **Returns**: A tuple of booleans indicating if a replacement occurred.

---

## Caveats

### The `from ... import ...` Rule: Patching the Source, Not the Local Copy

A common pitfall when monkey-patching is trying to modify a function that has been imported directly into the local namespace using `from module import function`.

To correctly patch an imported function, you must always **import the module itself and patch the function on the module object**.

#### Wrong Way

This will report success (`True`) but will not actually affect the call to `sin()`.

```python
from math import sin
from draping import decorate, my_decorator

# This modifies math.sin, but your local 'sin' is unaffected.
decorate(my_decorator, sin)

# This calls the original, undecorated sin function.
sin(3)
```

#### Correct Way

This will work as expected.

```python
import math
from draping import decorate, my_decorator

# Patch the function on its actual parent object.
decorate(my_decorator, math.sin)

# Call the function through the parent object.
math.sin(3)
```

