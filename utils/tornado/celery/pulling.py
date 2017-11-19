# -*- coding: utf-8 -*-
from tornado.concurrent import Future
from tornado.gen import TimeoutError
from tornado.ioloop import IOLoop
import logging

_logger = logging.getLogger(__name__)

MAX_POLLING_INTERVAL = 0.032  # 32 milliseconds


def _on_polling_result(result, fut, deadline, interval=0.001):
    if result.ready():
        fut.set_result(result.result)
        return

    io_loop = IOLoop.current()
    if deadline and deadline < io_loop.time():
        fut.set_exception(TimeoutError())
    else:
        interval = min(interval * 2, MAX_POLLING_INTERVAL)
        io_loop.call_later(interval, _on_polling_result,
                           result, fut, deadline, interval)


def delay_polling(task, *args, callback=None, timeout=30, **kwargs):
    fut = Future()
    io_loop = IOLoop.current()
    if callback:
        io_loop.add_future(fut, lambda f: callback(f.result()))
    result = task.delay(*args, **kwargs)
    if timeout <= 0:
        deadline = None
    else:
        deadline = io_loop.time() + timeout
    io_loop.add_callback(_on_polling_result, result, fut, deadline)
    return fut
