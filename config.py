from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SESSION_DIR = BASE_DIR / "flask_session"
BACKUP_DIR = BASE_DIR / "backups"

SECRET_KEY = "local-productivity-analytics-secret"
APP_NAME = "Pulseboard"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
DEMO_USER_COUNT = 1000

DATA_FILES = {
    "users": DATA_DIR / "users.json",
    "tasks": DATA_DIR / "tasks.json",
    "focus": DATA_DIR / "focus.json",
    "hobbies": DATA_DIR / "hobbies.json",
    "calendar_events": DATA_DIR / "calendar_events.json",
    "activity_logs": DATA_DIR / "activity_logs.json",
    "ai_data": DATA_DIR / "ai_data.json",
}
