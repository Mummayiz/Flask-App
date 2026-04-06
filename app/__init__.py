from pathlib import Path

from flask import Flask

from config import APP_NAME, SECRET_KEY, SESSION_DIR
from app.routes import app_routes
from app.storage import store


def create_app() -> Flask:
    root_dir = Path(__file__).resolve().parent.parent
    app = Flask(__name__, template_folder=str(root_dir / "templates"), static_folder=str(root_dir / "static"))
    app.config.update(
        SECRET_KEY=SECRET_KEY,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_FILE_DIR=str(SESSION_DIR),
        APP_NAME=APP_NAME,
    )
    store.bootstrap()
    app.register_blueprint(app_routes)
    return app
