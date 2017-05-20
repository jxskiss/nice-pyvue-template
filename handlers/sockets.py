# -*- coding:utf-8 -*-

import datetime
from tornado import gen
from tornado.log import gen_log
from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler, WebSocketClosedError


class EchoPageHandler(RequestHandler):

    def get(self, *args, **kwargs):
        self.render('websocket/echo_page.html')


class EchoTimeWebSocket(WebSocketHandler):
    _clients = set()

    def __init__(self, *args, **kwargs):
        super(EchoTimeWebSocket, self).__init__(*args, **kwargs)

    def check_origin(self, origin):
        # disable origin check
        return True

    @gen.coroutine
    def open(self, *args, **kwargs):
        gen_log.info("websocket connection from: %s" % self.request.remote_ip)
        self.write_message("Hello buddy, what's your name?")

    @gen.coroutine
    def on_message(self, message):
        nickname = message.strip()

        self.add_client(self)
        self.write_message("Nice to meet you, {}!".format(nickname))

        # start time echo loop
        yield self.echo_time()

    def on_close(self):
        gen_log.info("connection closed: %s" % self.request.remote_ip)

    @classmethod
    def add_client(cls, client):
        cls._clients.add(client)

    @classmethod
    def remove_client(cls, client):
        cls._clients.discard(client)

    @gen.coroutine
    def echo_time(self):
        try:
            # send current time to client every 5 seconds
            while True:
                now = datetime.datetime.now()
                self.write_message(now.isoformat(' '))
                yield gen.sleep(5)
        except WebSocketClosedError:
            self.remove_client(self)
        except Exception as err:
            gen_log.warn('unexpected error in echo websocket', exc_info=err)


handlers = [
    (r'/tornado/hello-socket', EchoPageHandler),
    (r'/tornado/socks/echo', EchoTimeWebSocket),
]
