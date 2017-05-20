#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys

for _lib_dir in ('libs', 'apps'):
    _lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), _lib_dir)
    if os.path.exists(_lib_path) and _lib_path not in sys.path:
        sys.path.insert(0, _lib_path)
del _lib_dir, _lib_path

from importlib import import_module
from tornado import ioloop, web, wsgi
from tornado.options import options, define, parse_command_line
from tornado.log import gen_log


define('debug', type=bool, default=False, help='run server in debug mode',
       callback=lambda debug: os.environ.update({'DJANGO_DEBUG': str(debug)}))
define('django', type=bool, default=False, help='enable django integration')
define('port', type=int, default=8000, help='listening port')
define('addr', type=str, default='0.0.0.0', help='listening address')

# DJANGO_SETTINGS_MODULE MUST be available before import any django related things
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ project_name }}.settings")
dj_settings = None


def main():
    global dj_settings

    # load environment variables from .env file
    import dotenv
    dotenv.read_dotenv()

    parse_command_line()

    # serve django admin in debug mode
    # NOTE: any django related things must be AFTER parsing options
    options.django = options.django or options.debug

    if options.django:
        if not options.debug:
            gen_log.warn('WARNING: it is STRONGLY DISCOURAGED to use tornado and django '
                         'within one process (one thread) in production!!!')

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
        # serve static apidoc files in debug mode
        handlers += [
            (r'^/apidoc/(.*)$', web.StaticFileHandler, dict(
                path='staticfiles/apidoc', default_filename='index.html')),
        ]

        # serve django admin pages and static files in debug mode
        import django.core.wsgi
        django_wsgi = wsgi.WSGIContainer(django.core.wsgi.get_wsgi_application())
        django_handlers = [
            (r'^/admin/.*$', web.FallbackHandler, dict(fallback=django_wsgi)),
            (r'^/static/.*$', web.FallbackHandler, dict(fallback=django_wsgi)),
            # fallback any not matched request to django
            (r'^/.*$', web.FallbackHandler, dict(fallback=django_wsgi))
        ]
        handlers += django_handlers

    app = web.Application(
        handlers=handlers,
        debug=options.debug,
        cookie_secret=(dj_settings and dj_settings.SECRET_KEY) or '{{ secret_key }}',
        django_enabled=options.django,
        dj_settings=dj_settings,
        template_path='templates',
    )

    serving_mode = 'debug' if options.debug else 'production'
    django_mode = 'enabled' if options.django else 'disabled'
    gen_log.warn('starting server at %s:%s in %s mode with django %s...',
                 options.addr, options.port, serving_mode, django_mode)
    app.listen(options.port, options.addr)
    ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
