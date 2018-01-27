#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
from importlib import import_module
from tornado import ioloop, web, wsgi
from tornado.options import options, define, parse_command_line
from tornado.log import gen_log
from utils import dotenv

define('debug', type=bool, default=False, help='run server in debug mode',
       callback=lambda debug: os.environ.update({'DEBUG': str(debug)}))
define('uvloop', type=bool, default=True, help='run server with uvloop')
define('django', type=bool, default=False, help='enable django integration')
define('django_threads', type=int, default=0, help='django thread pool size')
define('port', type=int, default=8000, help='listening port')
define('addr', type=str, default='0.0.0.0', help='listening address')


def main():
    # load environment variables from .env file
    dotenv.read_dotenv(dotenv.find_dotenv())
    parse_command_line()

    if options.uvloop:
        from tornado.platform.asyncio import AsyncIOMainLoop
        try:
            import asyncio
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            AsyncIOMainLoop().install()
        except ImportError:
            options.uvloop = False
            gen_log.error(
                'cannot import asyncio and uvloop, fallback to IOLoop')

    # serve django admin in debug mode
    # NOTE: any django related things must be AFTER parsing options
    options.django = options.django or options.debug

    # DJANGO_SETTINGS_MODULE MUST be available before importing any django
    # related things
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "{{ project_name }}.settings")
    dj_settings = None
    if options.django:
        if not options.debug:
            gen_log.warn(
                'WARNING: it is STRONGLY DISCOURAGED to use tornado and '
                'django within one process (one thread) in production!!!')

        import django
        import django.conf
        django.setup()
        dj_settings = django.conf.settings
    else:
        try:
            dj_settings = import_module(os.getenv('DJANGO_SETTINGS_MODULE'))
        except ImportError:
            pass

    from handlers import handlers

    if options.debug:
        # serve static files in debug mode
        handlers += [
            (r'^/apidoc/(.*)$', web.StaticFileHandler, dict(
                path='frontend/dist/apidoc', default_filename='index.html')),
            (r'^/media/(.+)$', web.StaticFileHandler, dict(
                path='staticfiles/media')),
        ]

        # serve django admin pages and static files in debug mode
        from handlers.with_django import FallbackHandler
        import django.core.wsgi
        django_wsgi = wsgi.WSGIContainer(
            django.core.wsgi.get_wsgi_application())
        django_handlers = [
            (r'^/admin/.*$', FallbackHandler, dict(fallback=django_wsgi)),
            (r'^/static/.*$', FallbackHandler, dict(fallback=django_wsgi)),
            # fallback any not matched request to django
            (r'^/.*$', FallbackHandler, dict(fallback=django_wsgi))
        ]
        handlers += django_handlers

    app = web.Application(
        handlers=handlers,
        debug=options.debug,
        cookie_secret=((dj_settings and dj_settings.SECRET_KEY) or
                       '{{ secret_key }}'),
        django_enabled=options.django,
        dj_settings=dj_settings,
        template_path='templates',
    )

    serving_mode = 'debug' if options.debug else 'production'
    django_mode = 'enabled' if options.django else 'disabled'
    gen_log.warn('starting server at %s:%s in %s mode with django %s...',
                 options.addr, options.port, serving_mode, django_mode)
    app.listen(options.port, options.addr, xheaders=True)

    ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
