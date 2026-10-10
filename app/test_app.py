"""Модульні тести застосунку (без бази даних). Запуск: pytest app"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import app  # noqa: E402


def test_route_known_paths():
    assert app.route("/health") == "health"
    assert app.route("/") == "index"
    assert app.route("/?x=1") == "index"


def test_route_unknown_path():
    assert app.route("/admin") is None


def test_render_visits_is_json():
    assert json.loads(app.render_visits(3)) == {"visits": 3}
