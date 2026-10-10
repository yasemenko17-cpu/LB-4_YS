"""Відкриті тести задачі 2: Багатоетапна збірка.

Запуск: pytest tests/test_lab_02.py -k S2 (замініть S2 на свій набір).
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


T02 = [('S1',
  'multistage',
  {'builder_base': 'python:3.12-slim',
   'runtime_base': 'python:3.12-slim',
   'workdir': '/app',
   'build_steps': ['python -m venv /opt/venv', '/opt/venv/bin/pip install --no-cache-dir -r requirements.txt'],
   'copies': [('/opt/venv', '/opt/venv'), ('/app/app.py', '/app/app.py')],
   'port': 8000,
   'cmd': ['/opt/venv/bin/python', 'app.py']},
  {'stages': 2,
   'builder_base': 'python:3.12-slim',
   'builder_alias': 'builder',
   'final_base': 'python:3.12-slim',
   'builder_runs': ['python -m venv /opt/venv', '/opt/venv/bin/pip install --no-cache-dir -r requirements.txt'],
   'final_runs': [],
   'copies': [('/opt/venv', '/opt/venv'), ('/app/app.py', '/app/app.py')],
   'final_other_copies': 0,
   'workdir': ['/app'],
   'expose': [8000],
   'cmd': ['/opt/venv/bin/python', 'app.py']}),
 ('S1',
  'multistage',
  {'builder_base': 'python:3.13-alpine',
   'runtime_base': 'python:3.13-alpine',
   'workdir': '/srv',
   'build_steps': ['pip install --prefix=/install -r requirements.txt'],
   'copies': [('/install', '/usr/local'), ('/srv/app.py', '/srv/app.py')],
   'port': 5000,
   'cmd': ['python', 'app.py']},
  {'stages': 2,
   'builder_base': 'python:3.13-alpine',
   'builder_alias': 'builder',
   'final_base': 'python:3.13-alpine',
   'builder_runs': ['pip install --prefix=/install -r requirements.txt'],
   'final_runs': [],
   'copies': [('/install', '/usr/local'), ('/srv/app.py', '/srv/app.py')],
   'final_other_copies': 0,
   'workdir': ['/srv'],
   'expose': [5000],
   'cmd': ['python', 'app.py']}),
 ('S2',
  'multistage',
  {'builder_base': 'golang:1.21-alpine',
   'runtime_base': 'scratch',
   'workdir': '/src',
   'build_steps': ['CGO_ENABLED=0 go build -o /out/server main.go'],
   'copies': [('/out/server', '/server')],
   'port': 8082,
   'cmd': ['/server']},
  {'stages': 2,
   'builder_base': 'golang:1.21-alpine',
   'builder_alias': 'builder',
   'final_base': 'scratch',
   'builder_runs': ['CGO_ENABLED=0 go build -o /out/server main.go'],
   'final_runs': [],
   'copies': [('/out/server', '/server')],
   'final_other_copies': 0,
   'workdir': ['/src'],
   'expose': [8082],
   'cmd': ['/server']}),
 ('S2',
  'multistage',
  {'builder_base': 'golang:1.21-alpine',
   'runtime_base': 'alpine:3.20',
   'workdir': '/src',
   'build_steps': ['CGO_ENABLED=0 go build -o /out/server main.go'],
   'copies': [('/out/server', '/usr/local/bin/server')],
   'port': 8083,
   'cmd': ['/usr/local/bin/server']},
  {'stages': 2,
   'builder_base': 'golang:1.21-alpine',
   'builder_alias': 'builder',
   'final_base': 'alpine:3.20',
   'builder_runs': ['CGO_ENABLED=0 go build -o /out/server main.go'],
   'final_runs': [],
   'copies': [('/out/server', '/usr/local/bin/server')],
   'final_other_copies': 0,
   'workdir': ['/src'],
   'expose': [8083],
   'cmd': ['/usr/local/bin/server']}),
 ('S3',
  'multistage',
  {'builder_base': 'node:22-alpine',
   'runtime_base': 'nginx:1.27-alpine',
   'workdir': '/app',
   'build_steps': ['npm ci', 'npm run build'],
   'copies': [('/app/dist', '/usr/share/nginx/html')],
   'port': 80,
   'cmd': ['nginx', '-g', 'daemon off;']},
  {'stages': 2,
   'builder_base': 'node:22-alpine',
   'builder_alias': 'builder',
   'final_base': 'nginx:1.27-alpine',
   'builder_runs': ['npm ci', 'npm run build'],
   'final_runs': [],
   'copies': [('/app/dist', '/usr/share/nginx/html')],
   'final_other_copies': 0,
   'workdir': ['/app'],
   'expose': [80],
   'cmd': ['nginx', '-g', 'daemon off;']}),
 ('S3',
  'multistage',
  {'builder_base': 'python:3.12-slim',
   'runtime_base': 'python:3.12-slim',
   'workdir': '/app',
   'build_steps': [],
   'copies': [('/opt/venv', '/opt/venv'), ('/app/app.py', '/app/app.py')],
   'port': 8000,
   'cmd': ['/opt/venv/bin/python', 'app.py']},
  ('!ValueError', 'Потрібен принаймні один крок збірки'))]


@pytest.mark.parametrize("tag,drv,kwargs,expected", T02, ids=_ids(T02, "T02"))
def test_task_02(tag, drv, kwargs, expected):
    run(2, drv, kwargs, expected)
