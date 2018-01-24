import asyncio
import functools
import logging
from typing import AsyncGenerator, Generator, List, Optional, TypeVar


logger = logging.getLogger(__name__)

T = TypeVar("T")

__all__ = ["block_on", "collect", "synchronize_generator"]


class _AsyncProxy:
    def __init__(self, __proxy, __loop: asyncio.BaseEventLoop):
        self.__proxy = __proxy
        self.__loop = __loop

    def __getattr__(self, func_name):
        func = getattr(self.__proxy, func_name)

        @functools.wraps(func)
        def call(*args, **kwargs):
            task = func(*args, **kwargs)
            return self.__loop.run_until_complete(task)
        return call


def block_on(obj, loop=None):
    if loop is None:
        loop = obj.loop
    return _AsyncProxy(obj, loop)


async def collect(generator: AsyncGenerator[T, None]) -> List[T]:
    results = []
    async for x in generator:
        results.append(x)
    return results


def synchronize_generator(
        async_gen: AsyncGenerator[T, None],
        loop: Optional[asyncio.BaseEventLoop]=None) -> Generator[T, None, None]:
    """
    Maps ``__anext__`` to ``__next__`` to synchronously interact with async generators.

    If you would write the following async code:

    .. code-block: python

        async for x in my_gen:
            print(x)

    Then you can synchronize this call with the following:

    .. code-block: python

        for x in synchronize_generator(my_gen):
            print(x)

    :param async_gen: An asynchronous generator you'd like to synchronously iterate
    :param loop: The event loop to use; probably the same one that created your async generator
    :return: An object that
    """
    if loop is None:
        loop = asyncio.get_event_loop()

    while True:
        try:
            yield loop.run_until_complete(async_gen.__anext__())
        except StopAsyncIteration:
            break


def _install_uvloop():
    try:
        import asyncio
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        logger.debug("installed uvloop.EventLoopPolicy")
    except ImportError:
        pass


def enable_speedups():
    _install_uvloop()


enable_speedups()
