# -*- coding: utf-8 -*-
import datetime
import numbers
import random
import re
import time
import dateutil.parser
from tornado.ioloop import PeriodicCallback


def _to_timestamp(dt):
    # convert timezone aware value to local timestamp
    if dt.utcoffset() is not None:
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
            start_at = dateutil.parser.parse(start_at)
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


class CronCallback(PeriodicCallback):
    """Schedules the given callback in crontab style schedule.

    If the schedule fall behind of clcock or callback runs for longer
    than the schedule interval, subsequent invocations will be skipped
    to get back on schedule.

    `start` must be called after the `PeriodicCallback` is created.
    """

    def __init__(self, callback, cron, random_sleep=None):
        self._cron = CronParser(cron)
        self._random_sleep = random_sleep
        self._next_sleep = 0

        callback_time = datetime.timedelta.max.total_seconds() * 1000
        super(CronCallback, self).__init__(callback, callback_time)

    def _schedule_next(self):
        if not self._running:
            return
        current_time = self.io_loop.time()
        self._next_timeout -= self._next_sleep

        if self._next_timeout <= current_time:
            self._next_timeout = _to_timestamp(
                self._cron.get_next_from(
                    datetime.datetime.fromtimestamp(current_time)))
        if self._random_sleep:
            self._next_sleep = random.randint(0, self._random_sleep)
            self._next_timeout += self._next_sleep
        self._timeout = self.io_loop.add_timeout(self._next_timeout, self._run)


class CronParser(object):

    SCH_MAP = {
        'yearly': '0 0 1 1 *',
        'annually': '0 0 1 1 *',
        'monthly': '0 0 1 * *',
        'weekly': '0 0 * * 0',
        'daily': '0 0 * * *',
        'midnight': '0 0 * * *',
        'hourly': '0 * * * *',
    }

    def __init__(self, cronline, base=None):
        self.cronline = cronline
        self.sched = base or datetime.datetime.now()
        self.task = None

    def _parse(self):
        line = self.cronline.lower()
        task = {}
        line = re.sub(r'^@(yearly|annually|monthly|weekly|daily|midnight|hourly)',
                      lambda m: self.SCH_MAP[m.group(1)], line)
        params = line.strip().split()
        if len(params) < 5:
            raise ValueError('Invalid cron line (too short)')
        elif len(params) > 5:
            raise ValueError('Invalid cron line (too long')
        days_of_week = {'sun': 0, 'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4,
                        'fri': 5, 'sat': 6}
        months_of_year = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5,
                          'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10,
                          'nov': 11, 'dec': 12, 'l': 'l'}
        for (s, i) in zip(params[:5], ['min', 'hr', 'dom', 'mon', 'dow']):
            if s not in [None, '*']:
                task[i] = []
                values = s.split(',')
                for val in values:
                    if i == 'dow':
                        ref_dict = days_of_week
                    elif i == 'mon':
                        ref_dict = months_of_year
                    if i in ('dow', 'mon') and '-' in val and '/' not in val:
                        is_num = val.split('-')[0].isdigit()
                        if is_num:
                            val = '%s/1' % val
                        else:
                            val = '-'.join(str(ref_dict[v]) for v in val.split('-'))
                    if val != '-1' and '-' in val and '/' not in val:
                        val = '%s/1' % val
                    if '/' in val:
                        task[i] += self._range_to_list(val, i)
                    elif val.isdigit() or val == '-1':
                        task[i].append(int(val))
                    elif i in ('dow', 'mon'):
                        if val in ref_dict:
                            task[i].append(ref_dict[val])
                    elif i == 'dom' and val == 'l':
                        task[i].append(val)
                if not task[i]:
                    raise ValueError('Invalid cron value (%s: %s)' % (i, s))
                if not self._sanity_check(task[i], i):
                    raise ValueError('Invalid cron value (%s: %s)' % (i, s))
                task[i] = sorted(task[i])
        self.task = task

    @staticmethod
    def _range_to_list(s, period='min'):
        ret = []
        star_range = {'min': '0-59', 'hr': '0-23', 'dom': '1-31',
                      'mon': '0-12', 'dow': '1-7'}
        if s.startswith('*'):
            s.replace('*', star_range[period], 1)
        pattern = re.compile(r'(\d+)(?:-(\d+))?/(\d+)')
        match = pattern.match(s)
        if match:
            min_ = int(match.group(1))
            max_ = int(match.group(2) or star_range[period].split('-')[-1]) + 1
            step_ = int(match.group(3))
            ret.extend(range(min_, max_, step_))
        return ret

    @staticmethod
    def _sanity_check(values, period):
        ok = False
        if period == 'min':
            ok = all(0 <= i <= 59 for i in values)
        elif period == 'hr':
            ok = all(0 <= i <= 23 for i in values)
        elif period == 'dom':
            dom_range = set(range(1, 32))
            dom_range.add('l')
            ok = all(i in dom_range for i in values)
        elif period == 'mon':
            ok = all(1 <= i <= 12 for i in values)
        elif period == 'dow':
            ok = all(0 <= i <= 7 for i in values)
        return ok

    @staticmethod
    def _get_next_dow(sched, task):
        task_dow = set(a % 7 for a in task['dow'])
        while sched.isoweekday() % 7 not in task_dow:
            sched += datetime.timedelta(days=1)
        return sched

    @staticmethod
    def _get_next_dom(sched, task):
        if task['dom'] == ['l']:
            last_feb = 29 if sched.year % 4 == 0 else 28
            last_day_of_month = [
                31, last_feb, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
            ]
            task_dom = {last_day_of_month[sched.month] - 1}
        else:
            task_dom = set(task['dom'])
        while sched.day not in task_dom:
            sched += datetime.timedelta(days=1)
        return sched

    @staticmethod
    def _get_next_mon(sched, task):
        task_mon = set(task['mon'])
        while sched.month not in task_mon:
            if sched.month < 12:
                sched = sched.replace(month=sched.month + 1)
            else:
                sched = sched.replace(month=1, year=sched.year + 1)
        return sched

    @staticmethod
    def _get_next_hhmm(sched, task, add_to=True):
        if add_to:
            sched += datetime.timedelta(minutes=1)
        if 'min' in task:
            task_min = set(task['min'])
            while sched.minute not in task_min:
                sched += datetime.timedelta(minutes=1)
        if 'hr' in task and sched.hour not in task['hr']:
            task_hour = set(task['hr'])
            while sched.hour not in task_hour:
                sched += datetime.timedelta(hours=1)
        return sched

    @classmethod
    def _get_next_date(cls, sched, task):
        if 'dow' in task and 'dom' in task:
            dow = cls._get_next_dow(sched, task)
            dom = cls._get_next_dom(sched, task)
            sched = min(dow, dom)
        elif 'dow' in task:
            sched = cls._get_next_dow(sched, task)
        elif 'dom' in task:
            sched = cls._get_next_dom(sched, task)
        if 'mon' in task:
            sched = cls._get_next_mon(sched, task)
        return sched.replace(hour=0, minute=0)

    def get_next_from(self, base):
        if not self.task:
            self._parse()

        task = self.task
        sched = base
        x = 0
        while x < 1000:  # avoid potential max recursions
            x += 1
            try:
                next_date = self._get_next_date(sched, task)
            except (ValueError, OverflowError) as exc:
                raise ValueError('Invalid cron expression (%s)' % exc)
            if next_date.date() > base.date():
                # we rolled date, check for valid hhmm
                sched = self._get_next_hhmm(next_date, task, False)
                break
            else:
                # same date, get next hhmm
                sched_time = self._get_next_hhmm(sched, task, True)
                if sched_time.date() > sched.date():
                    # rolled date again :(
                    sched = sched_time
                else:
                    sched = sched_time
                    break
        else:
            raise RuntimeError('Potential bug found, max recursion depth hit')
        if sched <= base:
            raise RuntimeError('Potential bug found, invalid next scheduled time')
        return sched

    def get_next(self):
        """Get next deadline according to cronline specs."""
        self.sched = self.get_next_from(self.sched)
        return self.sched

    def __iter__(self):
        """Support iteration."""
        return self

    __next__ = next = get_next


