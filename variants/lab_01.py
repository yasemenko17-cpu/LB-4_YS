"""Лабораторна APSIK-LAB04. Задача 1: Dockerfile з кешуванням шарів.

Правила — у student.md (розділ 7, задача 1) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_01.py
"""


def dockerfile_cached(base, workdir, deps_files, install_cmd, port, cmd, env=None):
    """Повертає текст Dockerfile: залежності встановлюються до копіювання вихідного коду."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
