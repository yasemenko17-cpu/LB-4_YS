"""Відкриті тести задачі 8: Змінні середовища, .env і профілі Compose.

Запуск: pytest tests/test_lab_08.py -k S2 (замініть S2 на свій набір).
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


T08 = [('S1',
  'profiles',
  {'project': 'shop',
   'db_image': 'postgres:16-alpine',
   'web_image': 'shop-web:1.0',
   'tools': [{'name': 'adminer', 'image': 'adminer:4', 'profile': 'debug', 'port': 8080}],
   'defaults': {'LOG_LEVEL': 'info'},
   'required': []},
  {'has_version': False,
   'services': ['adminer', 'db', 'web'],
   'profiles': {'adminer': ['debug'], 'db': [], 'web': []},
   'web_env': {'LOG_LEVEL': '${LOG_LEVEL:-info}'},
   'db_password': '${POSTGRES_PASSWORD:?Задайте POSTGRES_PASSWORD}',
   'tool_ports': {'adminer': [('127.0.0.1', '8080', '8080')]},
   'tool_depends': {'adminer': {'db': 'service_healthy'}},
   'tool_restart': {'adminer': None},
   'tool_command': {'adminer': None}}),
 ('S1',
  'profiles',
  {'project': 'blog',
   'db_image': 'postgres:16-alpine',
   'web_image': 'shop-web:1.0',
   'tools': [{'name': 'pgadmin', 'image': 'dpage/pgadmin4:8', 'profile': 'admin', 'port': 5050}],
   'defaults': {'LOG_LEVEL': 'info', 'WORKERS': '2'},
   'required': []},
  {'has_version': False,
   'services': ['db', 'pgadmin', 'web'],
   'profiles': {'db': [], 'pgadmin': ['admin'], 'web': []},
   'web_env': {'LOG_LEVEL': '${LOG_LEVEL:-info}', 'WORKERS': '${WORKERS:-2}'},
   'db_password': '${POSTGRES_PASSWORD:?Задайте POSTGRES_PASSWORD}',
   'tool_ports': {'pgadmin': [('127.0.0.1', '5050', '5050')]},
   'tool_depends': {'pgadmin': {'db': 'service_healthy'}},
   'tool_restart': {'pgadmin': None},
   'tool_command': {'pgadmin': None}}),
 ('S2',
  'profiles',
  {'project': 'shop',
   'db_image': 'postgres:16-alpine',
   'web_image': 'shop-web:1.0',
   'tools': [{'name': 'tests',
              'image': 'shop-web:1.0',
              'profile': 'test',
              'once': True,
              'command': ['pytest', '-q']}],
   'defaults': {'LOG_LEVEL': 'info'},
   'required': []},
  {'has_version': False,
   'services': ['db', 'tests', 'web'],
   'profiles': {'db': [], 'tests': ['test'], 'web': []},
   'web_env': {'LOG_LEVEL': '${LOG_LEVEL:-info}'},
   'db_password': '${POSTGRES_PASSWORD:?Задайте POSTGRES_PASSWORD}',
   'tool_ports': {'tests': []},
   'tool_depends': {'tests': {'db': 'service_healthy'}},
   'tool_restart': {'tests': 'no'},
   'tool_command': {'tests': ['pytest', '-q']}}),
 ('S2',
  'profiles',
  {'project': 'shop',
   'db_image': 'postgres:16-alpine',
   'web_image': 'shop-web:1.0',
   'tools': [{'name': 'tests', 'image': 'shop-web:1.0', 'profile': 'test', 'once': True, 'command': ['pytest', '-q']},
             {'name': 'adminer', 'image': 'adminer:4', 'profile': 'debug', 'port': 8080}],
   'defaults': {'LOG_LEVEL': 'info'},
   'required': ['SECRET_KEY']},
  {'has_version': False,
   'services': ['adminer', 'db', 'tests', 'web'],
   'profiles': {'adminer': ['debug'], 'db': [], 'tests': ['test'], 'web': []},
   'web_env': {'SECRET_KEY': '${SECRET_KEY:?Задайте SECRET_KEY}', 'LOG_LEVEL': '${LOG_LEVEL:-info}'},
   'db_password': '${POSTGRES_PASSWORD:?Задайте POSTGRES_PASSWORD}',
   'tool_ports': {'adminer': [('127.0.0.1', '8080', '8080')], 'tests': []},
   'tool_depends': {'adminer': {'db': 'service_healthy'}, 'tests': {'db': 'service_healthy'}},
   'tool_restart': {'adminer': None, 'tests': 'no'},
   'tool_command': {'adminer': None, 'tests': ['pytest', '-q']}}),
 ('S3',
  'envfile',
  {'defaults': {'LOG_LEVEL': 'info', 'WORKERS': '2'}, 'required': ['SECRET_KEY', 'API_URL']},
  {'pairs': [('SECRET_KEY', ''), ('API_URL', ''), ('LOG_LEVEL', 'info'), ('WORKERS', '2')],
   'has_comment': True,
   'ends_with_newline': True}),
 ('S3', 'envfile', {'defaults': {}, 'required': []}, {'pairs': [], 'has_comment': True, 'ends_with_newline': True})]


@pytest.mark.parametrize("tag,drv,kwargs,expected", T08, ids=_ids(T08, "T08"))
def test_task_08(tag, drv, kwargs, expected):
    run(8, drv, kwargs, expected)
