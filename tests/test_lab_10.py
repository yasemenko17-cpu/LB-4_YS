"""Відкриті тести задачі 10: Збірка й публікація образу в GHCR із мінімальними правами.

Запуск: pytest tests/test_lab_10.py -k S2 (замініть S2 на свій набір).
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


T10 = [('S1',
  'publish',
  {'image': 'ghcr.io/lab/app', 'branches': ['main'], 'release_tags': False},
  {'events': ['pull_request', 'push'],
   'push_branches': ['main'],
   'push_tags': None,
   'pr_branches': ['main'],
   'pull_request_target': False,
   'top_permissions': {'contents': 'read'},
   'jobs': ['publish'],
   'needs': None,
   'publish_permissions': {'contents': 'read', 'packages': 'write'},
   'test_permissions': None,
   'login': {'registry': 'ghcr.io',
             'username': '${{ github.actor }}',
             'password': '${{ secrets.GITHUB_TOKEN }}',
             'if': "github.event_name != 'pull_request'"},
   'meta_images': 'ghcr.io/lab/app',
   'meta_tags': ['type=ref,event=branch', 'type=sha', 'type=raw,value=latest,enable={{is_default_branch}}'],
   'build': {'context': '.',
             'push': "github.event_name != 'pull_request'",
             'tags': '${{ steps.meta.outputs.tags }}',
             'cache-from': 'type=gha',
             'cache-to': 'type=gha,mode=max'},
   'secrets': ['GITHUB_TOKEN'],
   'secrets_in_run': False,
   'all_pinned': True,
   'write_all': False,
   'deploy_step_env': []}),
 ('S1',
  'publish',
  {'image': 'ghcr.io/student/shop-web', 'branches': ['main', 'dev'], 'release_tags': False},
  {'events': ['pull_request', 'push'],
   'push_branches': ['main', 'dev'],
   'push_tags': None,
   'pr_branches': ['main', 'dev'],
   'pull_request_target': False,
   'top_permissions': {'contents': 'read'},
   'jobs': ['publish'],
   'needs': None,
   'publish_permissions': {'contents': 'read', 'packages': 'write'},
   'test_permissions': None,
   'login': {'registry': 'ghcr.io',
             'username': '${{ github.actor }}',
             'password': '${{ secrets.GITHUB_TOKEN }}',
             'if': "github.event_name != 'pull_request'"},
   'meta_images': 'ghcr.io/student/shop-web',
   'meta_tags': ['type=ref,event=branch', 'type=sha', 'type=raw,value=latest,enable={{is_default_branch}}'],
   'build': {'context': '.',
             'push': "github.event_name != 'pull_request'",
             'tags': '${{ steps.meta.outputs.tags }}',
             'cache-from': 'type=gha',
             'cache-to': 'type=gha,mode=max'},
   'secrets': ['GITHUB_TOKEN'],
   'secrets_in_run': False,
   'all_pinned': True,
   'write_all': False,
   'deploy_step_env': []}),
 ('S2',
  'publish',
  {'image': 'ghcr.io/lab/app', 'branches': ['main'], 'release_tags': True},
  {'events': ['pull_request', 'push'],
   'push_branches': ['main'],
   'push_tags': ['v*.*.*'],
   'pr_branches': ['main'],
   'pull_request_target': False,
   'top_permissions': {'contents': 'read'},
   'jobs': ['publish'],
   'needs': None,
   'publish_permissions': {'contents': 'read', 'packages': 'write'},
   'test_permissions': None,
   'login': {'registry': 'ghcr.io',
             'username': '${{ github.actor }}',
             'password': '${{ secrets.GITHUB_TOKEN }}',
             'if': "github.event_name != 'pull_request'"},
   'meta_images': 'ghcr.io/lab/app',
   'meta_tags': ['type=ref,event=branch',
                 'type=sha',
                 'type=semver,pattern={{version}}',
                 'type=semver,pattern={{major}}.{{minor}}',
                 'type=raw,value=latest,enable={{is_default_branch}}'],
   'build': {'context': '.',
             'push': "github.event_name != 'pull_request'",
             'tags': '${{ steps.meta.outputs.tags }}',
             'cache-from': 'type=gha',
             'cache-to': 'type=gha,mode=max'},
   'secrets': ['GITHUB_TOKEN'],
   'secrets_in_run': False,
   'all_pinned': True,
   'write_all': False,
   'deploy_step_env': []}),
 ('S2',
  'publish',
  {'image': 'ghcr.io/student/shop-web', 'branches': ['main', 'dev'], 'release_tags': True},
  {'events': ['pull_request', 'push'],
   'push_branches': ['main', 'dev'],
   'push_tags': ['v*.*.*'],
   'pr_branches': ['main', 'dev'],
   'pull_request_target': False,
   'top_permissions': {'contents': 'read'},
   'jobs': ['publish'],
   'needs': None,
   'publish_permissions': {'contents': 'read', 'packages': 'write'},
   'test_permissions': None,
   'login': {'registry': 'ghcr.io',
             'username': '${{ github.actor }}',
             'password': '${{ secrets.GITHUB_TOKEN }}',
             'if': "github.event_name != 'pull_request'"},
   'meta_images': 'ghcr.io/student/shop-web',
   'meta_tags': ['type=ref,event=branch',
                 'type=sha',
                 'type=semver,pattern={{version}}',
                 'type=semver,pattern={{major}}.{{minor}}',
                 'type=raw,value=latest,enable={{is_default_branch}}'],
   'build': {'context': '.',
             'push': "github.event_name != 'pull_request'",
             'tags': '${{ steps.meta.outputs.tags }}',
             'cache-from': 'type=gha',
             'cache-to': 'type=gha,mode=max'},
   'secrets': ['GITHUB_TOKEN'],
   'secrets_in_run': False,
   'all_pinned': True,
   'write_all': False,
   'deploy_step_env': []}),
 ('S3',
  'publish',
  {'image': 'ghcr.io/lab/app', 'branches': ['main'], 'release_tags': False, 'test_cmd': 'pytest -q'},
  {'events': ['pull_request', 'push'],
   'push_branches': ['main'],
   'push_tags': None,
   'pr_branches': ['main'],
   'pull_request_target': False,
   'top_permissions': {'contents': 'read'},
   'jobs': ['publish', 'test'],
   'needs': 'test',
   'publish_permissions': {'contents': 'read', 'packages': 'write'},
   'test_permissions': None,
   'login': {'registry': 'ghcr.io',
             'username': '${{ github.actor }}',
             'password': '${{ secrets.GITHUB_TOKEN }}',
             'if': "github.event_name != 'pull_request'"},
   'meta_images': 'ghcr.io/lab/app',
   'meta_tags': ['type=ref,event=branch', 'type=sha', 'type=raw,value=latest,enable={{is_default_branch}}'],
   'build': {'context': '.',
             'push': "github.event_name != 'pull_request'",
             'tags': '${{ steps.meta.outputs.tags }}',
             'cache-from': 'type=gha',
             'cache-to': 'type=gha,mode=max'},
   'secrets': ['GITHUB_TOKEN'],
   'secrets_in_run': False,
   'all_pinned': True,
   'write_all': False,
   'deploy_step_env': []}),
 ('S3',
  'publish',
  {'image': 'ghcr.io/lab/app',
   'branches': ['main'],
   'release_tags': False,
   'test_cmd': 'pytest app',
   'deploy_secret': 'DEPLOY_HOOK'},
  {'events': ['pull_request', 'push'],
   'push_branches': ['main'],
   'push_tags': None,
   'pr_branches': ['main'],
   'pull_request_target': False,
   'top_permissions': {'contents': 'read'},
   'jobs': ['publish', 'test'],
   'needs': 'test',
   'publish_permissions': {'contents': 'read', 'packages': 'write'},
   'test_permissions': None,
   'login': {'registry': 'ghcr.io',
             'username': '${{ github.actor }}',
             'password': '${{ secrets.GITHUB_TOKEN }}',
             'if': "github.event_name != 'pull_request'"},
   'meta_images': 'ghcr.io/lab/app',
   'meta_tags': ['type=ref,event=branch', 'type=sha', 'type=raw,value=latest,enable={{is_default_branch}}'],
   'build': {'context': '.',
             'push': "github.event_name != 'pull_request'",
             'tags': '${{ steps.meta.outputs.tags }}',
             'cache-from': 'type=gha',
             'cache-to': 'type=gha,mode=max'},
   'secrets': ['DEPLOY_HOOK', 'GITHUB_TOKEN'],
   'secrets_in_run': False,
   'all_pinned': True,
   'write_all': False,
   'deploy_step_env': [{'HOOK': '${{ secrets.DEPLOY_HOOK }}'}]})]


@pytest.mark.parametrize("tag,drv,kwargs,expected", T10, ids=_ids(T10, "T10"))
def test_task_10(tag, drv, kwargs, expected):
    run(10, drv, kwargs, expected)
