"""Відкриті тести задачі 3: Безпечний образ: користувач без прав root і HEALTHCHECK.

Запуск: pytest tests/test_lab_03.py -k S2 (замініть S2 на свій набір).
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


T03 = [('S1',
  'hardened',
  {'base': 'python:3.12-slim',
   'distro': 'debian',
   'user': 'app',
   'uid': 10001,
   'workdir': '/app',
   'deps_files': ['requirements.txt'],
   'install_cmd': 'pip install --no-cache-dir -r requirements.txt',
   'port': 8000,
   'cmd': ['python', 'app.py'],
   'healthcheck': {'cmd': ['python',
                           '-c',
                           "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]}},
  {'base': 'python:3.12-slim',
   'deps': ['requirements.txt'],
   'install': ['pip install --no-cache-dir -r requirements.txt'],
   'user': '10001:10001',
   'nonroot': True,
   'runs_after_user': 0,
   'user_before_cmd': True,
   'user_created': True,
   'chown': True,
   'health': {'interval': '30s',
              'timeout': '3s',
              'start_period': '5s',
              'retries': 3,
              'cmd': ['python',
                      '-c',
                      "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]},
   'secrets': [],
   'env': {},
   'expose': [8000],
   'cmd': ['python', 'app.py']}),
 ('S1',
  'hardened',
  {'base': 'python:3.12-slim',
   'distro': 'debian',
   'user': 'svc',
   'uid': 20000,
   'workdir': '/app',
   'deps_files': ['requirements.txt'],
   'install_cmd': 'pip install --no-cache-dir -r requirements.txt',
   'port': 8000,
   'cmd': ['python', 'app.py'],
   'healthcheck': {'cmd': ['python',
                           '-c',
                           "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"],
                   'interval': '10s',
                   'timeout': '2s',
                   'start_period': '15s',
                   'retries': 5},
   'env': {'APP_ENV': 'prod'}},
  {'base': 'python:3.12-slim',
   'deps': ['requirements.txt'],
   'install': ['pip install --no-cache-dir -r requirements.txt'],
   'user': '20000:20000',
   'nonroot': True,
   'runs_after_user': 0,
   'user_before_cmd': True,
   'user_created': True,
   'chown': True,
   'health': {'interval': '10s',
              'timeout': '2s',
              'start_period': '15s',
              'retries': 5,
              'cmd': ['python',
                      '-c',
                      "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]},
   'secrets': [],
   'env': {'APP_ENV': 'prod'},
   'expose': [8000],
   'cmd': ['python', 'app.py']}),
 ('S2',
  'hardened',
  {'base': 'python:3.13-alpine',
   'distro': 'alpine',
   'user': 'app',
   'uid': 10001,
   'workdir': '/app',
   'deps_files': ['requirements.txt'],
   'install_cmd': 'pip install --no-cache-dir -r requirements.txt',
   'port': 8000,
   'cmd': ['python', 'app.py'],
   'healthcheck': {'cmd': ['wget', '-q', '-O', '/dev/null', 'http://127.0.0.1:8000/health']}},
  {'base': 'python:3.13-alpine',
   'deps': ['requirements.txt'],
   'install': ['pip install --no-cache-dir -r requirements.txt'],
   'user': '10001:10001',
   'nonroot': True,
   'runs_after_user': 0,
   'user_before_cmd': True,
   'user_created': True,
   'chown': True,
   'health': {'interval': '30s',
              'timeout': '3s',
              'start_period': '5s',
              'retries': 3,
              'cmd': ['wget', '-q', '-O', '/dev/null', 'http://127.0.0.1:8000/health']},
   'secrets': [],
   'env': {},
   'expose': [8000],
   'cmd': ['python', 'app.py']}),
 ('S2',
  'hardened',
  {'base': 'node:22-alpine',
   'distro': 'alpine',
   'user': 'nodeapp',
   'uid': 10010,
   'workdir': '/usr/src/app',
   'deps_files': ['package.json', 'package-lock.json'],
   'install_cmd': 'npm ci --omit=dev',
   'port': 3000,
   'cmd': ['node', 'src/index.js'],
   'healthcheck': {'cmd': ['wget', '-q', '-O', '/dev/null', 'http://127.0.0.1:3000/health'],
                   'interval': '15s',
                   'retries': 4},
   'env': {'NODE_ENV': 'production', 'LOG_LEVEL': 'info'}},
  {'base': 'node:22-alpine',
   'deps': ['package-lock.json', 'package.json'],
   'install': ['npm ci --omit=dev'],
   'user': '10010:10010',
   'nonroot': True,
   'runs_after_user': 0,
   'user_before_cmd': True,
   'user_created': True,
   'chown': True,
   'health': {'interval': '15s',
              'timeout': '3s',
              'start_period': '5s',
              'retries': 4,
              'cmd': ['wget', '-q', '-O', '/dev/null', 'http://127.0.0.1:3000/health']},
   'secrets': [],
   'env': {'NODE_ENV': 'production', 'LOG_LEVEL': 'info'},
   'expose': [3000],
   'cmd': ['node', 'src/index.js']}),
 ('S3',
  'hardened',
  {'base': 'python:3.12-slim',
   'distro': 'debian',
   'user': 'app',
   'uid': 0,
   'workdir': '/app',
   'deps_files': ['requirements.txt'],
   'install_cmd': 'pip install --no-cache-dir -r requirements.txt',
   'port': 8000,
   'cmd': ['python', 'app.py'],
   'healthcheck': {'cmd': ['python',
                           '-c',
                           "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]}},
  ('!ValueError', 'Користувач не має бути root')),
 ('S3',
  'hardened',
  {'base': 'python:3.12-slim',
   'distro': 'debian',
   'user': 'root',
   'uid': 1000,
   'workdir': '/app',
   'deps_files': ['requirements.txt'],
   'install_cmd': 'pip install --no-cache-dir -r requirements.txt',
   'port': 8000,
   'cmd': ['python', 'app.py'],
   'healthcheck': {'cmd': ['python',
                           '-c',
                           "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]}},
  ('!ValueError', 'Користувач не має бути root'))]


@pytest.mark.parametrize("tag,drv,kwargs,expected", T03, ids=_ids(T03, "T03"))
def test_task_03(tag, drv, kwargs, expected):
    run(3, drv, kwargs, expected)
