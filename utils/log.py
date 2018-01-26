# -*- coding:utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from contextlib import contextmanager
import logging
import sys
import warnings
import six

__all__ = [
    'log', 'config_logger', 'suppress_logger', 'LoggerMixin',
    'StreamLogWriter', 'RedirectStdHandler', 'log_stdout', 'log_stderr',
]

# Tornado's beautiful logging format
_FORMAT = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s'
_DATE_FORMAT = '%y%m%d %H:%M:%S'
_LOG_FORMATTER = logging.Formatter(_FORMAT, _DATE_FORMAT)

# global logger
log = logging.getLogger(__name__)
log._configured = False


def config_logger(func=None,
                  filename=sys.stderr, level=logging.INFO,
                  max_mb=10, backup_count=5,
                  enable_root=False, root_level=None,
                  suppress=('requests', 'urllib3')):
    if isinstance(level, six.string_types):
        level = getattr(logging, level.upper())
    if isinstance(root_level, six.string_types):
        root_level = getattr(logging, root_level.upper())

    def decorator(func):
        global log
        if log._configured:
            warnings.warn('global logger has already been configured, '
                          'this config will not take effect',
                          UserWarning, 3)
            return func

        # suppress the massive logging message from un-welcomed loggers
        # default: requests, urllib3
        if suppress:
            target_level = max(logging.WARNING, level)
            for name in suppress:
                suppress_logger(name, target_level)

        if enable_root:
            logging.basicConfig(level=root_level or level,
                                format=_FORMAT, datefmt=_DATE_FORMAT)

        log.setLevel(level)
        if filename is sys.stderr:
            # if root logger has already been configured, simply propagate
            # messages to it, avoid duplicates to stderr
            if logging.root.handlers:
                pass
            else:
                handler = logging.StreamHandler(sys.stderr)
                handler.setFormatter(_LOG_FORMATTER)
                log.addHandler(handler)
        else:
            handler = logging.handlers.RotatingFileHandler(
                filename,
                maxBytes=max_mb * 1024 * 1024,
                backupCount=backup_count)
            handler.setFormatter(_LOG_FORMATTER)
            log.addHandler(handler)

        log._configured = True
        return func

    if func is not None:
        return decorator(func)

    return decorator


def suppress_logger(name, level):
    msg = 'suppress level of logger "{}" to "{}"'.format(
        name, logging.getLevelName(level))
    warnings.warn(msg, UserWarning, 2)
    logging.getLogger(name).setLevel(level)


class LoggerMixin(object):
    """
    Convenience super-class to have a logger configured with the class name
    """

    # The log property is the de-facto standard in most programming languages
    @property
    def log(self):
        try:
            return self._log
        except AttributeError:
            self._log = logging.root.getChild(
                '{}.{}'.format(
                    self.__class__.__module__,
                    self.__class__.__name__
                ))
            return self._log


class StreamLogWriter(object):
    """Allows to redirect stdout and stderr to logger."""
    encoding = False

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self._buffer = []

    def write(self, message):
        self._buffer.append(message)
        if message.endswith('\n'):
            self.flush()

    def flush(self):
        """Ensure all logging output has been flushed."""
        output = ''.join(self._buffer).rstrip()
        if output:
            self.logger.log(self.level, output)
            self._buffer = []

    def isatty(self):
        """
        Indicate the fd is not connected to a tty(-like) device.
        For compatibility reasons.
        """
        return False


class RedirectStdHandler(logging.StreamHandler):
    """
    This class is like a StreamHandler using stderr/stdout, but always
    use whatever stderr/stdout is currently set to rather than the
    value of sys.stderr/sys.stdout at handler construction time.
    """
    def __init__(self, stream):
        if not isinstance(stream, six.string_types):
            raise ValueError("Cannot use file like objects. Use 'stdout' or "
                             "'stderr' as str and without 'ext://'.")
        self._use_stderr = True
        if 'stdout' in stream:
            self._use_stderr = False

        # StreamHandler tries to set self.stream
        logging.Handler.__init__(self)

    @property
    def stream(self):
        if self._use_stderr:
            return sys.stderr

        return sys.stdout


@contextmanager
def log_stdout(logger, level):
    writer = StreamLogWriter(logger, level)
    try:
        sys.stdout = writer
        yield
    finally:
        writer.flush()
        sys.stdout = sys.__stdout__


@contextmanager
def log_stderr(logger, level):
    writer = StreamLogWriter(logger, level)
    try:
        sys.stderr = writer
        yield
    finally:
        writer.flush()
        sys.stderr = sys.__stderr__
