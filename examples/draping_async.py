#!/usr/bin/env python3
"""
An advanced example of the `draping` module with concurrent asyncio tasks
and a rich, multi-column output.
"""

import asyncio
import functools
from typing import Callable, List

# Assuming the draping module is in the same package or installed
from draping import decorate, redecorate, undecorate

# The rich library is used for beautiful, columnar output
try:
    from rich.console import Console
    from rich.columns import Columns
    from rich.panel import Panel
except ImportError:
    print("This example requires the 'rich' library. Please install it with 'pip install rich'. After all, why not rich yet?")
    exit(1)


# --- Async Decorator Factory for Demonstration ---
def async_decorator_factory(name: str) -> Callable:
    """Creates an async decorator that logs its execution to a buffer."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # The log_buffer is passed via kwargs to avoid direct printing
            log_buffer = kwargs.get("log_buffer")
            if log_buffer is not None:
                log_buffer.append(f"(Decorator '{name}' running)")
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# --- Three simple async tasks to run concurrently ---
async def task_a(*, log_buffer: List[str]):
    log_buffer.append("- Running original task_a")
    await asyncio.sleep(0.3)
    log_buffer.append("- Finished original task_a")

async def task_b(*, log_buffer: List[str]):
    log_buffer.append("- Running original task_b")
    await asyncio.sleep(0.2)
    log_buffer.append("- Finished original task_b")

async def task_c(*, log_buffer: List[str]):
    log_buffer.append("- Running original task_c")
    await asyncio.sleep(0.1)
    log_buffer.append("- Finished original task_c")


# --- Main Demonstration Block ---
async def main():
    """Runs a series of concurrent draping demonstrations."""
    console = Console()

    # Create decorator instances
    deco1 = async_decorator_factory("Deco 1")
    deco2 = async_decorator_factory("Deco 2")
    deco3 = async_decorator_factory("Deco 3")

    # Buffers to hold logs for each column
    logs_a, logs_b, logs_c = [], [], []

    async def run_and_show(title: str):
        """Helper to run tasks concurrently and display results."""
        console.print(f"\n[bold yellow]--- {title} ---[/bold yellow]")
        await asyncio.gather(
            task_a(log_buffer=logs_a),
            task_b(log_buffer=logs_b),
            task_c(log_buffer=logs_c),
        )
        columns = Columns([
            Panel("\n".join(logs_a), title="[cyan]Task A", expand=True),
            Panel("\n".join(logs_b), title="[magenta]Task B", expand=True),
            Panel("\n".join(logs_c), title="[green]Task C", expand=True),
        ])
        console.print(columns)
        logs_a.clear(); logs_b.clear(); logs_c.clear()


    # --- Step 1: Basic Decoration ---
    console.print("[bold]Action: Decorating Task A with Deco 1...[/bold]")
    decorate(deco1, task_a)
    await run_and_show("Result 1: Task A is decorated")

    # --- Step 2: Undecorate and Re-decorate ---
    console.print("[bold]Action: Undecorating Task A, Decorating Task B twice (with redecorate)...[/bold]")
    undecorate(task_a)
    decorate(deco1, task_b)
    decorate(deco1, task_b, decorate_again=True) # Apply a second time
    await run_and_show("Result 2: Task A is plain, Task B is decorated twice")

    # --- Step 3: Redecorate (Swap Decorators) ---
    console.print("[bold]Action: Undecorating Task B, Decorating Task C with Deco 1...[/bold]")
    undecorate(task_b) # Remove one layer
    undecorate(task_b) # Remove the second layer
    decorate(deco1, task_c)
    await run_and_show("Result 3: Task B is plain, Task C has Deco 1")

    console.print("[bold]Action: Replacing Deco 1 with Deco 2 on Task C...[/bold]")
    redecorate(deco1, deco2, task_c)
    await run_and_show("Result 4: Task C now has Deco 2 instead of Deco 1")
    
    # --- Step 4: Complex Undecorate ---
    console.print("[bold]Action: Applying Deco 1, 2, and 3 to Task A...[/bold]")
    decorate(deco1, task_a)
    decorate(deco2, task_a)
    decorate(deco3, task_a)
    await run_and_show("Result 5: Task A has three decorators")

    console.print("[bold]Action: Removing Deco 2 (from the middle)...[/bold]")
    undecorate(task_a, deco2)
    await run_and_show("Result 6: Task A now has only Deco 1 and 3")

    console.print("[bold]Action: Removing the topmost decorator (Deco 3)...[/bold]")
    undecorate(task_a, None) # None removes the outermost
    await run_and_show("Result 7: Task A has only Deco 1 remaining")


if __name__ == "__main__":
    asyncio.run(main())
