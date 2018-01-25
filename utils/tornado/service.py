# -*- coding:utf-8 -*-
"""
Tiny micro-service utility built of top of tornado, full of black magic.
Using together with other "utils.tornado.*" utilities is preferred, though
it can be used independently also.
"""
from tornado import ioloop, gen
from tornado.httpclient import AsyncHTTPClient
from tornado.log import gen_log
from tornado.options import options
from tornado.web import (Application, RequestHandler, StaticFileHandler,
                         RedirectHandler, ErrorHandler)
import functools
import inspect
import time
import warnings

from utils.tornado.api import ApiRequestHandler
from utils.tornado.scheduler import scheduler

__all__ = [
    'options', 'scheduler', 'service', 'health', 'heartbeat', 'run',
    'route', 'static', 'redirect', 'error',
    'get', 'post', 'put', 'delete', 'patch'
]


options.define('debug', type=bool, default=False, help='run server in debug mode')
options.define('uvloop', type=bool, default=True, help='run server with uvloop')
options.define('port', type=int, default=8000, help='listening port')
options.define('addr', type=str, default='0.0.0.0', help='listening address')

_services = []
_routes = {}
_handlers = {}


def service(cls):
    global _services, _routes, _handlers
    _services.append(cls)

    for attr, t in cls.__dict__.copy().items():
        if inspect.isfunction(t) and getattr(t, '_is_handler_method'):
            delattr(cls, attr)

    bases = (cls, ApiRequestHandler)
    if issubclass(cls, RequestHandler):
        bases = (cls, )
    for url, methods in list(_routes.items()):
        handler_name = cls.__name__ + '_' + methods.pop('name')
        handler_class = type(handler_name, bases, {'__module__': cls.__module__})
        for m, f in methods.items():
            setattr(handler_class, m, f)
        _handlers[url] = (url, handler_class)
        _routes.pop(url)

    return cls


def route(method, url):
    def decorator(func):
        methods = _routes.get(url, {})
        if not methods:
            methods['name'] = func.__name__.title() + '_Handler'

        methods[method.lower()] = func
        _routes[url] = methods
        func._is_handler_method = True
        return func

    return decorator


get, post, put, delete, patch = map(
    lambda pair: functools.partial(*pair), zip(
        (route, ) * 5, ("GET", "POST", "PUT", "DELETE", "PATCH")))


def static(url, path):
    _handlers[url] = (url, StaticFileHandler, dict(path=path))


def redirect(url, to):
    _handlers[url] = (url, RedirectHandler, dict(url=to))


def error(url, status_code):
    _handlers[url] = (url, ErrorHandler, dict(status_code=status_code))


def health(url=r'^/health$', text='ok'):

    @service
    class HealthyService(object):
        @get(url)
        def health(self):
            self.finish(text)

    return HealthyService


def heartbeat(url, interval=60, random_sleep=5, raise_error=False, **kwargs):

    @scheduler(time.time() + 1, '%sseconds' % interval, random_sleep)
    async def beat():
        gen_log.info('sending heartbeat to: %s', url)
        client = AsyncHTTPClient()
        resp = await client.fetch(url, raise_error=raise_error, **kwargs)
        if resp.code != 200:
            gen_log.warning('heartbeat failed with status code %s: %s',
                            resp.code, resp.body.decode())


def run(**app_kwargs):
    options.parse_command_line()

    if options.uvloop:
        from tornado.platform.asyncio import AsyncIOMainLoop
        try:
            import asyncio
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            AsyncIOMainLoop().instance()
        except ImportError:
            options.uvloop = False
            warnings.warn("Cannot import asyncio/uvloop, fallback to Tornado's IOLoop")

    if not _services:
        raise RuntimeError('No service registered, make sure they are defined properly!')
    if not _handlers:
        raise RuntimeError('No handler registered, make sure they are defined properly!')
    for svc in _services:
        gen_log.debug('Registered service: %r', svc)
    for url, handler in _handlers.items():
        gen_log.debug('Registered handler: %r, %r, subclass of: %r',
                      url, handler, handler[1].mro()[1:])

    app = Application(
        handlers=_handlers.values(),
        debug=options.debug,
        **app_kwargs
    )

    app.listen(options.port, options.addr)
    scheduler.start_all()

    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    @service
    class Service(object):
        @get('^/hello$')
        async def hello(self):
            await gen.sleep(0.001)
            name = self.get_argument('name', '')
            self.finish('hello, %s!' % (name or 'anonymous'))

    redirect('/world', '/hello')
    health('/health', 'ok')
    heartbeat('http://127.0.0.1:%d/health' % options.port)

    run()
