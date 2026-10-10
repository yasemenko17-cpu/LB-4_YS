"""Лабораторна APSIK-LAB04. Задача 9: Робочий процес перевірки коду в GitHub Actions.

Правила — у student.md (розділ 7, задача 9) та в картці вашого варіанта.
Відкриті тести: pytest tests/test_lab_09.py
"""


def workflow_ci(name, branches, python_versions, install_cmd, test_cmd, paths=None, cron=None):
    """Повертає текст .github/workflows/ci.yml."""
    raise NotImplementedError  # TODO: реалізуйте за описом задачі
