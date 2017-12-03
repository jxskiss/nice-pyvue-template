# -*- coding:utf-8 -*-
"""
Some useful and frequently used decorators, references:
    1. https://wiki.python.org/moin/PythonDecoratorLibrary
    2. https://github.com/pydanny/cached-property/
    3. https://github.com/bottlepy/bottle/
"""
import functools
import hashlib
import inspect
import itertools
import json
import logging
import math
import os
import re
import sys
import threading
import time
import warnings

from six import PY2, PY3, b, u, reraise
from six.moves import queue

if PY2:
    from io import open


class cached_attribute(object):
    """
    Thread safe decorator for read-only class attribute evaluated only
    once within TTL period.

    The default time-to-live (TTL) is 0 which is never expire, which
    will result the class attribute be replaced by the value when first
    accessed. Set to positive number to enable TTL.

    Usage example:

        import random

        # the class containing the attribute must be a new-style class
        class MyClass(object):

            # create class attribute whose value will only be evaluated
            # every 60 seconds, at maximum.
            @cached_attribute(ttl=60)
            def randint(cls):
                return random.randint(0, 100)

            # create class attribute whose value will only be evaluated
            # once, using all default parameters
            @cached_attribute
            def rand_float(cls):
                return random.random()

    By default the value is cached in the '_attr_cache_' attribute of the
    class that has the attribute getter method wrapped by this decorator.
    The cache attribute value is a dictionary which has a key for every
    attribute of the class which is wrapped by this decorator. Each entry
    in the cache is created only when the property is accessed for the
    first time and is a two-element tuple with the last computed attribute
    value and the last time it was updated in seconds since the epoch.

    The cache dictionary attribute can be specified using the 'cache_attr'
    parameter of the decorator constructor.

    To expire a cached attribute value with positive TTL manually just do:

        del instance.<attribute name>
        # or: del class._attr_cache_[<attribute name>]

    """

    def __init__(self, func=None, ttl=0, cache_attr='_attr_cache_'):
        self.cache_attr = cache_attr
        self.ttl = ttl
        self.lock = threading.RLock()

        if func is not None:
            self.__call__(func)

    def __call__(self, func):
        functools.update_wrapper(self, func, updated=[])
        self.func = func
        return self

    def __get__(self, obj, cls):
        if self.ttl <= 0:
            value = self.func(cls)
            setattr(cls, self.__name__, value)
            return value

        now = time.time()
        with self.lock:
            try:
                value, last_updated = getattr(
                    cls, self.cache_attr)[self.__name__]
                if self.ttl < now - last_updated:
                    raise AttributeError
            except (KeyError, AttributeError):
                value = self.func(cls)
                try:
                    cache = getattr(cls, self.cache_attr)
                except AttributeError:
                    cache = {}
                    setattr(cls, self.cache_attr, cache)
                cache[self.__name__] = (value, now)
            return value

    def __delete__(self, obj):
        try:
            del getattr(obj, self.cache_attr)[self.__name__]
        except (AttributeError, KeyError):
            pass


class cached_property(object):
    """
    Thread safe decorator for readonly properties evaluated only once
    within TTL period.

    The default time-to-live (TTL) is 0 which is never expire, which
    will result the property be replaced by the value when first accessed.
    Set to positive number to enable TTL.

    It can be used to create a cached property like this:

        import random

        # the class containing the property must be a new-style class
        class MyClass(object):

            # create property whose value is cached for ten minutes
            @cached_property(ttl=600)
            def randint(self):
                # will only be evaluated every 10 min, at maximum.
                return random.randint(0, 100)

            # use all default parameters, never expired
            @cached_property
            def rand_float(self):
                return random.random()

    By default the value is cached in the '_prop_cache_' attribute of the
    object instance that has the property getter method wrapped by this
    decorator. The cache attribute value is a dictionary which has a key
    for every property of the object which is wrapped by this decorator.
    Each entry in the cache is created only when the property is accessed
    for the first time and is a two-element tuple with the last computed
    property value and the last time it was updated in seconds since the epoch.

    The cache dictionary attribute can be specified using the 'cache_attr'
    parameter of the decorator constructor.

    To expire a cached property value with positive TTL manually just do:

        del instance.property
        # or: del instance._prop_cache_[<property name>]

    """
    def __init__(self, func=None, ttl=0, cache_attr='_prop_cache_'):
        self.cache_attr = cache_attr
        self.ttl = ttl
        self.lock = threading.RLock()

        if func is not None:
            self.__call__(func)

    def __call__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        return self

    def __get__(self, obj, cls=None):
        if obj is None:
            return self

        if self.ttl <= 0:
            value = obj.__dict__[self.__name__] = self.func(obj)
            return value

        now = time.time()
        with self.lock:
            try:
                value, last_updated = getattr(
                    obj, self.cache_attr)[self.__name__]
                if self.ttl < now - last_updated:
                    raise AttributeError
            except (KeyError, AttributeError):
                value = self.func(obj)
                try:
                    cache = getattr(obj, self.cache_attr)
                except AttributeError:
                    cache = {}
                    setattr(obj, self.cache_attr, cache)
                cache[self.__name__] = (value, now)
            return value

    def __delete__(self, obj):
        try:
            del getattr(obj, self.cache_attr)[self.__name__]
        except (AttributeError, KeyError):
            pass


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
            raise AttributeError("Readonly property.")
        getattr(obj, self.attr)[self.key] = value

    def __delete__(self, obj):
        if self.read_only:
            raise AttributeError("Readonly property.")
        del getattr(obj, self.attr)[self.key]


