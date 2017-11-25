# -*- coding:utf-8 -*-
"""
Some useful and frequently used decorators, references:
    1. https://wiki.python.org/moin/PythonDecoratorLibrary
    2. https://github.com/pydanny/cached-property/blob/master/cached_property.py
    3. https://github.com/bottlepy/bottle/blob/master/bottle.py
"""  # noqa
import functools
import inspect
import itertools
import logging
import math
import sys
import threading
import time
import traceback
import warnings

try:
    import Queue as queue
except ImportError:
    import queue


class lazy_attribute(object):
    """A property that caches itself to the class object."""

    def __init__(self, func):
        functools.update_wrapper(self, func, updated=[])
        self.getter = func

    def __get__(self, obj, cls):
        value = self.getter(cls)
        setattr(cls, self.__name__, value)
        return value


class cached_property(object):
    """
    Decorator for read-only properties evaluated only once within TTL period,
    it is thread safe.

    It can be used to create a cached property like this:

        import random

        # the class containing the property must be a new-style class
        class MyClass(object):

            # create property whose value is cached for ten minutes
            @cached_property(ttl=600)
            def randint(self):
                # will only be evaluated every 10 min. at maximum.
                return random.randint(0, 100)

            # use all default arguments, never expired
            @cached_property
            def random(self):
                return random.random()

    The value is cached in the '_cache' attribute of the object instance
    that has the property getter method wrapped by this decorator. The
    '_cache' attribute value is a dictionary which has a key for every
    property of the object which is wrapped by this decorator. Each entry
    in the cache is created only when the property is accessed for the
    first time and is a two-element tuple with the last computed property
    value and the last time it was updated in seconds since the epoch.

    The default time-to-live (TTL) is 0 which is never expire. Set to
    positive number to enable TTL.

    To expire a cached property value manually just do:

        del instance._cache[<property name>]

    """  # noqa
    def __init__(self, func=None, ttl=0, name=None, doc=None):
        self.ttl = ttl
        self.lock = threading.RLock()
        self.__name__, self.__doc__ = name, doc

        if func is not None:
            self.__call__(func)

    def __call__(self, func):
        self.func = func
        if not self.__doc__:
            self.__doc__ = func.__doc__
        if not self.__name__:
            self.__name__ = func.__name__
        self.__module__ = func.__module__
        return self

    def __get__(self, inst, owner):
        if inst is None:
            return self

        now = time.time()
        with self.lock:
            try:
                value, last_updated = inst._cache[self.__name__]
                if 0 < self.ttl < now - last_updated:
                    raise AttributeError
            except (KeyError, AttributeError):
                value = self.func(inst)
                try:
                    cache = inst._cache
                except AttributeError:
                    cache = inst._cache = {}
                cache[self.__name__] = (value, now)
            return value


class dict_property(object):
    """Property that maps to a key in a local dict-like attribute."""

    def __init__(self, attr, key=None, read_only=False):
        self.attr, self.key, self.read_only = attr, key, read_only

    def __call__(self, func):
        functools.update_wrapper(self, func, updated=[])
        self.getter, self.key = func, self.key or func.__name__
        return self

    def __get__(self, obj, cls):
        if obj is None:
            return self
        key, storage = self.key, getattr(obj, self.attr)
        if key not in storage:
            storage[key] = self.getter(obj)
        return storage[key]

    def __set__(self, obj, value):
        if self.read_only:
            raise AttributeError("Read-Only property.")
        getattr(obj, self.attr)[self.key] = value

    def __delete__(self, obj):
        if self.read_only:
            raise AttributeError("Read-Only property.")
        del getattr(obj, self.attr)[self.key]


def retry_on_exc(tries, delay=3, backoff=2,
                 exceptions=(Exception,), hook=None):
    """Function decorator implementing retrying logic.

    Copyright 2012 by Jeff Laughlin Consulting LLC.

    https://gist.github.com/n1ywb/2570004

    delay: Sleep this many seconds * backoff * try number after failure
    backoff: Multiply delay by this factor after each failure
    exceptions: A tuple of exception classes; default (Exception,)
    hook: A function with the signature
          myhook(tries_remaining, exception, delay), default None

    The decorator will call the function up to max_tries times if it raises
    an exception.

    By default it catches instances of the Exception class and subclasses.
    This will recover after all but the most fatal errors. You may specify a
    custom tuple of exception classes with the 'exceptions' argument; the
    function will only be retried if it raises one of the specified
    exceptions.

    Additionally you may specify a hook function which will be called prior
    to retrying with the number of remaining tries and the exception instance;
    see given example. This is primarily intended to give the opportunity to
    log the failure. Hook is not called after failure if no retries remain.
    """

    if backoff <= 1:
        raise ValueError("backoff must be greater than 1")

    tries = math.floor(tries)
    if tries < 0:
        raise ValueError("tries must be 0 or greater")

    if delay <= 0:
        raise ValueError("delay must be greater than 0")

    def deco_retry(f):
        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            my_delay = delay
            the_tries = list(range(tries))
            the_tries.reverse()
            for tries_remaining in the_tries:
                try:
                    return f(*args, **kwargs)
                except exceptions as err:
                    if tries_remaining > 0:
                        if hook is not None:
                            hook(tries_remaining, err, my_delay)
                        time.sleep(my_delay)
                        my_delay = my_delay * backoff
                    else:
                        raise

        return f_retry

    return deco_retry


