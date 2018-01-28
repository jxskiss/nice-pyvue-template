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

# uvloop should be setup on the interpreter startup to avoid tricky problems
try:
    import uvloop
    import asyncio
    from tornado.platform.asyncio import AsyncIOMainLoop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    AsyncIOMainLoop().install()
except ImportError:
    warnings.warn("Cannot import asyncio/uvloop, fallback to Tornado's IOLoop")

from utils.tornado.api import ApiRequestHandler
from utils.tornado.scheduler import scheduler

__all__ = [
    'options', 'scheduler', 'service', 'health', 'heartbeat', 'run',
    'route', 'static', 'redirect', 'error',
    'get', 'post', 'put', 'delete', 'patch'
]


options.define('debug', type=bool, default=False, help='run server in debug mode')
options.define('port', type=int, default=8000, help='listening port')
options.define('addr', type=str, default='0.0.0.0', help='listening address')

_services = []
_handlers = []


def service(cls):
    global _services, _handlers
    _services.append(cls)

    routes = {}
    for attr, t in sorted(cls.__dict__.items()):
        if inspect.isfunction(t) and getattr(t, '__service_handler__'):
            meth, url = t.__service_handler__
            if meth in routes.setdefault(url, {}):
                raise ValueError('duplicate method %r for url %r' % (meth, url))
            routes[url][meth] = t
            if 'name' not in routes[url]:
                routes[url]['name'] = t.__name__.title()
            delattr(cls, attr)

    bases = (cls, ApiRequestHandler)
    if issubclass(cls, RequestHandler):
        bases = (cls, )
    for url, handler in list(routes.items()):
        handler_name = '{}_{}_Handler'.format(cls.__name__, handler.pop('name'))
        handler_class = type(handler_name, bases, {'__module__': cls.__module__})
        for m, f in handler.items():
            setattr(handler_class, m, f)
        _handlers.append((url, handler_class))

    return cls


def route(method, url):
    def decorator(func):
        func.__service_handler__ = (method.lower(), url)
        return func

    return decorator


get, post, put, delete, patch = map(
    lambda pair: functools.partial(*pair), zip(
        (route, ) * 5, ("GET", "POST", "PUT", "DELETE", "PATCH")))


def static(url, path):
    _handlers.append((url, StaticFileHandler, dict(path=path)))


def redirect(url, to):
    _handlers.append((url, RedirectHandler, dict(url=to)))


def error(url, status_code):
    _handlers.append((url, ErrorHandler, dict(status_code=status_code)))


def health(url=r'^/health$', text='ok'):

    @service
    class HealthyService(object):
        @get(url)
        def health(self):
            self.finish(text)


def heartbeat(url, interval=60, random_sleep=5, raise_error=False, **kwargs):

    @scheduler(start_at=time.time() + 1, every='%sseconds' % interval,
               random_sleep=random_sleep)
    async def beat():
        gen_log.info('sending heartbeat to: %s', url)
        client = AsyncHTTPClient()
        resp = await client.fetch(url, raise_error=raise_error, **kwargs)
        if resp.code != 200:
            gen_log.warning('heartbeat failed with status code %s: %r',
                            resp.code, resp.error)


def run(**app_kwargs):
    options.parse_command_line()

    if not _services:
        raise RuntimeError(
            'No service registered, make sure they are defined properly!')
    if not _handlers:
        raise RuntimeError(
            'No handler registered, make sure they are defined properly!')
    for svc in _services:
        gen_log.debug('Registered service: %r', svc)
    for url, handler, *_ in _handlers:
        gen_log.debug('Registered handler: %r, %r, subclass of: %r',
                      url, handler, handler.mro()[1])

    app = Application(
        handlers=_handlers,
        debug=options.debug,
        **app_kwargs
    )

    app.listen(options.port, options.addr)
    scheduler.start_all()

    ioloop.IOLoop.instance().start()


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

    # heartbeat('http://www.example.com/heartbeat')
    # To self-beat, before calling run(), options are not prepared
    options.add_parse_callback(
        lambda: heartbeat('http://127.0.0.1:%d/health' % options.port))

    # if using behind reverse proxy, pass xheaders=True
    # run(xheaders=True)
    run()
