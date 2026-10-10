"""Драйвери задач: викликають вашу функцію й зводять результат до перевірюваних фактів.

Факти (словники) обчислює код, а очікувані значення записано в тестах. Помилки подано як ("!КласПомилки", "повідомлення").
Не змінюйте цей файл.
"""
import re

from conftest import load  # noqa: F401  (зручно мати поруч)
from stacklib import (action_pinned, context_files, copy_parts, image_is_pinned, job_steps, json_args,
                      load_yaml, norm_depends, norm_env, norm_mounts, norm_networks, norm_ports,
                      parse_dockerfile, parse_from, parse_healthcheck, stages, wf_on)

SECRET = re.compile(r"PASSWORD|PASSWD|SECRET|TOKEN|API_?KEY|PRIVATE_?KEY", re.I)


def safe(fn, *args, **kwargs):
    """Виконує fn; виняток перетворюється на кортеж ("!Клас", "повідомлення")."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        return ("!" + type(exc).__name__, str(exc))


def _is_error(value):
    return isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str) and value[0].startswith("!")


def _text(value):
    if not isinstance(value, str):
        return ("!TypeError", "очікувався рядок з текстом файла, отримано " + type(value).__name__)
    return None


def _env_of(instrs):
    out = {}
    for ins in instrs:
        if ins.name == "ENV":
            for part in ins.args.split():
                key, _, value = part.partition("=")
                out[key] = value
    return out


# ---- Задача 1


def d_cached(mod, **kw):
    text = safe(mod.dockerfile_cached, **kw)
    if _is_error(text):
        return text
    if _text(text):
        return _text(text)
    ins = parse_dockerfile(text)
    froms = [i for i in ins if i.name == "FROM"]
    runs = [(n, i) for n, i in enumerate(ins) if i.name == "RUN"]
    first_run = runs[0][0] if runs else len(ins)
    deps, src_before, src_after = set(), False, False
    for n, i in enumerate(ins):
        if i.name != "COPY":
            continue
        _, srcs, _ = copy_parts(i)
        for s in srcs:
            if s == ".":
                src_before |= n < first_run
                src_after |= n > first_run
            elif n < first_run:
                deps.add(s)
    workdirs = [i.args for i in ins if i.name == "WORKDIR"]
    cmd = [i for i in ins if i.name == "CMD"]
    return {
        "base": parse_from(froms[0].args)[0] if froms else None,
        "stages": len(froms),
        "workdir": workdirs[-1] if workdirs else None,
        "env": _env_of(ins),
        "deps": sorted(deps),
        "install": [i.args for _, i in runs],
        "source_before_install": src_before,
        "source_after_install": src_after,
        "expose": [int(i.args.split("/")[0]) for i in ins if i.name == "EXPOSE"],
        "cmd": json_args(cmd[-1].args) if cmd else None,
    }


# ---- Задача 2


def d_multistage(mod, **kw):
    text = safe(mod.dockerfile_multistage, **kw)
    if _is_error(text):
        return text
    if _text(text):
        return _text(text)
    groups = stages(parse_dockerfile(text))
    first, last = (groups[0], groups[-1]) if groups else ([], [])
    b_base, b_alias = parse_from(first[0].args) if first else (None, None)
    f_base = parse_from(last[0].args)[0] if last else None
    copies, other_copies = [], 0
    for i in last:
        if i.name == "COPY":
            flags, srcs, dst = copy_parts(i)
            if flags.get("from") == "builder" and len(groups) > 1:
                copies += [(s, dst) for s in srcs]
            else:
                other_copies += 1
    cmd = [i for i in last if i.name == "CMD"]
    return {
        "stages": len(groups),
        "builder_base": b_base,
        "builder_alias": b_alias,
        "final_base": f_base,
        "builder_runs": [i.args for i in first if i.name == "RUN"],
        "final_runs": [i.args for i in last if i.name == "RUN"] if len(groups) > 1 else None,
        "copies": copies,
        "final_other_copies": other_copies,
        "workdir": [i.args for i in last if i.name == "WORKDIR"][-1:] or None,
        "expose": [int(i.args.split("/")[0]) for i in last if i.name == "EXPOSE"],
        "cmd": json_args(cmd[-1].args) if cmd else None,
    }


# ---- Задача 3


def d_hardened(mod, **kw):
    text = safe(mod.dockerfile_hardened, **kw)
    if _is_error(text):
        return text
    if _text(text):
        return _text(text)
    ins = parse_dockerfile(text)
    froms = [i for i in ins if i.name == "FROM"]
    users = [(n, i) for n, i in enumerate(ins) if i.name == "USER"]
    last_n, last_user = users[-1] if users else (len(ins), None)
    name = (last_user.args.split(":")[0] if last_user else None)
    uid = kw.get("uid")
    created = any(i.name == "RUN" and re.search(r"useradd|adduser", i.args) and kw["user"] in i.args
                  for i in ins[:last_n])
    chown = any(i.name == "COPY" and copy_parts(i)[0].get("chown") == f"{uid}:{uid}" for i in ins)
    health = [parse_healthcheck(i.args) for i in ins if i.name == "HEALTHCHECK"]
    cmd = [i for i in ins if i.name == "CMD"]
    secret_keys = [p.partition("=")[0] for i in ins if i.name in ("ENV", "ARG") for p in i.args.split()
                   if SECRET.search(p.partition("=")[0])]
    first_run = next((n for n, i in enumerate(ins) if i.name == "RUN" and not re.search(r"useradd|adduser", i.args)), len(ins))
    deps = sorted(s for n, i in enumerate(ins) if i.name == "COPY" and n < first_run for s in copy_parts(i)[1] if s != ".")
    return {
        "base": parse_from(froms[0].args)[0] if froms else None,
        "deps": deps,
        "install": [i.args for i in ins if i.name == "RUN" and not re.search(r"useradd|adduser", i.args)],
        "user": last_user.args if last_user else None,
        "nonroot": bool(last_user) and name not in ("root", "0"),
        "runs_after_user": sum(1 for n, i in enumerate(ins) if i.name == "RUN" and n > last_n),
        "user_before_cmd": bool(cmd) and last_n < ins.index(cmd[-1]),
        "user_created": created,
        "chown": chown,
        "health": health[-1] if health else None,
        "secrets": secret_keys,
        "env": _env_of(ins),
        "expose": [int(i.args.split("/")[0]) for i in ins if i.name == "EXPOSE"],
        "cmd": json_args(cmd[-1].args) if cmd else None,
    }


# ---- Задача 4


def d_ignore(mod, stack, keep, extra, files):
    text = safe(mod.dockerignore, stack, keep, extra)
    if _is_error(text):
        return text
    if _text(text):
        return _text(text)
    return context_files(text, files)


# ---- Задача 5


def _svc(doc):
    svcs = doc.get("services")
    return svcs if isinstance(svcs, dict) else {}


def _health_test(svc):
    hc = svc.get("healthcheck") or {}
    return hc.get("test")


def _build_ctx(svc):
    build = svc.get("build")
    if isinstance(build, dict):
        return build.get("context")
    return build


def d_web_db(mod, **kw):
    text = safe(mod.compose_web_db, **kw)
    if _is_error(text):
        return text
    if _text(text):
        return _text(text)
    doc = load_yaml(text)
    svcs = _svc(doc)
    web, db = svcs.get("web", {}), svcs.get("db", {})
    hc = db.get("healthcheck") or {}
    return {
        "has_version": "version" in doc,
        "name": doc.get("name"),
        "services": sorted(svcs),
        "db_image": db.get("image"),
        "db_health": _health_test(db),
        "db_health_params": sorted(k for k in ("interval", "timeout", "retries") if k in hc),
        "db_ports": norm_ports(db.get("ports")),
        "web_image": web.get("image"),
        "web_build": _build_ctx(web),
        "web_ports": norm_ports(web.get("ports")),
        "web_depends": norm_depends(web),
        "web_health": _health_test(web),
        "database_url": norm_env(web).get("DATABASE_URL"),
        "password_literal": not norm_env(db).get("POSTGRES_PASSWORD", "").startswith("${"),
        "db_env": {k: v for k, v in norm_env(db).items() if k != "POSTGRES_PASSWORD"},
        "restart": {n: s.get("restart") for n, s in sorted(svcs.items())},
    }


# ---- Задача 6


def d_volumes(mod, **kw):
    text = safe(mod.compose_volumes, **kw)
    if _is_error(text):
        return text
    if _text(text):
        return _text(text)
    doc = load_yaml(text)
    db = _svc(doc).get("db", {})
    top = doc.get("volumes") or {}
    return {
        "has_version": "version" in doc,
        "services": sorted(_svc(doc)),
        "mounts": sorted(norm_mounts(db.get("volumes"))),
        "top_volumes": {k: (v or {}) for k, v in top.items()},
        "db_ports": norm_ports(db.get("ports")),
        "healthcheck": bool(_health_test(db)),
        "password_literal": not norm_env(db).get("POSTGRES_PASSWORD", "").startswith("${"),
    }


# ---- Задача 7


def d_networks(mod, **kw):
    text = safe(mod.compose_networks, **kw)
    if _is_error(text):
        return text
    if _text(text):
        return _text(text)
    doc = load_yaml(text)
    svcs = _svc(doc)
    tops = doc.get("networks") or {}
    cfg = (tops.get("backend") or {}).get("ipam", {}).get("config", []) if isinstance(tops.get("backend"), dict) else []
    return {
        "has_version": "version" in doc,
        "services": sorted(svcs),
        "networks": {n: sorted(norm_networks(s)) for n, s in sorted(svcs.items())},
        "ports": {n: norm_ports(s.get("ports")) for n, s in sorted(svcs.items())},
        "top_networks": sorted(tops),
        "backend_internal": bool((tops.get("backend") or {}).get("internal")),
        "frontend_internal": bool((tops.get("frontend") or {}).get("internal")),
        "web_aliases": {n: sorted(v.get("aliases", [])) for n, v in norm_networks(svcs.get("web", {})).items()},
        "subnets": [c.get("subnet") for c in cfg],
        "host_network": any(s.get("network_mode") == "host" for s in svcs.values()),
    }


# ---- Задача 8


def d_profiles(mod, **kw):
    text = safe(mod.compose_profiles, **kw)
    if _is_error(text):
        return text
    if _text(text):
        return _text(text)
    doc = load_yaml(text)
    svcs = _svc(doc)
    web = svcs.get("web", {})
    return {
        "has_version": "version" in doc,
        "services": sorted(svcs),
        "profiles": {n: sorted(s.get("profiles", [])) for n, s in sorted(svcs.items())},
        "web_env": norm_env(web),
        "db_password": norm_env(svcs.get("db", {})).get("POSTGRES_PASSWORD"),
        "tool_ports": {n: norm_ports(s.get("ports")) for n, s in sorted(svcs.items()) if n not in ("web", "db")},
        "tool_depends": {n: norm_depends(s) for n, s in sorted(svcs.items()) if n not in ("web", "db")},
        "tool_restart": {n: s.get("restart") for n, s in sorted(svcs.items()) if n not in ("web", "db")},
        "tool_command": {n: s.get("command") for n, s in sorted(svcs.items()) if n not in ("web", "db")},
    }


def d_envfile(mod, defaults, required):
    text = safe(mod.env_example, defaults, required)
    if _is_error(text):
        return text
    if _text(text):
        return _text(text)
    pairs = []
    for line in text.splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            key, sep, value = line.partition("=")
            pairs.append((key.strip(), value.strip() if sep else None))
    return {"pairs": pairs, "has_comment": any(l.lstrip().startswith("#") for l in text.splitlines()),
            "ends_with_newline": text.endswith("\n")}


# ---- Задача 9 і 10


def _expr(value):
    """Приводить пробіли всередині ${{ ... }} до єдиного вигляду."""
    if isinstance(value, str):
        return re.sub(r"\$\{\{\s*(.*?)\s*\}\}", lambda m: "${{ " + re.sub(r"\s+", " ", m.group(1)) + " }}", value.strip())
    return value


def _cond(value):
    """Умова if або push: однакова з ${{ }} і без них."""
    if isinstance(value, str):
        m = re.fullmatch(r"\$\{\{\s*(.*?)\s*\}\}", value.strip())
        return re.sub(r"\s+", " ", (m.group(1) if m else value).strip())
    return value


def _wf(text):
    doc = load_yaml(text)
    return doc, wf_on(doc), doc.get("jobs") or {}


def _all_uses(jobs):
    return [s["uses"] for j in jobs.values() for s in job_steps(j) if "uses" in s]


def d_ci(mod, **kw):
    text = safe(mod.workflow_ci, **kw)
    if _is_error(text):
        return text
    if _text(text):
        return _text(text)
    doc, on, jobs = _wf(text)
    job = jobs.get("test", {})
    steps = job_steps(job)
    setup = next((s for s in steps if str(s.get("uses", "")).startswith("actions/setup-python")), {})
    matrix = ((job.get("strategy") or {}).get("matrix") or {}).get("python-version")
    return {
        "name": doc.get("name"),
        "events": sorted(on),
        "push_branches": (on.get("push") or {}).get("branches"),
        "pr_branches": (on.get("pull_request") or {}).get("branches"),
        "push_paths": (on.get("push") or {}).get("paths"),
        "pr_paths": (on.get("pull_request") or {}).get("paths"),
        "cron": [s.get("cron") for s in (on.get("schedule") or [])],
        "concurrency": {k: _expr(v) for k, v in (doc.get("concurrency") or {}).items()} or None,
        "permissions": doc.get("permissions"),
        "jobs": sorted(jobs),
        "runs_on": job.get("runs_on", job.get("runs-on")),
        "timeout": job.get("timeout-minutes"),
        "matrix": matrix,
        "fail_fast": (job.get("strategy") or {}).get("fail-fast"),
        "setup_version": _expr((setup.get("with") or {}).get("python-version")),
        "cache": (setup.get("with") or {}).get("cache"),
        "uses": _all_uses(jobs),
        "all_pinned": all(action_pinned(u) for u in _all_uses(jobs)),
        "runs": [s["run"] for s in steps if "run" in s],
        "first_step_checkout": bool(steps) and str(steps[0].get("uses", "")).startswith("actions/checkout@"),
    }


def d_publish(mod, **kw):
    text = safe(mod.workflow_publish, **kw)
    if _is_error(text):
        return text
    if _text(text):
        return _text(text)
    doc, on, jobs = _wf(text)
    pub = jobs.get("publish", {})
    steps = job_steps(pub)

    def step(prefix):
        return next((s for s in steps if str(s.get("uses", "")).startswith(prefix)), {})
    login, meta, build = step("docker/login-action"), step("docker/metadata-action"), step("docker/build-push-action")
    run_texts = [s.get("run", "") for j in jobs.values() for s in job_steps(j)]
    tags = [t.strip() for t in str((meta.get("with") or {}).get("tags", "")).splitlines() if t.strip()]
    return {
        "events": sorted(on),
        "push_branches": (on.get("push") or {}).get("branches"),
        "push_tags": (on.get("push") or {}).get("tags"),
        "pr_branches": (on.get("pull_request") or {}).get("branches"),
        "pull_request_target": "pull_request_target" in on,
        "top_permissions": doc.get("permissions"),
        "jobs": sorted(jobs),
        "needs": pub["needs"][0] if isinstance(pub.get("needs"), list) and len(pub["needs"]) == 1 else pub.get("needs"),
        "publish_permissions": pub.get("permissions"),
        "test_permissions": (jobs.get("test") or {}).get("permissions"),
        "login": {"registry": (login.get("with") or {}).get("registry"),
                  "username": _expr((login.get("with") or {}).get("username")),
                  "password": _expr((login.get("with") or {}).get("password")),
                  "if": _cond(login.get("if"))},
        "meta_images": (meta.get("with") or {}).get("images"),
        "meta_tags": tags,
        "build": {k: (_cond(v) if k == "push" else _expr(v)) for k in ("context", "push", "tags", "cache-from", "cache-to")
                  for v in [(build.get("with") or {}).get(k)]},
        "secrets": sorted(set(re.findall(r"secrets\.([A-Za-z0-9_]+)", text))),
        "secrets_in_run": any("secrets." in r for r in run_texts),
        "all_pinned": all(action_pinned(u) for u in _all_uses(jobs)),
        "write_all": "write-all" in text,
        "deploy_step_env": [{k: _expr(v) for k, v in s["env"].items()} for s in steps if "run" in s and s.get("env")],
    }


DRIVERS = {k[2:]: v for k, v in dict(globals()).items() if k.startswith("d_")}
