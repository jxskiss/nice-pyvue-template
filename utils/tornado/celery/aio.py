# -*- coding: utf-8 -*-
from aioredis.errors import ChannelClosedError, ConnectionClosedError
from celery.exceptions import ImproperlyConfigured
import aioredis
import asyncio
import celery
import json
import logging
import re

_logger = logging.getLogger(__name__)


class AioCeleryProxy(object):
    """
    Commit celery task using this when you need to retrieve the result within
    Tornado/asyncio loop, ONLY redis (2.8+) backend is supported currently.

    Usage example:

        // tasks.py
        from celery import Celery
        import time

        app = Celery('tasks',
                     broker='redis://:@127.0.0.1:6379/0',
                     backend='redis://:@127.0.0.1:6379/1')

        @app.task
        def add(x, y):
            return x + y

        // app.py
        import asyncio
        import tasks

        celery_proxy = AioCeleryProxy()

        async def hello(x, y):
            result = await celery_proxy(tasks.add, x, y)
            print(result)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(hello(1, 2))
        loop.run_until_complete(celery_proxy.cleanup())

    Known issue:
        1.  The subscription connections may become unresponsive after some
            time, without throwing any exceptions. 
            If you run into this issue with the latest version of Redis change
            the defaults in redis.conf to:
                timeout 600
                tcp-keepalive 60

            See: https://gist.github.com/jxskiss/aadf53659837b2052145cfc1c37cc8ea#gistcomment-2231650
    """  # noqa

    def __init__(self, celery_app=None, loop=None):
        if celery_app is None:
            celery_app = celery.current_app
        self.backend = celery_app.conf['result_backend'] or ''
        self.backend_db = None
        self.pool = None
        self.pending_tasks = {}
        self.loop = loop or asyncio.get_event_loop()

        def _on_initialized(fut):
            try:
                fut.result()
            except Exception as exc:
                _logger.exception(exc)
                asyncio.ensure_future(self.cleanup())
            else:
                fut = asyncio.ensure_future(self.handle_events())
                fut.add_done_callback(
                    lambda f: asyncio.ensure_future(self.cleanup()))

        # schedule redis option checking and task result handler
        # on event loop startup
        fut = asyncio.ensure_future(self.initialize())
        fut.add_done_callback(_on_initialized)

    async def initialize(self):
        match = re.match(
            r'redis://(?::(\w+)?@)?([\w.]+):(\d+)/(\d{1,2})',
            self.backend
        )
        if not match:
            raise ImproperlyConfigured(
                'redis backend improperly configured: %s', self.backend)
        password, host, port, db_idx = match.groups()
        self.backend_db = int(db_idx or 0)

        if aioredis.__version__ < '1.0.0':
            aio_create_redis_pool = aioredis.create_pool
        else:
            aio_create_redis_pool = aioredis.create_redis_pool
        self.pool = await aio_create_redis_pool(
            (host, int(port)),
            db=self.backend_db, password=password,
            minsize=2)

        with await self.pool as red:
            redis_config = await red.config_get('notify-keyspace-events')
            notify_conf = redis_config.get('notify-keyspace-events')
            _logger.info('redis server notify-keyspace-events config: %r',
                         notify_conf)
            if not (notify_conf and 'E' in notify_conf and (
                    'A' in notify_conf or '$' in notify_conf)):
                await self.cleanup()
                raise ImproperlyConfigured(
                    'redis server notify-keyspace-events improperly '
                    'configured: %r' % notify_conf)

    async def cleanup(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def handle_events(self):
        while self.pool and not (self.loop.is_closed() or self.pool.closed):
            try:
                with await self.pool as sub:
                    channel = '__keyevent@{}__:set'.format(self.backend_db)
                    _logger.debug('subscribing channel: %s', channel)
                    channel = (await sub.psubscribe(channel))[0]
                    async for msg in channel.iter():
                        key = msg[1]
                        if key not in self.pending_tasks:
                            continue
                        await self.on_task_result(key)
            except (ChannelClosedError, ConnectionClosedError) as err:
                _logger.warning(
                    'unexpected %s error, retrying to connect to redis '
                    'in 2 seconds', type(err))
                await asyncio.sleep(2)
            except ConnectionRefusedError as err:
                _logger.warning(
                    'connecting to redis refused, retrying in 10 seconds')
                await asyncio.sleep(10)
            except Exception as err:
                if self.loop.is_closed():
                    return
                _logger.exception(
                    'unhandled error: %s, retrying in 60 seconds', err)
                await asyncio.sleep(60)

    async def on_task_result(self, backend_key):
        fut = self.pending_tasks.pop(backend_key)
        with await self.pool as res_client:
            result = await res_client.get(backend_key)
            result = json.loads(result.decode('utf-8'))['result']
        fut.set_result(result)

    async def submit(self, task, *args,
                     callback=None, timeout=30, **kwargs):
        task_result = task.delay(*args, **kwargs)
        backend_key = task.backend.get_key_for_task(task_result.task_id)
        fut = self.loop.create_future()
        self.pending_tasks[backend_key] = fut
        if callback:
            fut.add_done_callback(lambda f: callback(f.result()))

        if timeout <= 0:
            result = await fut
            return result

        try:
            result = await asyncio.wait_for(fut, timeout=timeout)
            return result
        except asyncio.futures.TimeoutError as err:
            self.pending_tasks.pop(backend_key)
            raise

    # shortcut
    __call__ = submit
