"""Лабораторна APSIK-LAB04. Задача 5: Стек web + PostgreSQL: healthcheck і depends_on.

Правила — у student.md (розділ 7, задача 5) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_05.py
"""


def compose_web_db(project, web_image, web_port, web_health, db_image, db_name, db_user, host_port, build_context=None):
    """Повертає текст compose.yaml зі службами db і web."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
