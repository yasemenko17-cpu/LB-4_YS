"""Відкриті тести задачі 5: Стек web + PostgreSQL: healthcheck і depends_on.

Запуск: pytest tests/test_lab_05.py -k S2 (замініть S2 на свій набір).
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


T05 = [('S1',
  'web_db',
  {'project': 'shop',
   'web_image': 'shop-web:1.0',
   'web_port': 8000,
   'web_health': ['CMD',
                  'python',
                  '-c',
                  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"],
   'db_image': 'postgres:16-alpine',
   'db_name': 'shopdb',
   'db_user': 'shop',
   'host_port': 8080},
  {'has_version': False,
   'name': 'shop',
   'services': ['db', 'web'],
   'db_image': 'postgres:16-alpine',
   'db_health': ['CMD-SHELL', 'pg_isready -U shop -d shopdb'],
   'db_health_params': ['interval', 'retries', 'timeout'],
   'db_ports': [],
   'web_image': 'shop-web:1.0',
   'web_build': None,
   'web_ports': [('127.0.0.1', '8080', '8000')],
   'web_depends': {'db': 'service_healthy'},
   'web_health': ['CMD',
                  'python',
                  '-c',
                  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"],
   'database_url': 'postgresql://shop:${POSTGRES_PASSWORD}@db:5432/shopdb',
   'password_literal': False,
   'db_env': {'POSTGRES_DB': 'shopdb', 'POSTGRES_USER': 'shop'},
   'restart': {'db': 'unless-stopped', 'web': 'unless-stopped'}}),
 ('S1',
  'web_db',
  {'project': 'blog',
   'web_image': 'ghcr.io/lab/blog:2.1',
   'web_port': 5000,
   'web_health': ['CMD-SHELL', 'wget -q -O /dev/null http://127.0.0.1:5000/health || exit 1'],
   'db_image': 'postgres:16',
   'db_name': 'blogdb',
   'db_user': 'blog',
   'host_port': 5050},
  {'has_version': False,
   'name': 'blog',
   'services': ['db', 'web'],
   'db_image': 'postgres:16',
   'db_health': ['CMD-SHELL', 'pg_isready -U blog -d blogdb'],
   'db_health_params': ['interval', 'retries', 'timeout'],
   'db_ports': [],
   'web_image': 'ghcr.io/lab/blog:2.1',
   'web_build': None,
   'web_ports': [('127.0.0.1', '5050', '5000')],
   'web_depends': {'db': 'service_healthy'},
   'web_health': ['CMD-SHELL', 'wget -q -O /dev/null http://127.0.0.1:5000/health || exit 1'],
   'database_url': 'postgresql://blog:${POSTGRES_PASSWORD}@db:5432/blogdb',
   'password_literal': False,
   'db_env': {'POSTGRES_DB': 'blogdb', 'POSTGRES_USER': 'blog'},
   'restart': {'db': 'unless-stopped', 'web': 'unless-stopped'}}),
 ('S2',
  'web_db',
  {'project': 'api',
   'web_image': 'node-api:3',
   'web_port': 3000,
   'web_health': ['CMD', 'wget', '-q', '-O', '/dev/null', 'http://127.0.0.1:3000/health'],
   'db_image': 'postgres:15-alpine',
   'db_name': 'apidb',
   'db_user': 'api',
   'host_port': 3001},
  {'has_version': False,
   'name': 'api',
   'services': ['db', 'web'],
   'db_image': 'postgres:15-alpine',
   'db_health': ['CMD-SHELL', 'pg_isready -U api -d apidb'],
   'db_health_params': ['interval', 'retries', 'timeout'],
   'db_ports': [],
   'web_image': 'node-api:3',
   'web_build': None,
   'web_ports': [('127.0.0.1', '3001', '3000')],
   'web_depends': {'db': 'service_healthy'},
   'web_health': ['CMD', 'wget', '-q', '-O', '/dev/null', 'http://127.0.0.1:3000/health'],
   'database_url': 'postgresql://api:${POSTGRES_PASSWORD}@db:5432/apidb',
   'password_literal': False,
   'db_env': {'POSTGRES_DB': 'apidb', 'POSTGRES_USER': 'api'},
   'restart': {'db': 'unless-stopped', 'web': 'unless-stopped'}}),
 ('S2',
  'web_db',
  {'project': 'lab04',
   'web_image': 'registry.local:5000/lab/web:latest-ci',
   'web_port': 8000,
   'web_health': ['CMD',
                  'python',
                  '-c',
                  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"],
   'db_image': 'postgres:16-alpine',
   'db_name': 'shopdb',
   'db_user': 'shop',
   'host_port': 18080},
  {'has_version': False,
   'name': 'lab04',
   'services': ['db', 'web'],
   'db_image': 'postgres:16-alpine',
   'db_health': ['CMD-SHELL', 'pg_isready -U shop -d shopdb'],
   'db_health_params': ['interval', 'retries', 'timeout'],
   'db_ports': [],
   'web_image': 'registry.local:5000/lab/web:latest-ci',
   'web_build': None,
   'web_ports': [('127.0.0.1', '18080', '8000')],
   'web_depends': {'db': 'service_healthy'},
   'web_health': ['CMD',
                  'python',
                  '-c',
                  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"],
   'database_url': 'postgresql://shop:${POSTGRES_PASSWORD}@db:5432/shopdb',
   'password_literal': False,
   'db_env': {'POSTGRES_DB': 'shopdb', 'POSTGRES_USER': 'shop'},
   'restart': {'db': 'unless-stopped', 'web': 'unless-stopped'}}),
 ('S3',
  'web_db',
  {'project': 'shop',
   'web_image': 'shop-web:1.0',
   'web_port': 8000,
   'web_health': ['CMD',
                  'python',
                  '-c',
                  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"],
   'db_image': 'postgres:16-alpine',
   'db_name': 'shopdb',
   'db_user': 'shop',
   'host_port': 8080,
   'build_context': './web'},
  {'has_version': False,
   'name': 'shop',
   'services': ['db', 'web'],
   'db_image': 'postgres:16-alpine',
   'db_health': ['CMD-SHELL', 'pg_isready -U shop -d shopdb'],
   'db_health_params': ['interval', 'retries', 'timeout'],
   'db_ports': [],
   'web_image': 'shop-web:1.0',
   'web_build': './web',
   'web_ports': [('127.0.0.1', '8080', '8000')],
   'web_depends': {'db': 'service_healthy'},
   'web_health': ['CMD',
                  'python',
                  '-c',
                  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"],
   'database_url': 'postgresql://shop:${POSTGRES_PASSWORD}@db:5432/shopdb',
   'password_literal': False,
   'db_env': {'POSTGRES_DB': 'shopdb', 'POSTGRES_USER': 'shop'},
   'restart': {'db': 'unless-stopped', 'web': 'unless-stopped'}}),
 ('S3',
  'web_db',
  {'project': 'mono',
   'web_image': 'mono-web:dev',
   'web_port': 8000,
   'web_health': ['CMD',
                  'python',
                  '-c',
                  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"],
   'db_image': 'postgres:16-alpine',
   'db_name': 'shopdb',
   'db_user': 'shop',
   'host_port': 8080,
   'build_context': '.'},
  {'has_version': False,
   'name': 'mono',
   'services': ['db', 'web'],
   'db_image': 'postgres:16-alpine',
   'db_health': ['CMD-SHELL', 'pg_isready -U shop -d shopdb'],
   'db_health_params': ['interval', 'retries', 'timeout'],
   'db_ports': [],
   'web_image': 'mono-web:dev',
   'web_build': '.',
   'web_ports': [('127.0.0.1', '8080', '8000')],
   'web_depends': {'db': 'service_healthy'},
   'web_health': ['CMD',
                  'python',
                  '-c',
                  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"],
   'database_url': 'postgresql://shop:${POSTGRES_PASSWORD}@db:5432/shopdb',
   'password_literal': False,
   'db_env': {'POSTGRES_DB': 'shopdb', 'POSTGRES_USER': 'shop'},
   'restart': {'db': 'unless-stopped', 'web': 'unless-stopped'}})]


@pytest.mark.parametrize("tag,drv,kwargs,expected", T05, ids=_ids(T05, "T05"))
def test_task_05(tag, drv, kwargs, expected):
    run(5, drv, kwargs, expected)
