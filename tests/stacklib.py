"""Розбір Dockerfile, compose.yaml, робочих процесів GitHub Actions і .dockerignore.

Модуль лише читає текст і повертає структури Python: перевірок тут немає.
Не змінюйте цей файл: ним користуються відкриті тести й скрипт перевірки частини Б.
"""
import json
import posixpath
import re
from collections import namedtuple

import yaml

Instr = namedtuple("Instr", "name args stage line")


# ---------------------------------------------------------------- Dockerfile


def parse_dockerfile(text):
    """Повертає список Instr(name, args, stage, line). Коментарі й порожні рядки пропускаються,
    продовження рядків через зворотну скісну риску зливаються, номер етапу збільшується на кожному FROM."""
    result, buf, start, stage = [], "", 0, -1
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not buf and (not line.strip() or line.lstrip().startswith("#")):
            continue
        if line.lstrip().startswith("#"):
            continue
        if not buf:
            start = number
        if line.endswith("\\"):
            buf += line[:-1] + " "
            continue
        buf += line
        parts = buf.strip().split(None, 1)
        name = parts[0].upper()
        args = parts[1].strip() if len(parts) > 1 else ""
        if name == "FROM":
            stage += 1
        result.append(Instr(name, re.sub(r"\s+", " ", args) if name == "RUN" and not args.startswith("[") else args,
                            max(stage, 0), start))
        buf = ""
    return result


def json_args(args):
    """Якщо аргументи записані у формі exec (JSON-масив), повертає список, інакше None."""
    args = args.strip()
    if args.startswith("["):
        try:
            value = json.loads(args)
        except ValueError:
            return None
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            return value
    return None


def parse_from(args):
    """FROM [--platform=..] образ [AS ім'я] -> (образ, ім'я або None)."""
    tokens = [t for t in args.split() if not t.startswith("--")]
    image = tokens[0]
    alias = tokens[2] if len(tokens) >= 3 and tokens[1].upper() == "AS" else None
    return image, alias


def split_flags(args):
    """Відокремлює початкові прапорці --ключ=значення від решти. Повертає (словник, решта_рядка)."""
    flags, rest = {}, args.strip()
    while rest.startswith("--"):
        token, _, rest = rest.partition(" ")
        key, _, value = token[2:].partition("=")
        flags[key] = value
        rest = rest.strip()
    return flags, rest


def copy_parts(instr):
    """COPY/ADD -> (прапорці, [джерела], призначення)."""
    flags, rest = split_flags(instr.args)
    items = json_args(rest) or rest.split()
    return flags, items[:-1], items[-1]


def image_is_pinned(image):
    """Образ має явний тег (не latest) або дайджест; scratch дозволений."""
    if image == "scratch" or "@sha256:" in image:
        return True
    name = image.rsplit("/", 1)[-1]
    if ":" not in name:
        return False
    return name.split(":", 1)[1] != "latest"


def stages(instrs):
    """Групує інструкції за етапами: список списків."""
    out = []
    for ins in instrs:
        while len(out) <= ins.stage:
            out.append([])
        out[ins.stage].append(ins)
    return out


def parse_healthcheck(args):
    """HEALTHCHECK [--interval=..] CMD ... -> словник із ключами interval, timeout, start_period, retries, cmd."""
    flags, rest = split_flags(args)
    out = {"interval": flags.get("interval"), "timeout": flags.get("timeout"),
           "start_period": flags.get("start-period"),
           "retries": int(flags["retries"]) if "retries" in flags else None, "cmd": None}
    if rest.upper().startswith("CMD"):
        out["cmd"] = json_args(rest[3:].strip())
    return out


# ---------------------------------------------------------------- Compose / YAML


def load_yaml(text):
    """Розбирає YAML-текст; корінь має бути відображенням."""
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Корінь YAML має бути відображенням")
    return data


def norm_ports(ports):
    """Список портів Compose -> список (ip, опублікований, цільовий)."""
    out = []
    for item in ports or []:
        if isinstance(item, dict):
            out.append((item.get("host_ip", ""), str(item.get("published", "")), str(item.get("target", ""))))
            continue
        parts = str(item).split(":")
        if len(parts) == 1:
            out.append(("", "", parts[0]))
        elif len(parts) == 2:
            out.append(("", parts[0], parts[1]))
        else:
            out.append((parts[0], parts[1], parts[2]))
    return out


