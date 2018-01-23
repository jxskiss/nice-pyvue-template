# -*- coding: utf-8 -*-
import datetime
import numbers
import random
import re
import time
from tornado.ioloop import PeriodicCallback

from utils import timezone


def _to_timestamp(dt):
    if timezone.is_aware(dt):
        t = time.mktime(dt.utctimetuple()) - time.timezone
    else:
        t = time.mktime(dt.timetuple())
    return t + dt.microsecond / 1e6


class ScheduledCallback(PeriodicCallback):
    """Scheduled tasks to be called periodically with a start time.

    :param callback: the scheduled function will be called periodically
    :param start_at: start time of this scheduled task, can be either
            datetime.datetime object or timestamp, or datetime string
            which will be parsed using dateutil.parser.parse,
            for datetime object or datetime string timezone is ok.
    :param every: a callable to calculate next timeout time according the
            previous timeout time, or a numeric timeout in seconds,
            or a timedelta object, or one of the shortcuts:
            'minute', 'hour', 'day', 'week', 'month'.
    :param random_sleep: if not None, sleep a random time no more than
            random_sleep in seconds before each time the task runs, including
            first time the task starts up.
    """
    EVERY_INCERS = {
        'second': lambda pre: pre + datetime.timedelta(seconds=1),
        'minute': lambda pre: pre + datetime.timedelta(minutes=1),
        'hour': lambda pre: pre + datetime.timedelta(hours=1),
        'day': lambda pre: pre + datetime.timedelta(days=1),
        'week': lambda pre: pre + datetime.timedelta(weeks=1),
        'month': None,  # method "_get_next_month"
    }
    PLURAL_PATTERN = re.compile(r'^(\d+)?(\w+?)s?$')

    def __init__(self, callback, start_at, every, random_sleep=None):
        if isinstance(start_at, datetime.datetime):
            self._start_at_timestamp = _to_timestamp(start_at)
        elif isinstance(start_at, numbers.Real):
            self._start_at_timestamp = start_at
        elif isinstance(start_at, str):
            start_at = timezone.parse(start_at)
            self._start_at_timestamp = _to_timestamp(start_at)
        else:
            raise TypeError("Unsupported start_at type: %r" % start_at)

        self._every_n, self._every = 1, None
        if callable(every):
            self._every = every
        elif isinstance(every, numbers.Real):
            self._every = lambda pre: pre + datetime.timedelta(seconds=every)
        elif isinstance(every, datetime.timedelta):
            self._every = lambda pre: pre + every
        elif isinstance(every, str):
            m = self.PLURAL_PATTERN.match(every)
            if m:
                self._every_n = int(m.group(1) or 1)
                self._every = self.EVERY_INCERS.get(m.group(2))
        if self._every is None:
            raise ValueError('Invalid value for parameter every: %r' % every)

        self._random_sleep = random_sleep
        self._next_sleep = 0

        # dummy value for parameter 'callback_time' which is not used
        # in this class, _next_timeout is calculated by the callable _every
        callback_time = datetime.timedelta.max.total_seconds() * 1000
        super(ScheduledCallback, self).__init__(callback, callback_time)

    def _get_next_month(self, pre):
        base = datetime.datetime.fromtimestamp(self._start_at_timestamp)
        y, m = divmod(pre.month + 1, 12)
        try:
            next_ = pre.replace(year=pre.year+y, month=m+1, day=base.day)
        except ValueError:
            try:
                for day in range(28, 31):
                    next_ = pre.replace(year=pre.year+y, month=m+1, day=day)
            except ValueError:
                pass
        return next_

    def _schedule_next(self):
        if not self._running:
            return
        current_time = self.io_loop.time()
        self._next_timeout -= self._next_sleep

        if self._next_timeout < self._start_at_timestamp:
            self._next_timeout = self._start_at_timestamp
        elif self._next_timeout <= current_time:
            _next_timeout = datetime.datetime.fromtimestamp(self._next_timeout)
            for _ in range(self._every_n):
                _next_timeout = self._every(_next_timeout)
            self._next_timeout = _to_timestamp(_next_timeout)

        if self._random_sleep:
            self._next_sleep = random.randint(0, self._random_sleep)
            self._next_timeout += self._next_sleep
        self._timeout = self.io_loop.add_timeout(self._next_timeout, self._run)


class scheduler(object):
    """Scheduler object to register and control tasks with decorator style.

    Usage:
        register a task: `@scheduler(start_at, every, random_sleep)`
        start all scheduled tasks: `scheduler.start_all()`
    """
    _tasks = []

    def __init__(self, start_at, every, random_sleep=None):
        """See `ScheduledCallback` for param docs."""
        self._args = (start_at, every, random_sleep)

    def __call__(self, task):
        self._tasks.append(ScheduledCallback(task, *self._args))
        return task

    @classmethod
    def start_all(cls):
        """Start all scheduled tasks."""
        for task in cls._tasks:
            task.start()
