"""Відкриті тести задачі 4: Файл .dockerignore.

Запуск: pytest tests/test_lab_04.py -k S2 (замініть S2 на свій набір).
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


T04 = [('S1',
  'ignore',
  {'stack': 'python',
   'keep': [],
   'extra': [],
   'files': ['app.py',
             'requirements.txt',
             'Dockerfile',
             'compose.yaml',
             '.dockerignore',
             '.env',
             '.env.local',
             '.env.example',
             'README.md',
             'docs/guide.md',
             'docs/README.md',
             '.git/config',
             '.github/workflows/ci.yml',
             '.vscode/settings.json',
             '.venv/bin/python',
             'app/__init__.py',
             'app/main.py',
             'app/__pycache__/main.cpython-312.pyc',
             'module.pyc',
             'tests/test_app.py',
             '.pytest_cache/README.md',
             'server.log',
             'logs/app.log',
             'static/index.html']},
  ['app.py', 'app/__init__.py', 'app/main.py', 'requirements.txt', 'static/index.html', 'tests/test_app.py']),
 ('S1',
  'ignore',
  {'stack': 'python',
   'keep': ['README.md'],
   'extra': [],
   'files': ['app.py',
             'requirements.txt',
             'Dockerfile',
             'compose.yaml',
             '.dockerignore',
             '.env',
             '.env.local',
             '.env.example',
             'README.md',
             'docs/guide.md',
             'docs/README.md',
             '.git/config',
             '.github/workflows/ci.yml',
             '.vscode/settings.json',
             '.venv/bin/python',
             'app/__init__.py',
             'app/main.py',
             'app/__pycache__/main.cpython-312.pyc',
             'module.pyc',
             'tests/test_app.py',
             '.pytest_cache/README.md',
             'server.log',
             'logs/app.log',
             'static/index.html']},
  ['README.md',
   'app.py',
   'app/__init__.py',
   'app/main.py',
   'requirements.txt',
   'static/index.html',
   'tests/test_app.py']),
 ('S2',
  'ignore',
  {'stack': 'node',
   'keep': [],
   'extra': [],
   'files': ['package.json',
             'package-lock.json',
             'src/index.js',
             'node_modules/express/index.js',
             'src/node_modules/x/y.js',
             'coverage/lcov.info',
             'npm-debug.log',
             '.env',
             '.env.production',
             '.env.example',
             'Dockerfile',
             'README.md',
             'public/index.html',
             '.git/HEAD',
             'test/a.test.js',
             'src/util.test.js']},
  ['package-lock.json', 'package.json', 'public/index.html', 'src/index.js', 'src/util.test.js', 'test/a.test.js']),
 ('S2',
  'ignore',
  {'stack': 'node',
   'keep': ['.env.example'],
   'extra': [],
   'files': ['package.json',
             'package-lock.json',
             'src/index.js',
             'node_modules/express/index.js',
             'src/node_modules/x/y.js',
             'coverage/lcov.info',
             'npm-debug.log',
             '.env',
             '.env.production',
             '.env.example',
             'Dockerfile',
             'README.md',
             'public/index.html',
             '.git/HEAD',
             'test/a.test.js',
             'src/util.test.js']},
  ['.env.example',
   'package-lock.json',
   'package.json',
   'public/index.html',
   'src/index.js',
   'src/util.test.js',
   'test/a.test.js']),
 ('S3',
  'ignore',
  {'stack': 'go',
   'keep': [],
   'extra': [],
   'files': ['main.go',
             'go.mod',
             'go.sum',
             'handler.go',
             'handler_test.go',
             'pkg/util/util_test.go',
             'pkg/util/util.go',
             'bin/server',
             'app.test',
             'pkg/x.test',
             'README.md',
             'docs/README.md',
             '.env',
             '.git/config',
             'Dockerfile',
             'scripts/run.sh']},
  ['go.mod', 'go.sum', 'handler.go', 'main.go', 'pkg/util/util.go', 'scripts/run.sh']),
 ('S3',
  'ignore',
  {'stack': 'go',
   'keep': ['docs/README.md'],
   'extra': ['scripts'],
   'files': ['main.go',
             'go.mod',
             'go.sum',
             'handler.go',
             'handler_test.go',
             'pkg/util/util_test.go',
             'pkg/util/util.go',
             'bin/server',
             'app.test',
             'pkg/x.test',
             'README.md',
             'docs/README.md',
             '.env',
             '.git/config',
             'Dockerfile',
             'scripts/run.sh']},
  ['docs/README.md', 'go.mod', 'go.sum', 'handler.go', 'main.go', 'pkg/util/util.go'])]


@pytest.mark.parametrize("tag,drv,kwargs,expected", T04, ids=_ids(T04, "T04"))
def test_task_04(tag, drv, kwargs, expected):
    run(4, drv, kwargs, expected)
