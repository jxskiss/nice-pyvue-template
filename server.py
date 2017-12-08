#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
from tornado import ioloop, web
from tornado.options import options, define, parse_command_line
from tornado.log import gen_log
from utils import dotenv

define('debug', type=bool, default=False, help='run server in debug mode')
define('uvloop', type=bool, default=True, help='run server with uvloop')
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

    from handlers import handlers

    if options.debug:
        # serve static files in debug mode
        handlers += [
            (r'^/apidoc/(.*)$', web.StaticFileHandler, dict(
                path='frontend/dist/apidoc', default_filename='index.html')),
            (r'^/media/(.+)$', web.StaticFileHandler, dict(
                path='staticfiles/media')),
            (r'^/static/(.+)$', web.StaticFileHandler, dict(
                path='staticfiles/static')),
        ]

    app = web.Application(
        handlers=handlers,
        debug=options.debug,
        cookie_secret=os.getenv('SECRET_KEY') or '{{ secret_key }}',
        template_path='templates',
    )

    serving_mode = 'debug' if options.debug else 'production'
    gen_log.warn('starting server at %s:%s in %s mode...',
                 options.addr, options.port, serving_mode)
    app.listen(options.port, options.addr)

    if options.uvloop:
        asyncio.get_event_loop().run_forever()
    else:
        ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
