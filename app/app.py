"""Навчальний вебзастосунок для частини Б: лічильник відвідувань у PostgreSQL.

Змінні середовища: DATABASE_URL (обов'язкова), PORT (за замовчуванням 8000).
Маршрути: GET /health (200, якщо база відповідає, інакше 503), GET / (рахує відвідування й повертає JSON).
Цей файл змінювати не потрібно.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


def route(path):
    """Назва маршруту за шляхом запиту або None."""
    path = path.split("?", 1)[0]
    if path == "/health":
        return "health"
    if path == "/":
        return "index"
    return None


def render_visits(count):
    """JSON-відповідь із кількістю відвідувань."""
    return json.dumps({"visits": count}, ensure_ascii=False)


def connect():
    import psycopg  # імпорт тут, щоб тести без бази не вимагали встановлення драйвера
    return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3)


def count_visit(conn):
    """Додає запис про відвідування й повертає загальну кількість."""
    with conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS visits (id serial PRIMARY KEY, at timestamptz DEFAULT now())")
        cur.execute("INSERT INTO visits DEFAULT VALUES")
        cur.execute("SELECT count(*) FROM visits")
        total = cur.fetchone()[0]
    conn.commit()
    return total


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        name = route(self.path)
        if name is None:
            return self._send(404, "не знайдено")
        try:
            with connect() as conn:
                if name == "health":
                    conn.execute("SELECT 1")
                    return self._send(200, "ok")
                return self._send(200, render_visits(count_visit(conn)), "application/json")
        except Exception as exc:  # noqa: BLE001
            return self._send(503, f"база даних недоступна: {type(exc).__name__}")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
