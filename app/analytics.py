from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta


def safe_date(value: str):
    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        return None


def to_int(value, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def score_from_totals(completed_tasks: int, focus_minutes: int, hobby_minutes: int) -> float:
    return round((completed_tasks * 2) + (focus_minutes * 0.5) + (hobby_minutes * 0.2), 1)


def productivity_score(tasks: list[dict], focus: list[dict], hobbies: list[dict]) -> float:
    completed = sum(1 for task in tasks if task.get("status") == "completed")
    focus_minutes = sum(to_int(item.get("duration_minutes")) for item in focus)
    hobby_minutes = sum(to_int(item.get("duration_minutes")) for item in hobbies)
    return score_from_totals(completed, focus_minutes, hobby_minutes)


def build_heatmap(activity_logs: list[dict], days: int = 140) -> list[dict]:
    today = date.today()
    buckets = defaultdict(int)
    for item in activity_logs:
        buckets[item.get("date", "")] += to_int(item.get("value"))
    cells = []
    for offset in range(days - 1, -1, -1):
        current = today - timedelta(days=offset)
        amount = buckets.get(current.isoformat(), 0)
        level = 0 if amount == 0 else 1 if amount < 2 else 2 if amount < 4 else 3 if amount < 7 else 4
        cells.append({"date": current.isoformat(), "value": amount, "level": level})
    return cells


def user_analytics(
    user: dict,
    tasks: list[dict],
    focus: list[dict],
    hobbies: list[dict],
    calendar_events: list[dict],
    activity_logs: list[dict],
) -> dict:
    completed_tasks = sum(1 for task in tasks if task.get("status") == "completed")
    total_tasks = len(tasks)
    focus_minutes = sum(to_int(item.get("duration_minutes")) for item in focus)
    hobby_minutes = sum(to_int(item.get("duration_minutes")) for item in hobbies)
    completion_rate = round((completed_tasks / total_tasks) * 100, 1) if total_tasks else 0
    average_focus_minutes = round(focus_minutes / len(focus), 1) if focus else 0
    score = productivity_score(tasks, focus, hobbies)
    status_counts = Counter(task.get("status", "pending") for task in tasks)
    priority_counts = Counter(task.get("priority", "medium") for task in tasks)
    daily_focus = defaultdict(int)
    for item in focus:
        daily_focus[item.get("date", "")] += to_int(item.get("duration_minutes"))

    upcoming = sorted(
        [event for event in calendar_events if safe_date(event.get("date", "")) and safe_date(event["date"]) >= date.today()],
        key=lambda item: (item["date"], item.get("time", "23:59")),
    )
    return {
        "user": user,
        "score": score,
        "completed_tasks": completed_tasks,
        "total_tasks": total_tasks,
        "focus_minutes": focus_minutes,
        "hobby_minutes": hobby_minutes,
        "average_focus_minutes": average_focus_minutes,
        "completion_rate": completion_rate,
        "task_status_counts": dict(status_counts),
        "task_priority_counts": dict(priority_counts),
        "daily_focus": dict(sorted(daily_focus.items())),
        "heatmap": build_heatmap(activity_logs),
        "recent_activity": sorted(activity_logs, key=lambda item: item.get("timestamp", ""), reverse=True)[:12],
        "next_event": upcoming[0] if upcoming else None,
        "upcoming_count": len(upcoming),
    }


def admin_analytics(
    users: list[dict],
    tasks: list[dict],
    focus: list[dict],
    hobbies: list[dict],
    calendar_events: list[dict],
    activity_logs: list[dict],
) -> dict:
    user_tasks = defaultdict(list)
    user_focus = defaultdict(list)
    user_hobbies = defaultdict(list)
    user_events = defaultdict(list)
    user_logs = defaultdict(list)

    for item in tasks:
        user_tasks[item.get("user_id")].append(item)
    for item in focus:
        user_focus[item.get("user_id")].append(item)
    for item in hobbies:
        user_hobbies[item.get("user_id")].append(item)
    for item in calendar_events:
        user_events[item.get("user_id")].append(item)
    for item in activity_logs:
        user_logs[item.get("user_id")].append(item)

    members = [user for user in users if user.get("role") != "admin"]
    member_ids = {user["id"] for user in members}
    seven_days_ago = date.today() - timedelta(days=6)

    user_rows = []
    for user in members:
        user_id = user["id"]
        details = user_analytics(
            user,
            user_tasks[user_id],
            user_focus[user_id],
            user_hobbies[user_id],
            user_events[user_id],
            user_logs[user_id],
        )
        logs = user_logs[user_id]
        activity_days = len({item.get("date") for item in logs if item.get("date")})
        recent_active = any((safe_date(item.get("date", "")) or date.min) >= seven_days_ago for item in logs)
        user_rows.append(
            {
                "id": user_id,
                "name": user.get("username", user.get("email", "User")),
                "email": user.get("email", ""),
                "score": details["score"],
                "completed_tasks": details["completed_tasks"],
                "total_tasks": details["total_tasks"],
                "completion_rate": details["completion_rate"],
                "focus_minutes": details["focus_minutes"],
                "average_focus_minutes": details["average_focus_minutes"],
                "hobby_minutes": details["hobby_minutes"],
                "activity_count": len(logs),
                "activity_days": activity_days,
                "is_active": recent_active,
            }
        )

    top_productive = sorted(
        user_rows,
        key=lambda item: (item["score"], item["completed_tasks"], item["focus_minutes"]),
        reverse=True,
    )[:10]
    top_active = sorted(
        user_rows,
        key=lambda item: (item["activity_count"], item["activity_days"], item["score"]),
        reverse=True,
    )[:10]
    top_completion = sorted(
        user_rows,
        key=lambda item: (item["completion_rate"], item["completed_tasks"], item["score"]),
        reverse=True,
    )[:10]
    top_average_focus = sorted(
        user_rows,
        key=lambda item: (item["average_focus_minutes"], item["focus_minutes"], item["score"]),
        reverse=True,
    )[:10]

    daily_active_map = defaultdict(set)
    for item in activity_logs:
        if item.get("user_id") in member_ids and item.get("date"):
            current = safe_date(item["date"])
            if current and current >= date.today() - timedelta(days=13):
                daily_active_map[item["date"]].add(item["user_id"])

    daily_active_users = []
    for offset in range(13, -1, -1):
        current = date.today() - timedelta(days=offset)
        key = current.isoformat()
        daily_active_users.append({"label": current.strftime("%d %b"), "value": len(daily_active_map.get(key, set()))})

    weekly_map = {}
    for weeks_back in range(7, -1, -1):
        current_week = date.today() - timedelta(days=date.today().weekday()) - timedelta(weeks=weeks_back)
        weekly_map[current_week] = 0.0

    def add_weekly_score(raw_date: str, value: float) -> None:
        current = safe_date(raw_date)
        if not current:
            return
        week_start = current - timedelta(days=current.weekday())
        if week_start in weekly_map:
            weekly_map[week_start] += value

    for item in tasks:
        if item.get("status") == "completed":
            add_weekly_score(item.get("created_at", ""), 2)
    for item in focus:
        add_weekly_score(item.get("date", ""), to_int(item.get("duration_minutes")) * 0.5)
    for item in hobbies:
        add_weekly_score(item.get("date", ""), to_int(item.get("duration_minutes")) * 0.2)

    weekly_productivity = [
        {"label": week.strftime("%d %b"), "value": round(score, 1)}
        for week, score in sorted(weekly_map.items())
    ]

    priority_counts = Counter(item.get("priority", "medium").title() for item in tasks if item.get("user_id") in member_ids)

    chart_payload = {
        "topProductive": {
            "labels": [item["name"] for item in top_productive],
            "values": [item["score"] for item in top_productive],
        },
        "topActive": {
            "labels": [item["name"] for item in top_active],
            "values": [item["activity_count"] for item in top_active],
        },
        "completionRate": {
            "labels": [item["name"] for item in top_completion],
            "values": [item["completion_rate"] for item in top_completion],
        },
        "averageFocus": {
            "labels": [item["name"] for item in top_average_focus],
            "values": [item["average_focus_minutes"] for item in top_average_focus],
        },
        "dailyActiveUsers": {
            "labels": [item["label"] for item in daily_active_users],
            "values": [item["value"] for item in daily_active_users],
        },
        "weeklyProductivity": {
            "labels": [item["label"] for item in weekly_productivity],
            "values": [item["value"] for item in weekly_productivity],
        },
        "taskPriorities": {
            "labels": list(priority_counts.keys()),
            "values": list(priority_counts.values()),
        },
    }

    return {
        "total_users": len(members),
        "active_users": sum(1 for item in user_rows if item["is_active"]),
        "total_tasks": len([item for item in tasks if item.get("user_id") in member_ids]),
        "total_focus_minutes": sum(to_int(item.get("duration_minutes")) for item in focus if item.get("user_id") in member_ids),
        "average_score": round(sum(item["score"] for item in user_rows) / len(user_rows), 1) if user_rows else 0,
        "average_focus_minutes": round(
            sum(item["average_focus_minutes"] for item in user_rows) / len(user_rows), 1
        ) if user_rows else 0,
        "top_productive": top_productive,
        "top_active": top_active,
        "top_completion": top_completion,
        "top_average_focus": top_average_focus,
        "user_rows": sorted(user_rows, key=lambda item: (item["score"], item["activity_count"]), reverse=True),
        "chart_payload": chart_payload,
    }
