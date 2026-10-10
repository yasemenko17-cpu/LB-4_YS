"""Лабораторна APSIK-LAB04. Задача 6: Томи для даних PostgreSQL.

Правила — у student.md (розділ 7, задача 6) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_06.py
"""


def compose_volumes(project, db_image, db_name, db_user, data_volume, init_dir, backup_dir, external=False, volume_name=None):
    """Повертає текст compose.yaml зі службою db і томами."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
