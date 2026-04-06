from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.analytics import admin_analytics, user_analytics
from app.auth import admin_required, current_user, login_required, verify_password
from app.coach import coach_reply, topic_breakdown
from app.storage import store


app_routes = Blueprint("app_routes", __name__)


def today_value() -> str:
    return date.today().isoformat()


def page_context(user=None):
    return {
        "app_name": "Pulseboard",
        "current_user": user,
        "today": today_value(),
    }


def user_records(user_id: str) -> dict:
    return {
        "tasks": [item for item in store.read("tasks") if item.get("user_id") == user_id],
        "focus": [item for item in store.read("focus") if item.get("user_id") == user_id],
        "hobbies": [item for item in store.read("hobbies") if item.get("user_id") == user_id],
        "calendar_events": [item for item in store.read("calendar_events") if item.get("user_id") == user_id],
        "activity_logs": [item for item in store.read("activity_logs") if item.get("user_id") == user_id],
    }


def dashboard_endpoint_for(user: dict) -> str:
    return "app_routes.admin_dashboard" if user.get("role") == "admin" else "app_routes.user_dashboard"


def safe_int(raw: str, fallback: int) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return fallback
    return max(1, value)


@app_routes.route("/")
def index():
    user = current_user()
    if user:
        return redirect(url_for(dashboard_endpoint_for(user)))
    return redirect(url_for("app_routes.login"))


@app_routes.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    return redirect(url_for(dashboard_endpoint_for(user)))


@app_routes.route("/user/dashboard")
@login_required
def user_dashboard():
    user = current_user()
    if user.get("role") == "admin":
        return redirect(url_for("app_routes.admin_dashboard"))
    records = user_records(user["id"])
    analytics = user_analytics(user, **records)
    chart_payload = {
        "tasks": analytics["task_status_counts"],
        "priorities": analytics["task_priority_counts"],
        "dailyFocus": analytics["daily_focus"],
    }
    return render_template(
        "dashboard.html",
        **page_context(user),
        analytics=analytics,
        chart_payload=json.dumps(chart_payload),
    )


@app_routes.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("auth/register.html", **page_context())
        try:
            user = store.create_user(username, email, password)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("auth/register.html", **page_context())
        session["user_id"] = user["id"]
        flash("Account created successfully.", "success")
        return redirect(url_for("app_routes.user_dashboard"))
    return render_template("auth/register.html", **page_context())


@app_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_value = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        user = store.get_user_by_login(login_value)
        if not user or not verify_password(password, user["password_hash"]):
            flash("Invalid username/email or password.", "error")
            return render_template("auth/login.html", **page_context())
        session["user_id"] = user["id"]
        store.log(user["id"], "auth", "Signed in.", 1)
        return redirect(url_for(dashboard_endpoint_for(user)))
    return render_template("auth/login.html", **page_context(), admin_mode=False)


@app_routes.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        login_value = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        user = store.get_user_by_login(login_value)
        if not user or user.get("role") != "admin" or not verify_password(password, user["password_hash"]):
            flash("Invalid admin credentials.", "error")
            return render_template("auth/login.html", **page_context(), admin_mode=True)
        session["user_id"] = user["id"]
        store.log(user["id"], "auth", "Signed in to admin workspace.", 1)
        return redirect(url_for("app_routes.admin_dashboard"))
    return render_template("auth/login.html", **page_context(), admin_mode=True)


@app_routes.route("/logout")
def logout():
    user = current_user()
    if user:
        store.log(user["id"], "auth", "Signed out.", 1)
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("app_routes.login"))


@app_routes.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks():
    user = current_user()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Task title is required.", "error")
            return redirect(url_for("app_routes.tasks"))
        record = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "title": title,
            "priority": request.form.get("priority", "medium"),
            "difficulty": request.form.get("difficulty", "medium"),
            "due_date": request.form.get("due_date", today_value()),
            "status": request.form.get("status", "pending"),
            "created_at": store.now(),
        }
        store.add_record("tasks", record)
        store.log(user["id"], "task", f"Added task: {title}", 2)
        flash("Task saved.", "success")
        return redirect(url_for("app_routes.tasks"))

    tasks_for_user = sorted(user_records(user["id"])["tasks"], key=lambda item: item.get("created_at", ""), reverse=True)
    return render_template("tasks.html", **page_context(user), tasks=tasks_for_user)


