# -*- coding:utf-8 -*-

from tornado.options import options


from .hello import handlers as hello_handlers
from .sockets import handlers as socket_handlers

handlers = hello_handlers + socket_handlers


if options.django:
    from .with_django import handlers as with_django_handlers

    handlers += with_django_handlers