def norm_mounts(volumes):
    """Список томів служби -> список (тип, джерело, ціль, лише_читання). Тип: volume, bind, tmpfs."""
    out = []
    for item in volumes or []:
        if isinstance(item, dict):
            out.append((item.get("type", "volume"), item.get("source", ""), item.get("target", ""),
                        bool(item.get("read_only", False))))
            continue
        parts = str(item).split(":")
        if len(parts) == 1:
            out.append(("volume", "", parts[0], False))
            continue
        source, target = parts[0], parts[1]
        ro = len(parts) > 2 and "ro" in parts[2].split(",")
        kind = "bind" if source.startswith((".", "/", "~")) else "volume"
        out.append((kind, source, target, ro))
    return out


def norm_networks(svc):
    """Мережі служби -> {ім'я: {aliases: [...]}}."""
    nets = svc.get("networks")
    if nets is None:
        return {}
    if isinstance(nets, list):
        return {n: {} for n in nets}
    return {n: (v or {}) for n, v in nets.items()}


def norm_depends(svc):
    """depends_on -> {служба: умова}."""
    dep = svc.get("depends_on")
    if dep is None:
        return {}
    if isinstance(dep, list):
        return {d: "service_started" for d in dep}
    return {d: (v or {}).get("condition", "service_started") for d, v in dep.items()}


def norm_env(svc):
    """environment -> словник рядків."""
    env = svc.get("environment")
    if env is None:
        return {}
    if isinstance(env, list):
        out = {}
        for item in env:
            key, _, value = str(item).partition("=")
            out[key] = value
        return out
    return {k: ("" if v is None else str(v)) for k, v in env.items()}


# ---------------------------------------------------------------- GitHub Actions


def wf_on(doc):
    """Тригери робочого процесу -> {подія: налаштування}. Ключ on у YAML 1.1 читається як True."""
    value = doc.get("on", doc.get(True))
    if value is None:
        return {}
    if isinstance(value, str):
        return {value: {}}
    if isinstance(value, list):
        return {v: {} for v in value}
    return {k: (v or {}) for k, v in value.items()}


def action_pinned(uses):
    """owner/repo@vN, @vN.M.K або @<40 hex>; гілки main/master/latest і відсутність версії не дозволені."""
    if "@" not in uses:
        return False
    ref = uses.split("@", 1)[1]
    return bool(re.fullmatch(r"v\d+(\.\d+){0,2}", ref) or re.fullmatch(r"[0-9a-f]{40}", ref))


def job_steps(job):
    return job.get("steps") or []


# ---------------------------------------------------------------- .dockerignore


def _glob_regex(pattern):
    out, i = "", 0
    while i < len(pattern):
        ch = pattern[i]
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
            continue
        if pattern.startswith("**", i):
            out += ".*"
            i += 2
            continue
        if ch == "*":
            out += "[^/]*"
        elif ch == "?":
            out += "[^/]"
        elif ch == "[":
            j = pattern.find("]", i + 1)
            if j == -1:
                out += re.escape(ch)
            else:
                out += "[" + pattern[i + 1:j].replace("\\", "\\\\") + "]"
                i = j
        else:
            out += re.escape(ch)
        i += 1
    return re.compile(out + r"\Z")


def parse_ignore(text):
    """Текст .dockerignore -> список (шаблон, виняток)."""
    rules = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negate = line.startswith("!")
        if negate:
            line = line[1:].strip()
        line = posixpath.normpath(line.lstrip("/")) if line.strip("/") else line
        rules.append((line, negate))
    return rules


def is_ignored(path, rules):
    """Чи не потрапить файл у контекст збірки: остання відповідність виграє; збіг із батьківською текою діє на все всередині."""
    prefixes = []
    parts = path.split("/")
    for i in range(len(parts)):
        prefixes.append("/".join(parts[:i + 1]))
    ignored = False
    for pattern, negate in rules:
        regex = _glob_regex(pattern)
        if any(regex.match(p) for p in prefixes):
            ignored = not negate
    return ignored


def context_files(text, files):
    """Які файли зі списку залишаться в контексті збірки."""
    rules = parse_ignore(text)
    return sorted(f for f in files if not is_ignored(f, rules))
