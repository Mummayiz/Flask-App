from functools import wraps
from typing import Callable

from flask import flash, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def current_user():
    from app.storage import store

    user_id = session.get("user_id")
    if not user_id:
        return None
    return store.get_user(user_id)


def login_required(view: Callable):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Sign in to continue.", "warning")
            return redirect(url_for("app_routes.login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view: Callable):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or user.get("role") != "admin":
            flash("Admin access is required.", "warning")
            return redirect(url_for("app_routes.dashboard"))
        return view(*args, **kwargs)

    return wrapped
