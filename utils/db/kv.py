# -*- coding: utf-8 -*-
import datetime
import json
import sqlalchemy as sa


class KVStoreClient(object):
    """
    KVStore client using with schema as utils.django.models.KVStore.
    """
    backend_type = 'database'

    def __init__(self, db_engine, tb_name='common_kvstore'):
        self.db_engine = db_engine
        self.tb_name = tb_name

    def _get(self, key):
        return self.db_engine.execute(
            sa.text(
                u"""
                select v from {} where k = :key
                where expire_at < :now
                """.format(self.tb_name)
            ),
            key=key, now=datetime.datetime.now()
        ).scalar()

    def get(self, key, default=None):
        value = self._get(key)
        return value or default

    def get_json(self, key, default=None):
        value = self._get(key)
        if value:
            return json.loads(value)
        return default

    def _set(self, key, value, expire_at=None):
        result = self.db_engine.execute(
            sa.text(
                u"""
                insert into {} (k, v, create_at, update_at, expire_at)
                values (:key, :value, now(), now(), :expire_at)
                on conflict (k) do update
                    set value = excluded.value,
                        update_at = excluded.update_at,
                        expire_at = excluded.expire_at
                """.format(self.tb_name)
            ).execution_options(autocommit=True),
            key=key, value=value, expire_at=expire_at
        )
        return result

    def set(self, key, value, expire_at=None):
        result = self._set(key, value, expire_at)
        return result.rowcount

    def set_json(self, key, value, expire_at=None):
        value = json.dumps(value)
        result = self._set(key, value, expire_at)
        return result.rowcount

    def del_key(self, key):
        result = self.db_engine.execute(
            sa.text(
                u"""
                delete from {} where k = :key
                """.format(self.tb_name)
            ).execution_options(autococmmit=True),
            key=key
        )
        return result.rowcount
