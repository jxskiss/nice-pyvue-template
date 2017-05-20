# -*- coding:utf-8 -*-

from tornado import web, gen


class TornadoHelloHandler(web.RequestHandler):
    """
    A pure tornado request handler.
    """

    @gen.coroutine
    def get(self):
        self.finish('Hello from tornado!')


handlers = [
    ('^/tornado/hello$', TornadoHelloHandler),
]
