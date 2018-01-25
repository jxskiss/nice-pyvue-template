# -*- coding:utf-8 -*-
import signal
import threading
import time


def sql_query_may_timeout(*args, timeout=0, interval=1, **kwargs):
    """Kill long-running query doesn't finish within given time.
    When timeout happens, there will be a dangled backend daemon thread
    keep running the query, so this is only useful when you just exit
    the main thread, then the daemonized thread will be abandoned.

    Reference:
        1. https://stackoverflow.com/a/16494559
        2. https://docs.python.org/2/library/threading.html
    """
    import pandas as pd

    if timeout <= 0:
        return pd.read_sql_query(*args, **kwargs)

    result = []

    def _query(result):
        df = pd.read_sql_query(*args, **kwargs)
        result.append(df)

    worker = threading.Thread(target=_query, args=(result, ),
                              daemon=True)

    def _wait_timeout():
        deadline = time.time() + timeout
        while True:
            if not worker.is_alive():
                return
            if time.time() > deadline:
                return
            time.sleep(interval)

    timer = threading.Thread(target=_wait_timeout)
    worker.start()
    timer.start()

    # wait work being finished or timeout
    timer.join()
    if worker.is_alive():
        raise TimeoutError('worker thread timeout after %s seconds' % timeout)
    elif not result:
        raise ValueError('worker finished without result, there must be '
                         'something wrong')

    return result[0]


class timeout(object):
    """
    To be used in a ``with`` block and timeout its content.
    Can only be used in main thread.

    :raise TimeoutError: in case of operation timeout
    :raise ValueError: in case timeout can't be used in current context
    """

    def __init__(self, seconds=60, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)
