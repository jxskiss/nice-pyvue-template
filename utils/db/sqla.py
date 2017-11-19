# -*- coding:utf-8 -*-
from sqlalchemy.pool import NullPool
from sqlalchemy import engine, exc, event
import sqlalchemy as sa

_engines = {}


# http://docs.sqlalchemy.org/en/latest/core/pooling.html#disconnect-handling-pessimistic  # noqa
@event.listens_for(engine.Engine, "engine_connect")
def ping_connection(connection, branch):
    if branch:
        # "branch" refers to a sub-connection of a connection,
        # we don't want to bother pinging on these.
        return

    # turn off "close with result".  This flag is only used with
    # "connectionless" execution, otherwise will be False in any case
    save_should_close_with_result = connection.should_close_with_result
    connection.should_close_with_result = False

    try:
        # run a SELECT 1.   use a core select() so that
        # the SELECT of a scalar value without a table is
        # appropriately formatted for the backend
        connection.scalar(sa.select([1]))
    except exc.DBAPIError as err:
        # catch SQLAlchemy's DBAPIError, which is a wrapper
        # for the DBAPI's exception.  It includes a .connection_invalidated
        # attribute which specifies if this connection is a "disconnect"
        # condition, which is based on inspection of the original exception
        # by the dialect in use.
        if err.connection_invalidated:
            # run the same SELECT again - the connection will re-validate
            # itself and establish a new connection.  The disconnect detection
            # here also causes the whole connection pool to be invalidated
            # so that all stale connections are discarded.
            connection.scalar(sa.select([1]))
        else:
            raise
    finally:
        # restore "close with result"
        connection.should_close_with_result = save_should_close_with_result


def global_engine(dsn, pool=True):
    global _engines

    pool_class = None if pool else NullPool
    if not dsn:
        return None
    if dsn not in _engines:
        _engines[dsn] = sa.create_engine(dsn, poolclass=pool_class)
    return _engines[dsn]
