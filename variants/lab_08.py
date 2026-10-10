import re
import yaml

def compose_profiles(project, db_image, web_image, tools, defaults, required):
    seen_services = set()
    
    # Валідація tools
    for tool in tools:
        t_name = tool.get('name')
        if t_name in ('web', 'db'):
            raise ValueError(f"Ім'я служби зайняте: {t_name}")
        if t_name in seen_services:
            raise ValueError(f"Дубль служби: {t_name}")
        seen_services.add(t_name)
        
        profile = tool.get('profile', '')
        # Перший символ - літера або цифра, далі щонайменше один символ (довжина від 2, без обов'язкової крапки)
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]{1,}$', profile):
            raise ValueError(f"Некоректне ім'я профілю: {profile}")

    services = {}
    
    # Служба db
    services['db'] = {
        'image': db_image,
        'restart': 'unless-stopped',
        'environment': {
            'POSTGRES_DB': '${DB_NAME:-appdb}',
            'POSTGRES_USER': '${DB_USER:-appuser}',
            'POSTGRES_PASSWORD': '${POSTGRES_PASSWORD:?Задайте POSTGRES_PASSWORD}'
        },
        'healthcheck': {
            'test': ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-appuser} -d ${DB_NAME:-appdb}"],
            'interval': '10s',
            'timeout': '5s',
            'retries': 5
        }
    }
    
    # Служба web
    web_env = {}
    for req in required:
        web_env[req] = f"${{{req}:?Задайте {req}}}"
    for k, v in defaults.items():
        web_env[k] = f"${{{k}:-{v}}}"
        
    services['web'] = {
        'image': web_image,
        'restart': 'unless-stopped',
        'environment': web_env,
        'depends_on': {
            'db': {
                'condition': 'service_healthy'
            }
        }
    }
    
    # Допоміжні служби з tools
    for tool in tools:
        t_name = tool['name']
        t_service = {
            'image': tool['image'],
            'profiles': [tool['profile']]
        }
        if 'command' in tool and tool['command']:
            t_service['command'] = tool['command']
        if tool.get('once'):
            t_service['restart'] = "no"  # рядок "no" в лапках
        if 'port' in tool and tool['port']:
            p = tool['port']
            t_service['ports'] = [f"127.0.0.1:{p}:{p}"]
        if tool.get('needs_db', True):
            t_service['depends_on'] = {
                'db': {
                    'condition': 'service_healthy'
                }
            }
        services[t_name] = t_service

    config = {
        'name': project,
        'services': services
    }
    
    yaml_text = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
    return yaml_text


def env_example(defaults, required):
    lines = ["# Файл зі змінними середовища за замовчуванням"]
    for req in required:
        lines.append(f"{req}=")
    for k, v in defaults.items():
        lines.append(f"{k}={v}")
    return "\n".join(lines) + "\n"