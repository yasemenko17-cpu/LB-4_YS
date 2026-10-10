"""Перевірка частини Б за файлами репозиторію (без звернень до GitHub).

Використання:  python part_b/check_repo.py [тека_репозиторію] [--docker]
За замовчуванням перевіряється тека, що містить part_b/. З прапорцем --docker додатково виконуються
`docker compose config` і `docker build` (потрібен Docker). Параметри проєкту беруться з part_b/project.json.
Скрипт читає лише файли: про публікацію образу в GHCR свідчить вивід `docker pull` у ANSWERS.md.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tests"))
from stacklib import (action_pinned, context_files, copy_parts, image_is_pinned, job_steps, json_args,  # noqa: E402
                      load_yaml, norm_depends, norm_env, norm_mounts, norm_networks, norm_ports, parse_dockerfile,
                      parse_from, parse_healthcheck, stages, wf_on)

SECRET = re.compile(r"PASSWORD|PASSWD|SECRET|TOKEN|API_?KEY|PRIVATE_?KEY", re.I)
SAMPLE = [".git/config", ".env", ".env.local", "app/app.py", "app/requirements.txt", "app/__pycache__/app.cpython-312.pyc",
          ".venv/bin/python", "README.md", "compose.yaml"]
MUST_KEEP = ["app/app.py", "app/requirements.txt"]
MUST_DROP = [".git/config", ".env", ".env.local", "app/__pycache__/app.cpython-312.pyc", ".venv/bin/python"]


def _read(repo, rel):
    path = repo / rel
    return path.read_text(encoding="utf-8") if path.is_file() else None


def check_dockerfile(repo, prj):
    text = _read(repo, "Dockerfile")
    if text is None:
        return ["Dockerfile: файла немає"]
    problems = []
    ins = parse_dockerfile(text)
    groups = stages(ins)
    froms = [i for i in ins if i.name == "FROM"]
    if len(groups) < 2:
        return ["Dockerfile: потрібна багатоетапна збірка (щонайменше два FROM)"]
    aliases = set()
    for f in froms:
        image, alias = parse_from(f.args)
        if image not in aliases and not image_is_pinned(image):
            problems.append(f"Dockerfile: базовий образ без явного тега або з latest: {image}")
        if alias:
            aliases.add(alias)
    final = groups[-1]
    users = [i for i in final if i.name == "USER"]
    if not users or users[-1].args.split(":")[0] in ("root", "0"):
        problems.append("Dockerfile: кінцевий етап має працювати від користувача без прав root (інструкція USER)")
    elif not re.match(r"\d+", users[-1].args):
        problems.append("Dockerfile: вкажіть числовий ідентифікатор користувача в USER (наприклад, USER 10001:10001)")
    if not any(i.name == "HEALTHCHECK" for i in final) or not any(
            i.name == "HEALTHCHECK" and parse_healthcheck(i.args)["cmd"] for i in final):
        problems.append("Dockerfile: потрібен HEALTHCHECK у формі CMD [\"...\"] у кінцевому етапі")
    if not any(i.name == "COPY" and copy_parts(i)[0].get("from") for i in final):
        problems.append("Dockerfile: кінцевий етап має копіювати результат збірки через COPY --from=")
    if any(i.name == "RUN" and re.search(r"pip install|npm ci|apt-get", i.args) for i in final):
        problems.append("Dockerfile: інструменти збірки (pip, npm, apt-get) не повинні потрапляти в кінцевий етап")
    if not any(i.name == "EXPOSE" and int(i.args.split("/")[0]) == prj["web_port"] for i in ins):
        problems.append(f"Dockerfile: потрібен EXPOSE {prj['web_port']}")
    cmds = [i for i in final if i.name == "CMD"]
    if not cmds or json_args(cmds[-1].args) is None:
        problems.append("Dockerfile: CMD має бути у формі exec (JSON-масив)")
    if any(i.name in ("ENV", "ARG") and SECRET.search(p.partition("=")[0]) for i in ins for p in i.args.split()):
        problems.append("Dockerfile: секрети не можна записувати в ENV чи ARG")
    # кешування: інсталяція залежностей у першому етапі стоїть після копіювання лише файла залежностей і до копіювання коду
    build = groups[0]
    install = next((n for n, i in enumerate(build) if i.name == "RUN" and re.search(r"pip install|npm ci|npm install", i.args)), None)
    if install is None:
        problems.append("Dockerfile: у першому етапі немає встановлення залежностей (pip install або npm ci)")
    else:
        before = [copy_parts(i)[1] for i in build[:install] if i.name == "COPY"]
        flat = [s for srcs in before for s in srcs]
        if not any("requirements" in s or "package" in s for s in flat):
            problems.append("Dockerfile: перед встановленням залежностей скопіюйте файл залежностей")
        if any(s in (".", "./", "app", "app/") for s in flat):
            problems.append("Dockerfile: код не можна копіювати до встановлення залежностей (зламається кеш шарів)")
    return problems


def check_dockerignore(repo, prj):
    text = _read(repo, ".dockerignore")
    if text is None:
        return [".dockerignore: файла немає"]
    kept = context_files(text, SAMPLE)
    problems = []
    for path in MUST_DROP:
        if path in kept:
            problems.append(f".dockerignore: {path} потрапляє в контекст збірки")
    for path in MUST_KEEP:
        if path not in kept:
            problems.append(f".dockerignore: {path} виключено, а він потрібен для збірки")
    return problems


def _published(svc):
    return norm_ports(svc.get("ports"))


def check_compose(repo, prj):
    text = _read(repo, "compose.yaml")
    if text is None:
        return ["compose.yaml: файла немає (ім'я має бути compose.yaml)"]
    try:
        doc = load_yaml(text)
    except Exception as exc:  # noqa: BLE001
        return [f"compose.yaml: некоректний YAML ({exc})"]
    problems = []
    if "version" in doc:
        problems.append("compose.yaml: поле version застаріле, приберіть його")
    svcs = doc.get("services") or {}
    if not {"web", "db"} <= set(svcs):
        return problems + ["compose.yaml: потрібні служби web і db"]
    web, db = svcs["web"], svcs["db"]
    image = str(db.get("image", ""))
    if "postgres" not in image or not image_is_pinned(image):
        problems.append("compose.yaml: db має використовувати образ postgres із явним тегом (не latest)")
    if "pg_isready" not in json.dumps((db.get("healthcheck") or {}).get("test", "")):
        problems.append("compose.yaml: db потребує healthcheck із pg_isready")
    mounts = [m for m in norm_mounts(db.get("volumes")) if m[2] == "/var/lib/postgresql/data"]
    if not mounts or mounts[0][0] != "volume":
        problems.append("compose.yaml: дані db мають зберігатися в іменованому томі, змонтованому в /var/lib/postgresql/data")
    elif mounts[0][1] not in (doc.get("volumes") or {}):
        problems.append(f"compose.yaml: том {mounts[0][1]} не оголошено в розділі volumes")
    if _published(db):
        problems.append("compose.yaml: db не повинна публікувати порти на хості")
    denv = norm_env(db)
    if not denv.get("POSTGRES_PASSWORD", "").startswith("${"):
        problems.append("compose.yaml: POSTGRES_PASSWORD має братися зі змінної ${POSTGRES_PASSWORD...}, а не з літерала")
    if denv.get("POSTGRES_DB") != prj["db_name"] or denv.get("POSTGRES_USER") != prj["db_user"]:
        problems.append("compose.yaml: POSTGRES_DB і POSTGRES_USER мають збігатися з project.json")
    build = web.get("build")
    ctx = build.get("context") if isinstance(build, dict) else build
    if ctx not in (".", "./"):
        problems.append("compose.yaml: web має збиратися з поточної теки (build: .)")
    expected = f"ghcr.io/{prj['github_owner']}/{prj['image_name']}"
    if not str(web.get("image", "")).startswith(expected):
        problems.append(f"compose.yaml: image служби web має починатися з {expected}")
    if norm_depends(web).get("db") != "service_healthy":
        problems.append("compose.yaml: web має залежати від db з умовою service_healthy")
    if not (web.get("healthcheck") or {}).get("test"):
        problems.append("compose.yaml: web потребує healthcheck")
    want = ("127.0.0.1", str(prj["host_port"]), str(prj["web_port"]))
    if want not in _published(web):
        problems.append(f"compose.yaml: порт web має публікуватися як 127.0.0.1:{prj['host_port']}:{prj['web_port']}")
    url = norm_env(web).get("DATABASE_URL", "")
    if f"@db:5432/{prj['db_name']}" not in url or "${POSTGRES_PASSWORD" not in url:
        problems.append("compose.yaml: DATABASE_URL має вказувати на службу db і брати пароль зі змінної")
    common = set(norm_networks(web)) & set(norm_networks(db))
    if not common or not common <= set(doc.get("networks") or {}):
        problems.append("compose.yaml: web і db мають належати спільній оголошеній мережі (розділ networks)")
    if not web.get("restart") or not db.get("restart"):
        problems.append("compose.yaml: задайте restart для web і db")
    return problems


def check_env_files(repo, prj):
    problems = []
    example = _read(repo, ".env.example")
    if example is None or not re.search(r"^POSTGRES_PASSWORD=", example, re.M):
        problems.append(".env.example: потрібен файл із рядком POSTGRES_PASSWORD=")
    elif re.search(r"^POSTGRES_PASSWORD=\S{12,}", example, re.M):
        problems.append(".env.example: не записуйте справжній пароль, залиште значення порожнім")
    gi = _read(repo, ".gitignore") or ""
    if not any(line.strip() in (".env", "/.env") for line in gi.splitlines()):
        problems.append(".gitignore: додайте рядок .env, щоб секрети не потрапили в репозиторій")
    if (repo / ".git").exists() and shutil.which("git"):
        out = subprocess.run(["git", "-C", str(repo), "ls-files", ".env"], capture_output=True, text=True).stdout.strip()
        if out:
            problems.append(".env відстежується git: видаліть його з індексу (git rm --cached .env) і змініть пароль")
    return problems


def _workflow_file(repo):
    folder = repo / ".github" / "workflows"
    files = sorted(folder.glob("*.y*ml")) if folder.is_dir() else []
    return files


def check_workflow(repo, prj):
    files = _workflow_file(repo)
    if not files:
        return [".github/workflows: немає жодного файла робочого процесу"]
    problems = []
    found = False
    image = f"ghcr.io/{prj['github_owner']}/{prj['image_name']}"
    for path in files:
        text = path.read_text(encoding="utf-8")
        try:
            doc = load_yaml(text)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{path.name}: некоректний YAML ({exc})")
            continue
        jobs = doc.get("jobs") or {}
        pushes = [j for j in jobs.values() if any(str(s.get("uses", "")).startswith("docker/build-push-action") for s in job_steps(j))]
        if not pushes:
            continue
        found = True
        name = path.name
        on = wf_on(doc)
        if "push" not in on or "pull_request" not in on:
            problems.append(f"{name}: процес має запускатися на push і pull_request")
        if "pull_request_target" in on:
            problems.append(f"{name}: pull_request_target небезпечний для збірки коду з форків")
        if doc.get("permissions") != {"contents": "read"}:
            problems.append(f"{name}: на верхньому рівні задайте permissions: contents: read")
        if "write-all" in text:
            problems.append(f"{name}: права write-all заборонені")
        for jname, job in jobs.items():
            perms = job.get("permissions") or {}
            is_pub = job in pushes
            if perms.get("packages") == "write" and not is_pub:
                problems.append(f"{name}: packages: write потрібен лише завданню публікації, а не {jname}")
        job = pushes[0]
        perms = job.get("permissions") or {}
        if perms.get("packages") != "write" or perms.get("contents") != "read":
            problems.append(f"{name}: завдання публікації потребує permissions: contents: read і packages: write")
        steps = job_steps(job)
        login = next((s for s in steps if str(s.get("uses", "")).startswith("docker/login-action")), None)
        if not login:
            problems.append(f"{name}: немає кроку docker/login-action")
        else:
            w = login.get("with") or {}
            if w.get("registry") != "ghcr.io":
                problems.append(f"{name}: login-action має використовувати registry: ghcr.io")
            if "secrets.GITHUB_TOKEN" not in str(w.get("password", "")):
                problems.append(f"{name}: пароль для входу в GHCR має бути ${{{{ secrets.GITHUB_TOKEN }}}}")
        meta = next((s for s in steps if str(s.get("uses", "")).startswith("docker/metadata-action")), None)
        if not meta:
            problems.append(f"{name}: немає кроку docker/metadata-action для тегів")
        else:
            w = meta.get("with") or {}
            if w.get("images") != image:
                problems.append(f"{name}: metadata-action має публікувати образ {image}")
            if "type=sha" not in str(w.get("tags", "")):
                problems.append(f"{name}: серед тегів потрібен type=sha")
        build = next(s for s in steps if str(s.get("uses", "")).startswith("docker/build-push-action"))
        w = build.get("with") or {}
        if "pull_request" not in str(w.get("push", "")):
            problems.append(f"{name}: build-push-action має публікувати лише поза pull_request (push: ${{{{ github.event_name != 'pull_request' }}}})")
        if "cache-from" not in w or "cache-to" not in w:
            problems.append(f"{name}: увімкніть кеш збірки (cache-from і cache-to)")
        if not any("pytest" in str(s.get("run", "")) for j in jobs.values() for s in job_steps(j)):
            problems.append(f"{name}: перед збіркою виконайте pytest")
        elif "test" not in jobs or "test" not in (job.get("needs") if isinstance(job.get("needs"), list) else [job.get("needs")]):
            problems.append(f"{name}: завдання публікації має залежати від завдання test (needs: test)")
        uses = [s["uses"] for j in jobs.values() for s in job_steps(j) if "uses" in s]
        bad = [u for u in uses if not action_pinned(u)]
        if bad:
            problems.append(f"{name}: дії без закріпленої версії: {', '.join(bad)}")
        if re.search(r"password:\s*[^$\s]", text, re.I) or re.search(r"ghp_[A-Za-z0-9]+", text):
            problems.append(f"{name}: у файлі є пароль або токен у відкритому вигляді")
    if not found:
        problems.append("робочі процеси: жоден не використовує docker/build-push-action")
    return problems


def check_answers(repo, prj):
    text = _read(repo, "part_b/ANSWERS.md")
    if text is None:
        return ["part_b/ANSWERS.md: файла немає"]
    problems = []
    if "ЗАПОВНІТЬ" in text:
        problems.append("ANSWERS.md: залишилися місця з позначкою ЗАПОВНІТЬ")
    image = f"ghcr.io/{prj['github_owner']}/{prj['image_name']}"
    if image not in text:
        problems.append(f"ANSWERS.md: має містити вивід docker pull для {image}")
    if not re.search(r"sha256:[0-9a-f]{64}", text):
        problems.append("ANSWERS.md: немає дайджесту sha256 із виводу docker pull")
    if not re.search(r"https://github\.com/[\w.-]+/[\w.-]+/actions/runs/\d+", text):
        problems.append("ANSWERS.md: додайте посилання на успішний запуск робочого процесу (…/actions/runs/<номер>)")
    answers = re.split(r"^### Питання \d+", text, flags=re.M)[1:]
    if len(answers) < 4:
        problems.append("ANSWERS.md: має бути чотири відповіді на питання")
    for n, a in enumerate(answers, 1):
        if len(re.findall(r"\w+", a)) < 20:
            problems.append(f"ANSWERS.md: відповідь на питання {n} закоротка (потрібно щонайменше 20 слів)")
    return problems


def check_project(repo):
    path = repo / "part_b" / "project.json"
    if not path.is_file():
        return None, ["part_b/project.json: файла немає"]
    prj = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(prj.get("github_owner", ""))):
        problems.append("project.json: github_owner має бути вашим логіном GitHub малими латинськими літерами")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", str(prj.get("image_name", ""))):
        problems.append("project.json: image_name має містити лише малі літери, цифри та . _ -")
    return prj, problems


def docker_checks(repo, prj):
    problems = []
    if not shutil.which("docker"):
        return ["--docker: Docker не знайдено"]
    env = dict(os.environ, POSTGRES_PASSWORD="check-only")
    r = subprocess.run(["docker", "compose", "config", "-q"], cwd=repo, env=env, capture_output=True, text=True)
    if r.returncode:
        problems.append("docker compose config: " + r.stderr.strip()[-300:])
    r = subprocess.run(["docker", "build", "-q", "-t", "apsik-lab04-check:test", "."], cwd=repo, capture_output=True, text=True)
    if r.returncode:
        problems.append("docker build: " + (r.stdout + r.stderr).strip()[-300:])
    else:
        subprocess.run(["docker", "rmi", "-f", "apsik-lab04-check:test"], capture_output=True)
    return problems


def check(repo, docker=False):
    """Повертає список невиконаних вимог (порожній, якщо все гаразд)."""
    repo = Path(repo)
    prj, problems = check_project(repo)
    if prj is None:
        return problems
    for fn in (check_dockerfile, check_dockerignore, check_compose, check_env_files, check_workflow, check_answers):
        problems += fn(repo, prj)
    if docker and not problems:
        problems += docker_checks(repo, prj)
    return problems


def main(argv):
    docker = "--docker" in argv
    args = [a for a in argv if not a.startswith("--")]
    repo = Path(args[0]).resolve() if args else HERE.parent
    problems = check(repo, docker)
    if problems:
        print(f"Невиконаних вимог: {len(problems)}")
        for p in problems:
            print("- " + p)
        return 1
    print("Усі вимоги частини Б виконано")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
