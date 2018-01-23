# -*- coding:utf-8 -*-

from importlib import import_module
from tornado.concurrent import run_on_executor
from tornado.web import RequestHandler
from django.contrib import auth


class DummyRequest(object):
    pass


class WithDjangoHandler(RequestHandler):
    """
    Base handler for integration with django.
    To use django integrated handlers, the django MUST be setup
    when instantiate the web.Application object.
    """

    _executor = None

    # FIXME: run_on_executor is thread-unsafe, is there pitfalls?
    @property
    def executor(self):
        executor = WithDjangoHandler._executor
        if executor is not None:
            return executor

        from tornado.options import options
        from warnings import warn
        executor = None
        if options.django_threads > 0:
            try:
                from concurrent.futures import ThreadPoolExecutor
                executor = ThreadPoolExecutor(options.django_threads)
            except ImportError:
                warn(
                    'package concurrent.futures not installed, '
                    'dummy_executor (main thread) will be used instead',
                    UserWarning)
        else:
            warn(
                'options.django_threads is improperly configured as %s, '
                'dummy_executor (main thread) will be used instead'
                % options.django_threads, UserWarning)
        if not executor:
            from tornado.concurrent import dummy_executor
            executor = dummy_executor
        setattr(WithDjangoHandler, '_executor', executor)
        return executor

    def initialize(self):
        self.dj_request = DummyRequest()
        self.dj_user = None

    @property
    def dj_settings(self):
        return self.settings['dj_settings']

    def get_current_user(self):
        """
        Get user session with django's session facility.
        """
        if self.dj_user is None:
            engine = import_module(self.dj_settings.SESSION_ENGINE)
            session_key = self.get_cookie(self.dj_settings.SESSION_COOKIE_NAME)
            self.dj_request.session = engine.SessionStore(session_key)
            self.dj_user = auth.get_user(self.dj_request)
        return self.dj_user


class FallbackHandler(WithDjangoHandler):

    def initialize(self, fallback):
        self.fallback = fallback

    @run_on_executor
    def prepare(self):
        self.fallback(self.request)
        self._finished = True


class DjangoHelloHandler(WithDjangoHandler):
    """
    Demo handler integrating with django.
    """

    @run_on_executor
    def get(self):
        user = self.get_current_user()
        self.finish('Hello django user: %s, your session key is: %s.'
                    % (user.username or 'anonymous',
                       self.dj_request.session.session_key))


handlers = [
    ('^/tornado/hello-django$', DjangoHelloHandler),
]
