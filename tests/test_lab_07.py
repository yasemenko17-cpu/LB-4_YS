"""Відкриті тести задачі 7: Мережі frontend і backend.

Запуск: pytest tests/test_lab_07.py -k S2 (замініть S2 на свій набір).
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


T07 = [('S1',
  'networks',
  {'project': 'shop',
   'proxy_image': 'nginx:1.27-alpine',
   'web_image': 'shop-web:1.0',
   'db_image': 'postgres:16-alpine',
   'public_port': 8080},
  {'has_version': False,
   'services': ['db', 'proxy', 'web'],
   'networks': {'db': ['backend'], 'proxy': ['frontend'], 'web': ['backend', 'frontend']},
   'ports': {'db': [], 'proxy': [('127.0.0.1', '8080', '80')], 'web': []},
   'top_networks': ['backend', 'frontend'],
   'backend_internal': True,
   'frontend_internal': False,
   'web_aliases': {'frontend': [], 'backend': []},
   'subnets': [],
   'host_network': False}),
 ('S1',
  'networks',
  {'project': 'blog',
   'proxy_image': 'nginx:1.27-alpine',
   'web_image': 'blog-web:2',
   'db_image': 'postgres:16-alpine',
   'public_port': 9000},
  {'has_version': False,
   'services': ['db', 'proxy', 'web'],
   'networks': {'db': ['backend'], 'proxy': ['frontend'], 'web': ['backend', 'frontend']},
   'ports': {'db': [], 'proxy': [('127.0.0.1', '9000', '80')], 'web': []},
   'top_networks': ['backend', 'frontend'],
   'backend_internal': True,
   'frontend_internal': False,
   'web_aliases': {'frontend': [], 'backend': []},
   'subnets': [],
   'host_network': False}),
 ('S2',
  'networks',
  {'project': 'shop',
   'proxy_image': 'nginx:1.27-alpine',
   'web_image': 'shop-web:1.0',
   'db_image': 'postgres:16-alpine',
   'public_port': 8080,
   'alias': 'app'},
  {'has_version': False,
   'services': ['db', 'proxy', 'web'],
   'networks': {'db': ['backend'], 'proxy': ['frontend'], 'web': ['backend', 'frontend']},
   'ports': {'db': [], 'proxy': [('127.0.0.1', '8080', '80')], 'web': []},
   'top_networks': ['backend', 'frontend'],
   'backend_internal': True,
   'frontend_internal': False,
   'web_aliases': {'frontend': ['app'], 'backend': []},
   'subnets': [],
   'host_network': False}),
 ('S2',
  'networks',
  {'project': 'shop',
   'proxy_image': 'nginx:1.27-alpine',
   'web_image': 'shop-web:1.0',
   'db_image': 'postgres:16-alpine',
   'public_port': 8081,
   'alias': 'backend-api'},
  {'has_version': False,
   'services': ['db', 'proxy', 'web'],
   'networks': {'db': ['backend'], 'proxy': ['frontend'], 'web': ['backend', 'frontend']},
   'ports': {'db': [], 'proxy': [('127.0.0.1', '8081', '80')], 'web': []},
   'top_networks': ['backend', 'frontend'],
   'backend_internal': True,
   'frontend_internal': False,
   'web_aliases': {'frontend': ['backend-api'], 'backend': []},
   'subnets': [],
   'host_network': False}),
 ('S3',
  'networks',
  {'project': 'shop',
   'proxy_image': 'nginx:1.27-alpine',
   'web_image': 'shop-web:1.0',
   'db_image': 'postgres:16-alpine',
   'public_port': 8080,
   'subnet': '10.77.0.0/24'},
  {'has_version': False,
   'services': ['db', 'proxy', 'web'],
   'networks': {'db': ['backend'], 'proxy': ['frontend'], 'web': ['backend', 'frontend']},
   'ports': {'db': [], 'proxy': [('127.0.0.1', '8080', '80')], 'web': []},
   'top_networks': ['backend', 'frontend'],
   'backend_internal': True,
   'frontend_internal': False,
   'web_aliases': {'frontend': [], 'backend': []},
   'subnets': ['10.77.0.0/24'],
   'host_network': False}),
 ('S3',
  'networks',
  {'project': 'shop',
   'proxy_image': 'nginx:1.27-alpine',
   'web_image': 'shop-web:1.0',
   'db_image': 'postgres:16-alpine',
   'public_port': 8080,
   'subnet': '172.30.5.0/24',
   'alias': 'app'},
  {'has_version': False,
   'services': ['db', 'proxy', 'web'],
   'networks': {'db': ['backend'], 'proxy': ['frontend'], 'web': ['backend', 'frontend']},
   'ports': {'db': [], 'proxy': [('127.0.0.1', '8080', '80')], 'web': []},
   'top_networks': ['backend', 'frontend'],
   'backend_internal': True,
   'frontend_internal': False,
   'web_aliases': {'frontend': ['app'], 'backend': []},
   'subnets': ['172.30.5.0/24'],
   'host_network': False})]


@pytest.mark.parametrize("tag,drv,kwargs,expected", T07, ids=_ids(T07, "T07"))
def test_task_07(tag, drv, kwargs, expected):
    run(7, drv, kwargs, expected)