@app_routes.route("/tasks/<task_id>/status", methods=["POST"])
@login_required
def task_status(task_id: str):
    user = current_user()
    task = next((item for item in store.read("tasks") if item["id"] == task_id and item["user_id"] == user["id"]), None)
    if task:
        next_status = request.form.get("status", "completed")
        store.update_collection_item("tasks", task_id, {"status": next_status})
        store.log(user["id"], "task", f"Marked task '{task['title']}' as {next_status}.", 2)
        flash("Task updated.", "success")
    return redirect(url_for("app_routes.tasks"))


@app_routes.route("/tasks/<task_id>/delete", methods=["POST"])
@login_required
def task_delete(task_id: str):
    user = current_user()
    task = next((item for item in store.read("tasks") if item["id"] == task_id and item["user_id"] == user["id"]), None)
    if task and store.delete_collection_item("tasks", task_id):
        store.log(user["id"], "task", f"Deleted task: {task['title']}", 1)
        flash("Task deleted.", "success")
    return redirect(url_for("app_routes.tasks"))


@app_routes.route("/calendar", methods=["GET", "POST"])
@login_required
def calendar():
    user = current_user()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Event title is required.", "error")
            return redirect(url_for("app_routes.calendar"))
        event = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "title": title,
            "date": request.form.get("date", today_value()),
            "time": request.form.get("time", ""),
            "type": request.form.get("type", "task"),
            "notes": request.form.get("notes", ""),
            "created_at": store.now(),
        }
        store.add_record("calendar_events", event)
        store.log(user["id"], "calendar", f"Added calendar item: {title}", 1)
        flash("Calendar item added.", "success")
        return redirect(url_for("app_routes.calendar"))

    events = sorted(user_records(user["id"])["calendar_events"], key=lambda item: (item.get("date", ""), item.get("time", "")))
    grouped = defaultdict(list)
    for event in events:
        grouped[event["date"]].append(event)
    return render_template("calendar.html", **page_context(user), grouped=dict(grouped))


@app_routes.route("/calendar/<event_id>/delete", methods=["POST"])
@login_required
def calendar_delete(event_id: str):
    user = current_user()
    event = next((item for item in store.read("calendar_events") if item["id"] == event_id and item["user_id"] == user["id"]), None)
    if event and store.delete_collection_item("calendar_events", event_id):
        store.log(user["id"], "calendar", f"Removed calendar item: {event['title']}", 1)
        flash("Calendar item removed.", "success")
    return redirect(url_for("app_routes.calendar"))


