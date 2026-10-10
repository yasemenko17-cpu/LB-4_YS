"""Лабораторна APSIK-LAB04. Задача 3: Безпечний образ: користувач без прав root і HEALTHCHECK.

Правила — у student.md (розділ 7, задача 3) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_03.py
"""


def dockerfile_hardened(base, distro, user, uid, workdir, deps_files, install_cmd, port, cmd, healthcheck, env=None):
    """Повертає текст Dockerfile, у якому застосунок працює без прав root і має HEALTHCHECK."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
