from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path

from werkzeug.security import generate_password_hash

from config import ADMIN_PASSWORD, ADMIN_USERNAME, BACKUP_DIR, DATA_DIR, DATA_FILES, SESSION_DIR
from app.coach import default_ai_entries
from utils.seeding import seed_demo_data


class JSONStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()

    def bootstrap(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        for path in DATA_FILES.values():
            if not path.exists():
                self._write(path, [])
        users = self.read("users")
        if not any(user.get("role") == "admin" for user in users):
            users.append(
                {
                    "id": str(uuid.uuid4()),
                    "username": ADMIN_USERNAME,
                    "email": "admin@pulseboard.local",
                    "password_hash": generate_password_hash(ADMIN_PASSWORD),
                    "role": "admin",
                    "theme": "dark",
                    "created_at": self.now(),
                }
            )
            self.write("users", users)
        if len(self.read("ai_data")) < 200:
            self.write("ai_data", default_ai_entries())
        if len(self.read("users")) <= 1 and not self.read("tasks") and not self.read("focus"):
            seed_demo_data(self)

    def now(self) -> str:
        return datetime.utcnow().isoformat(timespec="seconds")

    def _read(self, path: Path):
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, path: Path, payload) -> None:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        temp_path.replace(path)

    def read(self, key: str):
        return self._read(DATA_FILES[key])

    def write(self, key: str, payload) -> None:
        with self._lock:
            self._write(DATA_FILES[key], payload)

    def get_user(self, user_id: str):
        return next((user for user in self.read("users") if user["id"] == user_id), None)

    def get_user_by_login(self, login: str):
        login = login.strip().lower()
        for user in self.read("users"):
            if user.get("username", "").lower() == login or user.get("email", "").lower() == login:
                return user
        return None

    def create_user(self, username: str, email: str, password: str):
        users = self.read("users")
        lowered_email = email.strip().lower()
        lowered_username = username.strip().lower()
        if not lowered_username or len(lowered_username) < 3:
            raise ValueError("Username must be at least 3 characters.")
        if "@" not in lowered_email or "." not in lowered_email:
            raise ValueError("Enter a valid email address.")
        if any(user.get("email", "").lower() == lowered_email for user in users):
            raise ValueError("Email already exists.")
        if any(user.get("username", "").lower() == lowered_username for user in users):
            raise ValueError("Username already exists.")
        user = {
            "id": str(uuid.uuid4()),
            "username": username.strip(),
            "email": lowered_email,
            "password_hash": generate_password_hash(password),
            "role": "user",
            "theme": "dark",
            "created_at": self.now(),
        }
        users.append(user)
        self.write("users", users)
        self.log(user["id"], "account", "Created a new account.", 3)
        return user

    def update_collection_item(self, key: str, item_id: str, payload: dict):
        items = self.read(key)
        for index, item in enumerate(items):
            if item["id"] == item_id:
                items[index] = {**item, **payload}
                self.write(key, items)
                return True
        return False

    def delete_collection_item(self, key: str, item_id: str):
        items = self.read(key)
        filtered = [item for item in items if item["id"] != item_id]
        if len(filtered) != len(items):
            self.write(key, filtered)
            return True
        return False

    def add_record(self, key: str, record: dict):
        items = self.read(key)
        items.append(record)
        self.write(key, items)

    def log(self, user_id: str, category: str, description: str, value: int = 1) -> None:
        logs = self.read("activity_logs")
        logs.append(
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "category": category,
                "description": description,
                "value": value,
                "date": datetime.utcnow().date().isoformat(),
                "timestamp": self.now(),
            }
        )
        self.write("activity_logs", logs)


store = JSONStore()