@app_routes.route("/focus", methods=["GET", "POST"])
@login_required
def focus():
    user = current_user()
    if request.method == "POST":
        minutes = safe_int(request.form.get("duration_minutes", "25"), 25)
        session_record = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "duration_minutes": minutes,
            "date": request.form.get("date", today_value()),
            "notes": request.form.get("notes", "").strip(),
            "created_at": store.now(),
        }
        store.add_record("focus", session_record)
        store.log(user["id"], "focus", f"Logged {minutes} minutes of focus.", max(1, minutes // 25))
        flash("Focus session logged.", "success")
        return redirect(url_for("app_routes.focus"))

    sessions = sorted(user_records(user["id"])["focus"], key=lambda item: item.get("date", ""), reverse=True)
    total_minutes = sum(item.get("duration_minutes", 0) for item in sessions)
    return render_template("focus.html", **page_context(user), sessions=sessions, total_minutes=total_minutes)


@app_routes.route("/hobbies", methods=["GET", "POST"])
@login_required
def hobbies():
    user = current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Hobby name is required.", "error")
            return redirect(url_for("app_routes.hobbies"))
        hobby = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "name": name,
            "duration_minutes": safe_int(request.form.get("duration_minutes", "30"), 30),
            "date": request.form.get("date", today_value()),
            "notes": request.form.get("notes", ""),
            "created_at": store.now(),
        }
        store.add_record("hobbies", hobby)
        store.log(user["id"], "hobby", f"Logged hobby time for {name}.", 1)
        flash("Hobby session saved.", "success")
        return redirect(url_for("app_routes.hobbies"))

    hobbies_for_user = sorted(user_records(user["id"])["hobbies"], key=lambda item: item.get("date", ""), reverse=True)
    total_minutes = sum(item.get("duration_minutes", 0) for item in hobbies_for_user)
    return render_template("hobbies.html", **page_context(user), hobbies=hobbies_for_user, total_minutes=total_minutes)


@app_routes.route("/hobbies/<hobby_id>/delete", methods=["POST"])
@login_required
def hobby_delete(hobby_id: str):
    user = current_user()
    hobby = next((item for item in store.read("hobbies") if item["id"] == hobby_id and item["user_id"] == user["id"]), None)
    if hobby and store.delete_collection_item("hobbies", hobby_id):
        store.log(user["id"], "hobby", f"Deleted hobby entry: {hobby['name']}", 1)
        flash("Hobby entry deleted.", "success")
    return redirect(url_for("app_routes.hobbies"))


@app_routes.route("/ai-coach", methods=["GET", "POST"])
@login_required
def ai_coach():
    user = current_user()
    records = user_records(user["id"])
    analytics = user_analytics(user, **records)
    messages = session.get("coach_messages", [])
    examples = [
        "How can I improve productivity?",
        "How to stay focused?",
        "How to manage time?",
    ]
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if message:
            reply = coach_reply(message, analytics, store.read("ai_data"))
            messages.append({"role": "user", "content": message})
            messages.append({"role": "coach", **reply})
            session["coach_messages"] = messages[-20:]
            store.log(user["id"], "coach", "Asked the AI coach for guidance.", 1)
            flash("Coach response ready.", "success")
        return redirect(url_for("app_routes.ai_coach"))
    return render_template(
        "ai_coach.html",
        **page_context(user),
        analytics=analytics,
        messages=messages,
        examples=examples,
        topic_breakdown=topic_breakdown([item for item in messages if item.get("role") == "coach"]),
    )


@app_routes.route("/admin")
@admin_required
def admin_root():
    return redirect(url_for("app_routes.admin_dashboard"))


@app_routes.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    user = current_user()
    users = store.read("users")
    tasks = store.read("tasks")
    focus_items = store.read("focus")
    hobbies_items = store.read("hobbies")
    events = store.read("calendar_events")
    activity_logs = store.read("activity_logs")
    analytics = admin_analytics(users, tasks, focus_items, hobbies_items, events, activity_logs)
    query = request.args.get("q", "").strip().lower()
    filtered_users = [
        item
        for item in analytics["user_rows"]
        if not query or query in item.get("name", "").lower() or query in item.get("email", "").lower()
    ]
    return render_template(
        "admin_dashboard.html",
        **page_context(user),
        analytics=analytics,
        users=filtered_users,
        query=query,
        chart_payload=json.dumps(analytics["chart_payload"]),
    )


@app_routes.route("/admin/users/<user_id>")
@admin_required
def admin_user(user_id: str):
    user = current_user()
    target = store.get_user(user_id)
    if not target:
        flash("User not found.", "error")
        return redirect(url_for("app_routes.admin_dashboard"))
    records = user_records(user_id)
    analytics = user_analytics(target, **records)
    chart_payload = {
        "taskStatus": analytics["task_status_counts"],
        "taskPriority": analytics["task_priority_counts"],
        "dailyFocus": analytics["daily_focus"],
    }
    return render_template(
        "admin/user_detail.html",
        **page_context(user),
        target=target,
        analytics=analytics,
        records=records,
        chart_payload=json.dumps(chart_payload),
    )
