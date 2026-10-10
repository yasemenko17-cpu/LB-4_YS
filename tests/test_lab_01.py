"""Відкриті тести задачі 1: Dockerfile з кешуванням шарів.

Запуск: pytest tests/test_lab_01.py -k S2 (замініть S2 на свій набір).
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


T01 = [('S1',
  'cached',
  {'base': 'python:3.12-slim',
   'workdir': '/app',
   'deps_files': ['requirements.txt'],
   'install_cmd': 'pip install --no-cache-dir -r requirements.txt',
   'port': 8000,
   'cmd': ['python', 'app.py']},
  {'base': 'python:3.12-slim',
   'stages': 1,
   'workdir': '/app',
   'env': {},
   'deps': ['requirements.txt'],
   'install': ['pip install --no-cache-dir -r requirements.txt'],
   'source_before_install': False,
   'source_after_install': True,
   'expose': [8000],
   'cmd': ['python', 'app.py']}),
 ('S1',
  'cached',
  {'base': 'python:3.13-alpine',
   'workdir': '/srv/api',
   'deps_files': ['requirements.txt'],
   'install_cmd': 'pip install -r requirements.txt',
   'port': 5000,
   'cmd': ['python', 'server.py']},
  {'base': 'python:3.13-alpine',
   'stages': 1,
   'workdir': '/srv/api',
   'env': {},
   'deps': ['requirements.txt'],
   'install': ['pip install -r requirements.txt'],
   'source_before_install': False,
   'source_after_install': True,
   'expose': [5000],
   'cmd': ['python', 'server.py']}),
 ('S2',
  'cached',
  {'base': 'node:22-alpine',
   'workdir': '/usr/src/app',
   'deps_files': ['package.json', 'package-lock.json'],
   'install_cmd': 'npm ci --omit=dev',
   'port': 3000,
   'cmd': ['node', 'src/index.js'],
   'env': {'NODE_ENV': 'production'}},
  {'base': 'node:22-alpine',
   'stages': 1,
   'workdir': '/usr/src/app',
   'env': {'NODE_ENV': 'production'},
   'deps': ['package-lock.json', 'package.json'],
   'install': ['npm ci --omit=dev'],
   'source_before_install': False,
   'source_after_install': True,
   'expose': [3000],
   'cmd': ['node', 'src/index.js']}),
 ('S2',
  'cached',
  {'base': 'node:20-slim',
   'workdir': '/opt/web',
   'deps_files': ['package.json', 'package-lock.json'],
   'install_cmd': 'npm ci',
   'port': 3000,
   'cmd': ['npm', 'start'],
   'env': {'NODE_ENV': 'production', 'PORT': '3000'}},
  {'base': 'node:20-slim',
   'stages': 1,
   'workdir': '/opt/web',
   'env': {'NODE_ENV': 'production', 'PORT': '3000'},
   'deps': ['package-lock.json', 'package.json'],
   'install': ['npm ci'],
   'source_before_install': False,
   'source_after_install': True,
   'expose': [3000],
   'cmd': ['npm', 'start']}),
 ('S3',
  'cached',
  {'base': 'python',
   'workdir': '/app',
   'deps_files': ['requirements.txt'],
   'install_cmd': 'pip install -r requirements.txt',
   'port': 8000,
   'cmd': ['python', 'app.py']},
  ('!ValueError', 'Базовий образ має мати явний тег: python')),
 ('S3',
  'cached',
  {'base': 'python:latest',
   'workdir': '/app',
   'deps_files': ['requirements.txt'],
   'install_cmd': 'pip install -r requirements.txt',
   'port': 8000,
   'cmd': ['python', 'app.py']},
  ('!ValueError', 'Тег latest заборонений: python:latest'))]


@pytest.mark.parametrize("tag,drv,kwargs,expected", T01, ids=_ids(T01, "T01"))
def test_task_01(tag, drv, kwargs, expected):
    run(1, drv, kwargs, expected)
