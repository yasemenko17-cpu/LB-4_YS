"""Відкриті тести задачі 6: Томи для даних PostgreSQL.

Запуск: pytest tests/test_lab_06.py -k S2 (замініть S2 на свій набір).
Тут лише приклади з карток варіантів; повний набір перевірок є у викладача.
"""
import copy
import signal

import pytest
from conftest import load
from support import DRIVERS


def _same(a, b):
    """Рівність із допуском; список і кортеж вважаються однаковими послідовностями."""
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) < 1e-9
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_same(a[k], b[k]) for k in a)
    return a == b


def run(task, drv, kwargs, expected):
    """Запускає драйвер на вашому модулі. Помилки подано як ("!КласПомилки", "повідомлення")."""
    got = DRIVERS[drv](load(task), **copy.deepcopy(kwargs))
    assert _same(got, expected), f"отримано {got!r}, очікувалось {expected!r}"


def _ids(cases, prefix):
    return [f"{prefix}-{c[0]}-{i}" for i, c in enumerate(cases)]


@pytest.fixture(autouse=True)
def _watchdog():
    """Тест, що завис, завершується за 10 с."""
    def boom(signum, frame):
        raise TimeoutError("тест завис довше 10 с")
    old = signal.signal(signal.SIGALRM, boom)
    signal.alarm(10)
    yield
    signal.alarm(0)
    signal.signal(signal.SIGALRM, old)


T06 = [('S1',
  'volumes',
  {'project': 'notes',
   'db_image': 'postgres:16-alpine',
   'db_name': 'notesdb',
   'db_user': 'notes',
   'data_volume': 'pgdata',
   'init_dir': 'initdb',
   'backup_dir': 'backups'},
  {'has_version': False,
   'services': ['db'],
   'mounts': [('bind', './backups', '/backup', False),
              ('bind', './initdb', '/docker-entrypoint-initdb.d', True),
              ('volume', 'pgdata', '/var/lib/postgresql/data', False)],
   'top_volumes': {'pgdata': {}},
   'db_ports': [],
   'healthcheck': True,
   'password_literal': False}),
 ('S1',
  'volumes',
  {'project': 'inventory',
   'db_image': 'postgres:16-alpine',
   'db_name': 'inv',
   'db_user': 'inv',
   'data_volume': 'invdata',
   'init_dir': 'db/init',
   'backup_dir': 'db/backup'},
  {'has_version': False,
   'services': ['db'],
   'mounts': [('bind', './db/backup', '/backup', False),
              ('bind', './db/init', '/docker-entrypoint-initdb.d', True),
              ('volume', 'invdata', '/var/lib/postgresql/data', False)],
   'top_volumes': {'invdata': {}},
   'db_ports': [],
   'healthcheck': True,
   'password_literal': False}),
 ('S2',
  'volumes',
  {'project': 'notes',
   'db_image': 'postgres:16-alpine',
   'db_name': 'notesdb',
   'db_user': 'notes',
   'data_volume': 'pgdata',
   'init_dir': 'initdb',
   'backup_dir': 'backups',
   'volume_name': 'notes-data'},
  {'has_version': False,
   'services': ['db'],
   'mounts': [('bind', './backups', '/backup', False),
              ('bind', './initdb', '/docker-entrypoint-initdb.d', True),
              ('volume', 'pgdata', '/var/lib/postgresql/data', False)],
   'top_volumes': {'pgdata': {'name': 'notes-data'}},
   'db_ports': [],
   'healthcheck': True,
   'password_literal': False}),
 ('S2',
  'volumes',
  {'project': 'shop',
   'db_image': 'postgres:16-alpine',
   'db_name': 'notesdb',
   'db_user': 'notes',
   'data_volume': 'shopdb',
   'init_dir': 'sql',
   'backup_dir': 'backups',
   'volume_name': 'shop-pgdata'},
  {'has_version': False,
   'services': ['db'],
   'mounts': [('bind', './backups', '/backup', False),
              ('bind', './sql', '/docker-entrypoint-initdb.d', True),
              ('volume', 'shopdb', '/var/lib/postgresql/data', False)],
   'top_volumes': {'shopdb': {'name': 'shop-pgdata'}},
   'db_ports': [],
   'healthcheck': True,
   'password_literal': False}),
 ('S3',
  'volumes',
  {'project': 'notes',
   'db_image': 'postgres:16-alpine',
   'db_name': 'notesdb',
   'db_user': 'notes',
   'data_volume': 'pgdata',
   'init_dir': 'initdb',
   'backup_dir': 'backups',
   'external': True,
   'volume_name': 'apsik-ext'},
  {'has_version': False,
   'services': ['db'],
   'mounts': [('bind', './backups', '/backup', False),
              ('bind', './initdb', '/docker-entrypoint-initdb.d', True),
              ('volume', 'pgdata', '/var/lib/postgresql/data', False)],
   'top_volumes': {'pgdata': {'external': True, 'name': 'apsik-ext'}},
   'db_ports': [],
   'healthcheck': True,
   'password_literal': False}),
 ('S3',
  'volumes',
  {'project': 'shared',
   'db_image': 'postgres:16-alpine',
   'db_name': 'notesdb',
   'db_user': 'notes',
   'data_volume': 'store',
   'init_dir': 'initdb',
   'backup_dir': 'backups',
   'external': True,
   'volume_name': 'shared-pg-data'},
  {'has_version': False,
   'services': ['db'],
   'mounts': [('bind', './backups', '/backup', False),
              ('bind', './initdb', '/docker-entrypoint-initdb.d', True),
              ('volume', 'store', '/var/lib/postgresql/data', False)],
   'top_volumes': {'store': {'external': True, 'name': 'shared-pg-data'}},
   'db_ports': [],
   'healthcheck': True,
   'password_literal': False})]


@pytest.mark.parametrize("tag,drv,kwargs,expected", T06, ids=_ids(T06, "T06"))
def test_task_06(tag, drv, kwargs, expected):
    run(6, drv, kwargs, expected)