class scheduler(object):
    """Scheduler object to register and control tasks with decorator style.

    Usage:
        register a scheduled task:
            @scheduler(start_at=time.time() + 1, every='minute', random_sleep=5)
            def task():
                pass

            @scheduler(start_at='2018-01-30 02:00:00+08:00', every='2days')
            def task():
                pass

        register a crontab-style task:
            @scheduler(cron='* * * * *', random_sleep=5)
            def task():
                pass

        start all scheduled tasks: `scheduler.start_all()`
    """
    tasks = []

    def __init__(self, start_at=None, every=None,  # ScheduledCallback
                 cron=None,  # CronCallback
                 callback_seconds=None,  # PeriodicCallback
                 random_sleep=None,  # shared params
                 ):
        """
        See `ScheduledCallback` for doc of params start_at and every.
        See `CronCallback` for doc of param cron.
        See `PeriodicCallback` for doc of param callback_seconds:
            callback_time = callback_seconds * 1000
        """
        if start_at and every:
            self.sch_class = ScheduledCallback
            self.sch_kwargs = {'start_at': start_at, 'every': every,
                               'random_sleep': random_sleep}
        elif cron:
            self.sch_class = CronCallback
            self.sch_kwargs = {'cron': cron, 'random_sleep': random_sleep}
        elif callback_seconds:
            self.sch_class = PeriodicCallback
            self.sch_kwargs = {'callback_time': callback_seconds * 1000}
        else:
            raise ValueError('Either (start_at, every) or cron or '
                             'callback_seconds must be given')

    def __call__(self, task):
        self.tasks.append(self.sch_class(task, **self.sch_kwargs))
        return task

    @classmethod
    def start_all(cls):
        """Start all scheduled tasks."""
        for task in cls.tasks:
            task.start()
