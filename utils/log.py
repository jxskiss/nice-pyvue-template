# -*- coding:utf-8 -*-
import logging
import sys
import warnings
import six

__all__ = ['log', 'config_logger', 'suppress_logger', 'LoggerMixin']

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
