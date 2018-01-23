# -*- coding:utf-8 -*-
import pandas as pd
import threading
import time


def sql_query_with_timeout(*args, timeout=0, interval=1, **kwargs):
    """Kill long-running query doesn't finish within given time.
    When timeout happens, there will be a dangled backend daemon thread
    keep running the query, so this is only useful when you just exit
    the main thread, then the daemonized thread will be abandoned.

    Reference:
        1. https://stackoverflow.com/a/16494559
        2. https://docs.python.org/2/library/threading.html
    """
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
