from time import sleep
from typing import Callable, Generator


def backoff(attempts: int = 10, mult_factor: float = 1.5, max_sleep: float = 60.) -> Generator:
    """
    Exponential sleep time generator.

    Args:
        attempts: number of sleep times to calculate.
        mult_factor: the multiplication factor to calculate the next sleep time.
        max_sleep: the max amount of seconds to sleep regardless of the calculated values.

    Returns:
        Generator: sleep times iterator.
    """
    sleep_time = 0.1
    for _ in range(attempts):
        sleep_time *= mult_factor
        yield min(sleep_time, max_sleep)


async def retry(func: Callable, args=(), kwargs={}, intervals=backoff(), logger=None):
    """
    Simple retry function to invoke async coroutine func in a loop of limited attempts with backoff.
    When all attempts fail the latest exception will be raised.

    Args:
        func: the function to be invoked.
        args: the arguments of the function to be invoked.
        kwargs: the keyword arguments of the function to be invoked.
        intervals: the sleep times in between function calls.
        logger: A logger to log the warning in case the function call fails.

    Returns:

    """
    exc = None
    for i, t in enumerate(intervals, 1):
        try:
            await func(*args, **kwargs)
        except Exception as e:
            exc = e
            if logger:
                logger.warning(f'Retry attempt {i}: {func}(*{args}, **{kwargs}) failed: {e}')
            sleep(t)
    raise exc
