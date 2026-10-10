"""Лабораторна APSIK-LAB04. Задача 2: Багатоетапна збірка.

Правила — у student.md (розділ 7, задача 2) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_02.py
"""


def dockerfile_multistage(builder_base, runtime_base, workdir, build_steps, copies, port, cmd):
    """Повертає текст Dockerfile з етапом збірки builder і мінімальним кінцевим етапом."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
