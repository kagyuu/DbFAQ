"""単体テスト用の偽の Oracle プール・接続・カーソル。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace


class FakeCursor:
    def __init__(self, conn: FakeConnection):
        self.conn = conn
        self.description = None
        self._rows: list = []

    async def execute(self, sql, params=None, **kwargs):
        self.conn.calls.append(("cursor.execute", sql, params or kwargs))
        result = self.conn.responder(sql, params or kwargs)
        if isinstance(result, Exception):
            raise result
        description, rows = result
        self.description = description
        self._rows = list(rows)
        self._pos = 0

    async def fetchall(self):
        return self._rows

    async def fetchmany(self, n):
        self.conn.calls.append(("cursor.fetchmany", n))
        error = getattr(self.conn, "fetch_error", None)
        if error is not None and self._pos > 0:
            raise error
        batch = self._rows[self._pos : self._pos + n]
        self._pos += len(batch)
        return batch

    def close(self):
        pass


class FakeConnection:
    def __init__(self, responder=None, fail_on=None, rollback_error=None, version="23.26.3.0.0"):
        self.calls: list = []
        self.call_timeout = 0
        self.current_schema = None
        self.version = version
        self.responder = responder or (lambda sql, params: (None, []))
        self.fail_on = fail_on or {}
        self.rollback_error = rollback_error

    async def execute(self, sql, params=None, **kwargs):
        self.calls.append(("execute", sql))
        if sql in self.fail_on:
            raise self.fail_on[sql]

    def cursor(self):
        return FakeCursor(self)

    async def rollback(self):
        self.calls.append(("rollback",))
        if self.rollback_error:
            raise self.rollback_error


class FakePool:
    def __init__(self, conn: FakeConnection):
        self.conn = conn

    @asynccontextmanager
    async def acquire(self):
        yield self.conn

    async def close(self, force=False):
        pass


def col(name: str, type_name: str):
    """cursor.description の 1 要素相当。"""
    return SimpleNamespace(name=name, type_code=SimpleNamespace(name=type_name))
