"""Відкриті тести задачі 9: Робочий процес перевірки коду в GitHub Actions.

Запуск: pytest tests/test_lab_09.py -k S2 (замініть S2 на свій набір).
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


T09 = [('S1',
  'ci',
  {'name': 'CI',
   'branches': ['main'],
   'python_versions': ['3.12'],
   'install_cmd': 'pip install -r requirements.txt',
   'test_cmd': 'pytest -q'},
  {'name': 'CI',
   'events': ['pull_request', 'push', 'workflow_dispatch'],
   'push_branches': ['main'],
   'pr_branches': ['main'],
   'push_paths': None,
   'pr_paths': None,
   'cron': [],
   'concurrency': {'group': '${{ github.workflow }}-${{ github.ref }}', 'cancel-in-progress': True},
   'permissions': {'contents': 'read'},
   'jobs': ['test'],
   'runs_on': 'ubuntu-latest',
   'timeout': 15,
   'matrix': None,
   'fail_fast': None,
   'setup_version': '3.12',
   'cache': 'pip',
   'uses': ['actions/checkout@v7', 'actions/setup-python@v7'],
   'all_pinned': True,
   'runs': ['pip install -r requirements.txt', 'pytest -q'],
   'first_step_checkout': True}),
 ('S1',
  'ci',
  {'name': 'Перевірка',
   'branches': ['main', 'develop'],
   'python_versions': ['3.13'],
   'install_cmd': 'pip install -r app/requirements.txt pytest',
   'test_cmd': 'pytest app'},
  {'name': 'Перевірка',
   'events': ['pull_request', 'push', 'workflow_dispatch'],
   'push_branches': ['main', 'develop'],
   'pr_branches': ['main', 'develop'],
   'push_paths': None,
   'pr_paths': None,
   'cron': [],
   'concurrency': {'group': '${{ github.workflow }}-${{ github.ref }}', 'cancel-in-progress': True},
   'permissions': {'contents': 'read'},
   'jobs': ['test'],
   'runs_on': 'ubuntu-latest',
   'timeout': 15,
   'matrix': None,
   'fail_fast': None,
   'setup_version': '3.13',
   'cache': 'pip',
   'uses': ['actions/checkout@v7', 'actions/setup-python@v7'],
   'all_pinned': True,
   'runs': ['pip install -r app/requirements.txt pytest', 'pytest app'],
   'first_step_checkout': True}),
 ('S2',
  'ci',
  {'name': 'CI',
   'branches': ['main'],
   'python_versions': ['3.10', '3.11', '3.12'],
   'install_cmd': 'pip install -r requirements.txt',
   'test_cmd': 'pytest -q'},
  {'name': 'CI',
   'events': ['pull_request', 'push', 'workflow_dispatch'],
   'push_branches': ['main'],
   'pr_branches': ['main'],
   'push_paths': None,
   'pr_paths': None,
   'cron': [],
   'concurrency': {'group': '${{ github.workflow }}-${{ github.ref }}', 'cancel-in-progress': True},
   'permissions': {'contents': 'read'},
   'jobs': ['test'],
   'runs_on': 'ubuntu-latest',
   'timeout': 15,
   'matrix': ['3.10', '3.11', '3.12'],
   'fail_fast': False,
   'setup_version': '${{ matrix.python-version }}',
   'cache': 'pip',
   'uses': ['actions/checkout@v7', 'actions/setup-python@v7'],
   'all_pinned': True,
   'runs': ['pip install -r requirements.txt', 'pytest -q'],
   'first_step_checkout': True}),
 ('S2',
  'ci',
  {'name': 'Matrix',
   'branches': ['main'],
   'python_versions': ['3.12', '3.13'],
   'install_cmd': 'pip install -r requirements.txt',
   'test_cmd': 'pytest -q --maxfail=1'},
  {'name': 'Matrix',
   'events': ['pull_request', 'push', 'workflow_dispatch'],
   'push_branches': ['main'],
   'pr_branches': ['main'],
   'push_paths': None,
   'pr_paths': None,
   'cron': [],
   'concurrency': {'group': '${{ github.workflow }}-${{ github.ref }}', 'cancel-in-progress': True},
   'permissions': {'contents': 'read'},
   'jobs': ['test'],
   'runs_on': 'ubuntu-latest',
   'timeout': 15,
   'matrix': ['3.12', '3.13'],
   'fail_fast': False,
   'setup_version': '${{ matrix.python-version }}',
   'cache': 'pip',
   'uses': ['actions/checkout@v7', 'actions/setup-python@v7'],
   'all_pinned': True,
   'runs': ['pip install -r requirements.txt', 'pytest -q --maxfail=1'],
   'first_step_checkout': True}),
 ('S3',
  'ci',
  {'name': 'CI',
   'branches': ['main'],
   'python_versions': ['3.12'],
   'install_cmd': 'pip install -r requirements.txt',
   'test_cmd': 'pytest -q',
   'paths': ['app/**', 'requirements.txt']},
  {'name': 'CI',
   'events': ['pull_request', 'push', 'workflow_dispatch'],
   'push_branches': ['main'],
   'pr_branches': ['main'],
   'push_paths': ['app/**', 'requirements.txt'],
   'pr_paths': ['app/**', 'requirements.txt'],
   'cron': [],
   'concurrency': {'group': '${{ github.workflow }}-${{ github.ref }}', 'cancel-in-progress': True},
   'permissions': {'contents': 'read'},
   'jobs': ['test'],
   'runs_on': 'ubuntu-latest',
   'timeout': 15,
   'matrix': None,
   'fail_fast': None,
   'setup_version': '3.12',
   'cache': 'pip',
   'uses': ['actions/checkout@v7', 'actions/setup-python@v7'],
   'all_pinned': True,
   'runs': ['pip install -r requirements.txt', 'pytest -q'],
   'first_step_checkout': True}),
 ('S3',
  'ci',
  {'name': 'CI',
   'branches': ['main'],
   'python_versions': ['3.12'],
   'install_cmd': 'pip install -r requirements.txt',
   'test_cmd': 'pytest -q',
   'cron': '0 3 * * 1'},
  {'name': 'CI',
   'events': ['pull_request', 'push', 'schedule', 'workflow_dispatch'],
   'push_branches': ['main'],
   'pr_branches': ['main'],
   'push_paths': None,
   'pr_paths': None,
   'cron': ['0 3 * * 1'],
   'concurrency': {'group': '${{ github.workflow }}-${{ github.ref }}', 'cancel-in-progress': True},
   'permissions': {'contents': 'read'},
   'jobs': ['test'],
   'runs_on': 'ubuntu-latest',
   'timeout': 15,
   'matrix': None,
   'fail_fast': None,
   'setup_version': '3.12',
   'cache': 'pip',
   'uses': ['actions/checkout@v7', 'actions/setup-python@v7'],
   'all_pinned': True,
   'runs': ['pip install -r requirements.txt', 'pytest -q'],
   'first_step_checkout': True})]


@pytest.mark.parametrize("tag,drv,kwargs,expected", T09, ids=_ids(T09, "T09"))
def test_task_09(tag, drv, kwargs, expected):
    run(9, drv, kwargs, expected)
