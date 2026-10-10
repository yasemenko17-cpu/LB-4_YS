"""Лабораторна APSIK-LAB04. Задача 10: Збірка й публікація образу в GHCR із мінімальними правами.

Правила — у student.md (розділ 7, задача 10) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_10.py
"""


def workflow_publish(image, branches, release_tags, test_cmd=None, deploy_secret=None):
    """Повертає текст .github/workflows/publish.yml."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
