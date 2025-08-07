#!/usr/bin/env python3
"""Examples of how the draping module works"""

from time import sleep
import functools
from typing import Callable

# Assuming the draping module is in the same package or installed
from draping import decorate, redecorate, undecorate


# --- Utility for colored output ---
class Colors:
    """ANSI escape codes for colored terminal text."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Prints a bold, yellow header."""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}--- {text} ---{Colors.ENDC}")

def print_action(text: str):
    """Prints a blue action line."""
    print(f"{Colors.BLUE}>>> {text}{Colors.ENDC}")

def print_result(text: str):
    """Prints a green result line."""
    print(f"{Colors.GREEN}    {text}{Colors.ENDC}")


# --- A simple, clear decorator for demonstration purposes ---
def simple_decorator_factory(name: str) -> Callable:
    """
    This factory creates a decorator that prints its name when called.
    It correctly uses @functools.wraps, which is essential for `draping` to work.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"    (Decorator '{name}' running)")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# --- A few simple functions to act as our subjects ---
def func_1():
    print("    - Running original func_1")
    sleep(1)

def func_2():
    print("    - Running original func_2")
    sleep(1)

def func_3():
    print("    - Running original func_3")
    sleep(1)

def func_4():
    print("    - Running original func_4")
    sleep(1)


# --- Main Demonstration Block ---
if __name__ == "__main__":
    # 1. Create decorator instances
    deco1 = simple_decorator_factory("Deco 1")
    deco2 = simple_decorator_factory("Deco 2")
    deco3 = simple_decorator_factory("Deco 3")

    # 2. Basic decoration
    print_header("Step 1: Basic Decoration")
    print_action("decorate(deco1, func_1)")
    changed = decorate(deco1, func_1)
    print_result(f"Changed: {changed[0]}")
    print_action("Calling func_1():")
    func_1()

    # 3. Attempting to re-decorate with decorate_again=False (default)
    print_header("Step 2: Attempting to re-decorate (decorate_again=False)")
    print_action("Decorating func_2 with deco1 for the first time...")
    decorate(deco1, func_2)
    print_action("Calling func_2():")
    func_2()
    print_action("\nAttempting to decorate func_2 with deco1 AGAIN...")
    changed = decorate(deco1, func_2) # decorate_again is False by default
    print_result(f"Changed: {changed[0]} (as expected, no change)")
    print_action("Calling func_2():")
    func_2()

    # 4. Forcing re-decoration with decorate_again=True
    print_header("Step 3: Forcing re-decoration (decorate_again=True)")
    print_action("Decorating func_2 with deco1 again, but with decorate_again=True...")
    changed = decorate(deco1, func_2, decorate_again=True)
    print_result(f"Changed: {changed[0]}")
    print_action("Calling func_2():")
    func_2()

    # 5. Using redecorate()
    print_header("Step 4: Using redecorate()")
    print_action("Decorating func_3 with deco1...")
    decorate(deco1, func_3)
    print_action("Calling func_3():")
    func_3()
    
    print_action("\nAttempting to replace deco2 with deco1 (should fail, deco2 not present)...")
    changed = redecorate(deco2, deco1, func_3)
    print_result(f"Changed: {changed[0]} (no change, deco2 was not found)")
    print_action("Calling func_3():")
    func_3()

    print_action("\nNow, replacing deco1 with deco2...")
    changed = redecorate(deco1, deco2, func_3)
    print_result(f"Changed: {changed[0]}")
    print_action("Calling func_3():")
    func_3()

    # 6. Using undecorate() with multiple layers
    print_header("Step 5: Complex undecorate() scenarios")
    print_action("Decorating func_4 with deco1, then deco2, then deco3...")
    decorate(deco1, func_4)
    decorate(deco2, func_4)
    decorate(deco3, func_4)
    print_action("Calling func_4() with 3 decorators:")
    func_4()

    print_action("\nAttempting to remove deco1 with if_topmost=True (should fail)...")
    changed = undecorate(func_4, deco1, if_topmost=True)
    print_result(f"Changed: {changed} (no change, deco1 was not topmost)")
    print_action("Calling func_4():")
    func_4()

    print_action("\nRemoving deco2 from the middle of the chain...")
    changed = undecorate(func_4, deco2)
    print_result(f"Changed: {changed}")
    print_action("Calling func_4():")
    func_4()
    
    print_action("\nRemoving the new topmost decorator (deco3) by passing None...")
    changed = undecorate(func_4, None)
    print_result(f"Changed: {changed}")
    print_action("Calling func_4():")
    func_4()
