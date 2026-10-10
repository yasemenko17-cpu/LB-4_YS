# Стартовий проєкт APSIK-LAB04

1. Відкрийте проєкт у GitHub Codespaces (Code → Codespaces → Create codespace; у Codespaces уже є Docker) або локально: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt`. Для частини Б локально потрібні Docker і Git.
2. Визначте свою задачу й набір за номером варіанта: задача = `(номер - 1) // 3 + 1`, набір = `(номер - 1) % 3 + 1`. Реалізуйте функцію у файлі `variants/lab_NN.py` за карткою варіанта: вона повертає текст Dockerfile, compose.yaml, робочого процесу або .dockerignore.
3. Запускайте відкриті тести своєї задачі й свого набору: `pytest tests/test_lab_NN.py -k S2` (замініть `S2` на свій набір: `S1`, `S2` або `S3`).
4. Змінюйте лише свій файл у `variants/` (і за бажанням додавайте `tests/test_my.py`). Тести лише розбирають текст, Docker для задач не потрібен.
5. Частина Б: заповніть `part_b/project.json`, створіть у корені репозиторію `Dockerfile`, `.dockerignore`, `compose.yaml`, `.env.example` і `.github/workflows/publish.yml`; код застосунку лежить у `app/`. Перевірка: `python part_b/check_repo.py` (з прапорцем `--docker` також збирає образ). Відповіді запишіть у `part_b/ANSWERS.md`.
