# -*- coding:utf-8 -*-

from importlib import import_module

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

    def initialize(self):
        self.dj_request = DummyRequest()
        self.dj_user = None
        super(WithDjangoHandler, self).initialize()

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


class DjangoHelloHandler(WithDjangoHandler):
    """
    Demo handler integrating with django.
    """

    def get(self):
        user = self.get_current_user()
        self.finish('Hello django user: %s, your session key is: %s.'
                    % (user.username or 'anonymous',
                       self.dj_request.session.session_key))


handlers = [
    ('^/tornado/hello-django$', DjangoHelloHandler),
]
