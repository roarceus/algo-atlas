"""Cross-platform timeout execution for solution verification."""

import signal
import sys
from typing import Any, Callable


class TimeoutError(Exception):
    """Raised when execution times out."""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Execution timed out")


def _run_with_timeout_windows(func: Callable, args: list, timeout: int) -> Any:
    """Run function with timeout on Windows using threading.

    Args:
        func: Function to run.
        args: Arguments to pass.
        timeout: Timeout in seconds.

    Returns:
        Function result.

    Raises:
        TimeoutError: If execution exceeds timeout.
        Exception: If function raises an exception.
    """
    import threading
    import queue

    result_queue = queue.Queue()
    exception_queue = queue.Queue()

    def wrapper():
        try:
            result = func(*args)
            result_queue.put(result)
        except Exception as e:
            exception_queue.put(e)

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        raise TimeoutError("Execution timed out")

    if not exception_queue.empty():
        raise exception_queue.get()

    if not result_queue.empty():
        return result_queue.get()

    return None


def _run_with_timeout_unix(func: Callable, args: list, timeout: int) -> Any:
    """Run function with timeout on Unix using signals.

    Args:
        func: Function to run.
        args: Arguments to pass.
        timeout: Timeout in seconds.

    Returns:
        Function result.
    """
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout)

    try:
        result = func(*args)
        return result
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def _run_with_timeout(func: Callable, args: list, timeout: int) -> Any:
    """Run function with timeout (cross-platform).

    Args:
        func: Function to run.
        args: Arguments to pass.
        timeout: Timeout in seconds.

    Returns:
        Function result.
    """
    if sys.platform == "win32":
        return _run_with_timeout_windows(func, args, timeout)
    else:
        return _run_with_timeout_unix(func, args, timeout)
