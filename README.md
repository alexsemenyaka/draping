[![PyPI version](https://img.shields.io/pypi/v/draping.svg)](https://pypi.org/project/draping/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/draping.svg)](https://pypi.org/project/draping/)
[![PyPI - License](https://img.shields.io/pypi/l/draping.svg)](https://pypi.org/project/draping/)
[![Coverage Status](https://coveralls.io/repos/github/alexsemenyaka/draping/badge.svg?branch=main)](https://coveralls.io/github/alexsemenyaka/draping?branch=main)
[![CI/CD Status](https://github.com/alexsemenyaka/draping/actions/workflows/ci.yml/badge.svg)](https://github.com/alexsemenyaka/draping/actions/workflows/ci.yml)

# WHAT IT IS

This module allows developers to apply and remove decorators to the fumctions (both sync and async) on-fly.

# INTRO

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