def retry_on_false(tries, delay=3, backoff=2):
    """
    Retry function or method with exponential backoff until it returns True.

    delay sets the initial delay in seconds, and backoff sets the factor by
    which the delay should lengthen after each failure. backoff must be
    greater than 1, or else it isn't really a backoff. tries must be at least
    0, and delay greater than 0.
    """

    if backoff <= 1:
        raise ValueError("backoff must be greater than 1")

    tries = math.floor(tries)
    if tries < 0:
        raise ValueError("tries must be 0 or greater")

    if delay <= 0:
        raise ValueError("delay must be greater than 0")

    def deco_retry(f):
        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            m_tries, m_delay = tries, delay  # make mutable

            rv = f(*args, **kwargs)  # first attempt
            while m_tries > 0:
                if rv is True:  # Done on success
                    return True

                m_tries -= 1  # consume an attempt
                time.sleep(m_delay)  # wait...
                m_delay *= backoff  # make future wait longer

                rv = f(*args, **kwargs)  # Try again

            return False  # Ran out of tries :-(

        return f_retry  # true decorator -> decorated function

    return deco_retry  # @retry(arg[, ...]) -> true decorator


def deprecated(func=None, msg=None):
    """
    This is a decorator which can be used to mark functions as deprecated.
    It will result in a warning being emitted when the function is used.

    Usage examples:

        @other_decorators_must_be_upper
        @deprecated
        def some_old_function(x, y):
            return x + y

        class SomeClass:
            @deprecated
            def some_old_method(self, x, y):
                return x + y
    """
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = msg or "Function {} is deprecated.".format(func.__name__)
            warnings.warn(message, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        return wrapper

    if func is not None:
        return deco(func)

    return deco


def unimplemented(func=None, defaultval=None):
    """
    Allows you to test unimplemented code in a development environment by
    specifying a default argument as an argument to the decorator (or you
    can leave it off to specify None to be returned).
    """
    if func is None:
        def unimp_wrapper(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                return defaultval

            return wrapper

        return unimp_wrapper

    else:
        return lambda *args, **kwargs: defaultval


def enabled(func):
    """
    This decorator doesn't add any behavior， Keep function unchanged.

    Commonly used together with the disabled decorator, example Usage:

        GLOBAL_ENABLE_FLAG = True
        state = enabled if GLOBAL_ENABLE_FLAG else disabled

        @state
        def special_function_foo():
            print("function was enabled")
    """
    return func


def disabled(func):
    """
    This decorator disables the provided function, and does nothing.

    See the decorator enabled for usage example.
    """
    def empty_func(*args, **kargs):
        pass

    return empty_func


class _LogDecorator(object):

    logger_name = '_logDecorator'

    def __new__(cls, func=None,
                logger=None, level=None, logger_name=None, propagate=True):
        self = object.__new__(cls)

        logging.basicConfig(level=logging.DEBUG)
        self.level = level or (logger and logger.level) or logging.root.level
        if logger is None:
            self.logger_name = logger_name or cls.logger_name
            self.logger = logging.getLogger(self.logger_name)
        else:
            self.logger = logger
            self.logger_name = logger.name
        self.logger.propagate = propagate

        # make sure the logger's level is not greater than target level
        if self.logger.level > self.level:
            warnings.warn(
                "The logger's level is greater than level, resetting to "
                "level: {}".format(logging.getLevelName(self.logger.level)),
                category=UserWarning,
                stacklevel=2
            )
            self.level = self.logger.level

        if func is not None:
            return self.__call__(func)
        return self

    def __call__(self, func):
        raise NotImplementedError()


class log_args(_LogDecorator):
    """
    Dumps out the arguments passed to a function before calling it.
    """
    def __call__(self, func):
        arg_names = inspect.getargspec(func).args
        f_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.logger.log(self.level, '%s : %s', f_name, ', '.join(
                '%s=%s' % entry
                for entry in itertools.chain(
                    zip(arg_names, args), kwargs.items())))
            return func(*args, **kwargs)

        return wrapper


class log_events(_LogDecorator):
    """
    Logging decorator that allows you to log function entering and
    leaving events with a specific logger.
    """

    ENTRY_MESSAGE = 'Entering %s'
    EXIT_MESSAGE = 'Exiting %s'

    def __call__(self, func):
        f_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.logger.log(self.level, self.ENTRY_MESSAGE, f_name)
            f_result = func(*args, **kwargs)
            self.logger.log(self.level, self.EXIT_MESSAGE, f_name)
            return f_result

        return wrapper


class print_to_log(_LogDecorator):
    """
    Redirects stdout printing to python standard logging.
    """
    logger_name = 'STDOUT'

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            stdout_bak = sys.stdout
            sys.stdout = self
            try:
                return func(*args, **kwargs)
            finally:
                sys.stdout = stdout_bak

        return wrapper

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


def singleton(cls):
    """
    Use class as singleton. Usage example:

        @singleton
        class Foo:
            def __new__(cls):
                cls.x = 10
                return object.__new__(cls)

            def __init__(self):
                assert self.x == 10
                self.x = 15

        assert Foo().x == 15
        Foo().x = 20
        assert Foo().x == 20
    """

    cls.__new_original__ = cls.__new__

    @functools.wraps(cls.__new__)
    def singleton_new(cls, *args, **kwargs):
        it = cls.__dict__.get('__it__')
        if it is not None:
            return it

        cls.__it__ = it = cls.__new_original__(cls, *args, **kwargs)
        it.__init_original__(*args, **kwargs)
        return it

    cls.__new__ = singleton_new
    cls.__init_original__ = cls.__init__
    cls.__init__ = object.__init__

    return cls


class asynchronous(object):
    """
    Make function calling asynchronously. Usage example:

        import time

        @asynchronous
        def long_process(num):
            time.sleep(10)
            return num * num

        result = long_process.start(12)

        for i in range(20):
            print(i)
            time.sleep(1)

            if result.is_done():
                print("result {0}".format(result.get_result()))

        result2 = long_process.start(13)

        try:
            print("result2 {0}".format(result2.get_result()))
        except asynchronous.NotYetDoneException as ex:
            print ex.message

    """
    def __init__(self, func):
        self.func = func

        def threaded(*args, **kwargs):
            self.queue.put(self.func(*args, **kwargs))

        self.threaded = threaded

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def start(self, *args, **kwargs):
        self.queue = queue.Queue()
        thread = threading.Thread(
            target=self.threaded, args=args, kwargs=kwargs)
        thread.start()
        return asynchronous.Result(self.queue, thread)

    class NotYetDoneException(Exception):
        def __init__(self, message):
            self.message = message

    class Result(object):
        def __init__(self, queue, thread):
            self.queue = queue
            self.thread = thread
            self.result = None

        def is_done(self):
            return not self.thread.is_alive()

        def get_result(self):
            if not self.is_done():
                raise asynchronous.NotYetDoneException(
                    'the call has not yet completed its task')

            if not hasattr(self, 'result'):
                self.result = self.queue.get()

            return self.result


def lazy_thunkify(func):
    """Make a function immediately return a function of no args which, when
    called, waits for the result, which will start being processed in another
    thread.

    This decorator will cause any function to, instead of running its code,
    start a thread to run the code, returning a thunk (function with no args)
    that wait for the function's completion and returns the value (or raises
    the exception).

    Useful if you have Computation A that takes x seconds and then uses
    Computation B, which takes y seconds. Instead of x+y seconds you only
    need max(x,y) seconds.

    Example:

        @lazy_thunkify
        def slow_double(i):
            print "Multiplying..."
            time.sleep(5)
            print "Done multiplying!"
            return i*2


        def maybe_multiply(x):
            double_thunk = slow_double(x)
            print "Thinking..."
            time.sleep(3)
            time.sleep(3)
            time.sleep(1)
            if x == 3:
                print "Using it!"
                res = double_thunk()
            else:
                print "Not using it."
                res = None
            return res

        # both take 7 seconds
        maybe_multiply(10)
        maybe_multiply(3)
    """

    @functools.wraps(func)
    def lazy_thunked(*args, **kwargs):
        wait_event = threading.Event()

        result = [None]
        exc = [False, None]

        def worker_func():
            try:
                func_result = func(*args, **kwargs)
                result[0] = func_result
            except Exception as err:
                exc[0] = True
                exc[1] = sys.exc_info()
                print("Lazy thunk has thrown an exception (will be raised "
                      "on thunk()):\n%s" % (traceback.format_exc()))
            finally:
                wait_event.set()

        def thunk():
            wait_event.wait()
            if exc[0]:
                # raise exc[1][0], exc[1][1], exc[1][2]
                # raise exc[1][1] from None
                raise exc[1][1]

            return result[0]

        threading.Thread(target=worker_func).start()

        return thunk

    return lazy_thunked