def retry_on_error(tries, delay=3, backoff=2,
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

    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            m_delay = delay
            m_tries = list(reversed(range(tries)))
            for tries_remaining in m_tries:
                try:
                    return func(*args, **kwargs)
                except exceptions as err:
                    if tries_remaining > 0:
                        if hook is not None:
                            hook(tries_remaining, err, m_delay)
                        time.sleep(m_delay)
                        m_delay = m_delay * backoff
                    else:
                        raise

        return wrapper

    return deco


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

    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            m_tries, m_delay = tries, delay

            rv = func(*args, **kwargs)
            while m_tries > 0:
                if rv is True:
                    return True

                m_tries -= 1
                time.sleep(m_delay)
                m_delay *= backoff

                rv = func(*args, **kwargs)

            return False

        return wrapper

    return deco


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
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return defaultval

        return wrapper

    if func is not None:
        return deco(func)

    return deco


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

    DEFAULT_LEVEL = logging.DEBUG
    DEFAULT_FORMAT = '[%(levelname)1.1s %(asctime)s %(name)s] %(message)s'
    DEFAULT_DATE_FORMAT = '%y%m%d %H:%M:%S'

    logger_name = 'LogDecorator'

    def __new__(cls, func=None,
                logger=None, level=None, logger_name=None, propagate=True):
        self = object.__new__(cls)

        # Do basic configuration for the logging system if not already
        logging.basicConfig(level=cls.DEFAULT_LEVEL,
                            format=cls.DEFAULT_FORMAT,
                            datefmt=cls.DEFAULT_DATE_FORMAT)
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


class log_parameters(_LogDecorator):
    """
    Dumps out the arguments passed to a function before calling it.

    NOTE: other decorators must be defined upper this decorator,
          or it won't work.
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

    def __call__(self, func):
        f_name = func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.logger.log(self.level, 'Entering %s', f_name)
            try:
                f_result = func(*args, **kwargs)
            except Exception as err:
                self.logger.log(self.level, 'Exception in %s', f_name)
                raise
            else:
                self.logger.log(self.level, 'Exiting %s', f_name)
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
                self.flush()
                sys.stdout = stdout_bak

        return wrapper

    @property
    def buf(self):
        if not hasattr(self, '_buf'):
            setattr(self, '_buf', [])
        return self._buf

    @buf.setter
    def buf(self, buf):
        setattr(self, '_buf', buf)

    def write(self, text):
        self.buf.append(text)
        if text.endswith('\n'):
            self.flush()

    def flush(self):
        output = ''.join(self.buf).rstrip()
        if output:
            self.logger.log(self.level, output)
            self.buf = []


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
                print("result {0}".format(result.result()))

        result2 = long_process.start(13)

        try:
            print("result2 {0}".format(result2.result()))
        except asynchronous.NotYetDoneException:
            print "not ready"

        result3 = long_process.start(5)
        print("result3 {0}".format(result3.wait())

    """
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.err, self.exc_info = False, None

        def threaded(*args, **kwargs):
            try:
                self.queue.put(self.func(*args, **kwargs))
            except Exception as err:
                self.err = True
                self.exc_info = sys.exc_info()
            finally:
                self.wait_event.set()

        self.threaded = threaded

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def start(self, *args, **kwargs):
        self.queue = queue.Queue()
        self.wait_event = threading.Event()
        self.thread = threading.Thread(
            target=self.threaded, args=args, kwargs=kwargs)
        self.thread.start()
        return asynchronous.Result(self)

    class NotYetDoneException(Exception):
        pass

    class Result(object):
        def __init__(self, refer):
            self.refer = refer
            self._is_done = False

        def is_done(self):
            if not self._is_done:
                if self.refer.queue.empty():
                    if self.refer.thread.is_alive():
                        return False
            self._is_done = True
            return True

        def result(self):
            if not self.is_done():
                raise asynchronous.NotYetDoneException()
            if self.refer.err:
                exc_info = self.refer.exc_info
                reraise(exc_info[0], exc_info[1], exc_info[2])

            # cache the result, or deadlock happens when you retrieve
            # the result more than once
            if not hasattr(self, '_result'):
                setattr(self, '_result', self.refer.queue.get())
            return self._result

        def wait(self):
            self.refer.wait_event.wait()
            return self.result()


@singleton
class _Mock(object):
    """
    Return mock data from json file or default value when the decorated
    function raise NotImplementError exception.

    This class is a singleton for better cache strategy and performance.

    Usage example:

        my_mock = functools.partial(mock.from_file,
                                    file='/some/file.json', ttl=300)

        class MyClass(object):

            # provided there is key value "myclass_foo": "some value"
            # in the json file
            @my_mock(key='myclass_foo')
            def foo(*args, **kwargs):
                raise NotImplementedError()

            @my_mock(default={'foo': 'bar'})
            def bar(*args, **kwargs):
                raise my_mock.PleaseMockMe()

    """

    class PleaseMockMe(Exception):

        def __init__(self, key=None):
            self.key = key

    class KeyMissing(Exception):

        def __init__(self, key):
            self.key = key

    @staticmethod
    def fix_json(string):
        """
        https://gist.github.com/liftoff/ee7b81659673eca23cd9fc0d8b8e68b7
        Copyright: Dan McDougall <daniel.mcdougall@liftoffsoftware.com>

        Removes C-style comments and trailing commas from string.

        .. code-block:: javascript

            {
                // A comment!  You normally can't put these in JSON
                "testing": {
                    "foo": "bar", // <-- A trailing comma!  No worries.
                }, // <-- Another one!
                /*
                This style of comments will also be safely removed
                */
            }

        """
        comments_re = re.compile(
            r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
            re.DOTALL | re.MULTILINE
        )
        trailing_object_commas_re = re.compile(
            r'(,)\s*}(?=([^"\\]*(\\.|"([^"\\]*\\.)*[^"\\]*"))*[^"]*$)')
        trailing_array_commas_re = re.compile(
            r'(,)\s*\](?=([^"\\]*(\\.|"([^"\\]*\\.)*[^"\\]*"))*[^"]*$)')

        def uncomment(match):
            s = match.group(0)
            if s[0] == '/':
                return ''
            return s

        string = comments_re.sub(uncomment, string)
        string = trailing_object_commas_re.sub("}", string)
        string = trailing_array_commas_re.sub("]", string)
        return string

    def from_file(self, key=None, file=None, ttl=3600, default=None,
                  exceptions=(NotImplementedError, PleaseMockMe)):
        if default is None and not file:
            caller_dir = os.path.dirname(inspect.stack()[1][1])
            guess_files = [
                os.path.join(caller_dir, 'mock_data.json'),
                os.path.join(caller_dir, 'mock.json'),
            ]
            for gf in guess_files:
                if os.path.exists(gf):
                    file = gf
                    break
        if file:
            file = os.path.normpath(os.path.abspath(file))
            if not os.path.exists(file):
                raise IOError('mock file "%s" does not exists' % file)

            attr_name = 'from_file_{}'.format(hashlib.md5(b(file)).hexdigest())
            setattr(self.__class__, attr_name, cached_property(
                lambda obj: json.loads(self.fix_json(
                    open(file, encoding='utf8').read())), ttl=ttl))

        def deco(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as err:
                    if isinstance(err, _Mock.PleaseMockMe) and err.key:
                        m_k = err.key
                    else:
                        m_k = key
                    if m_k and file:
                        try:
                            return getattr(self, attr_name)[m_k]
                        except KeyError as err:
                            # expire the cache to force reloading
                            delattr(self, attr_name)
                            reraise(_Mock.KeyMissing, _Mock.KeyMissing(m_k),
                                    None)
                    if callable(default):
                        return default()
                    return default

            return wrapper

        return deco

    # shortcut to allow using the mock decorator without parameters
    __call__ = from_file


mock = _Mock()
