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
    Tornado/asyncio loop, ONLY redis backend is supported.
    NOTE: this is not a common case when using celery and is not recommended.
    """

    def __init__(self, celery_app=None, loop=None):
        if celery_app is None:
            celery_app = celery.current_app
        self.backend = celery_app.conf['result_backend'] or ''
        self.backend_db = None
        self.pool = None
        self.pending_tasks = {}
        self.loop = loop or asyncio.get_event_loop()
        self.initialize()

    def initialize(self):
        match = re.match(
            r'redis://(?::(\w+)?@)?([\w.]+):(\d+)/(\d{1,2})',
            self.backend
        )
        if not match:
            raise ImproperlyConfigured(
                'redis backend improperly configured: %s', self.backend)

        password, host, port, db_idx = match.groups()
        self.backend_db = int(db_idx or 0)
        self.pool = self.loop.run_until_complete(
            aioredis.create_pool(
                (host, int(port)),
                db=self.backend_db, password=password,
                minsize=2))
        try:
            self.loop.run_until_complete(self._check_redis_option())
        except ImproperlyConfigured:
            self.loop.run_until_complete(self.cleanup())
            raise
        self.loop.call_soon(asyncio.ensure_future, self.handle_events())

    async def _check_redis_option(self):
        with await self.pool as red:
            redis_config = await red.config_get('notify-keyspace-events')
            notify_conf = redis_config.get('notify-keyspace-events')
            _logger.info('redis server notify-keyspace-events config: "%s"',
                         notify_conf)
            if not (notify_conf and (
                    ('E' in notify_conf and 'A' in notify_conf) or
                    ('E' in notify_conf and '$' in notify_conf))):
                raise ImproperlyConfigured(
                    'redis server notify-keyspace-events improperly '
                    'configured: "%s"' % (notify_conf, ))

    async def cleanup(self):
        self.pool.close()
        await self.pool.wait_closed()

    async def handle_events(self):
        while not (self.loop.is_closed() or self.pool.closed):
            try:
                await self._handle_events()
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

    async def _handle_events(self):
        with await self.pool as sub:
            channel = '__keyevent@{}__:set'.format(self.backend_db)
            _logger.debug('subscribing channel: %s', channel)
            channel = (await sub.psubscribe(channel))[0]
            async for msg in channel.iter():
                _logger.debug('message: %s', msg)
                key = msg[1]
                if key not in self.pending_tasks:
                    continue
                await self.on_task_result(key)

    async def on_task_result(self, backend_key):
        fut = self.pending_tasks.pop(backend_key)
        with await self.pool as res_client:
            result = await res_client.get(backend_key)
            result = json.loads(result.decode('utf-8'))['result']
        fut.set_result(result)

    async def commit(self, task, *args,
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
