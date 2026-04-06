from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta


def safe_date(value: str):
    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        return None


def productivity_score(tasks: list[dict], focus: list[dict], hobbies: list[dict]) -> int:
    completed = sum(1 for task in tasks if task.get("status") == "completed")
    focus_minutes = sum(int(item.get("duration_minutes", 0)) for item in focus)
    hobby_minutes = sum(int(item.get("duration_minutes", 0)) for item in hobbies)
    return int(min(100, completed * 8 + min(40, focus_minutes // 6) + min(20, hobby_minutes // 15)))


def build_heatmap(activity_logs: list[dict], days: int = 140) -> list[dict]:
    today = date.today()
    buckets = defaultdict(int)
    for item in activity_logs:
        buckets[item.get("date", "")] += int(item.get("value", 0) or 0)
    cells = []
    for offset in range(days - 1, -1, -1):
        current = today - timedelta(days=offset)
        amount = buckets.get(current.isoformat(), 0)
        level = 0 if amount == 0 else 1 if amount < 2 else 2 if amount < 4 else 3 if amount < 7 else 4
        cells.append({"date": current.isoformat(), "value": amount, "level": level})
    return cells


def user_analytics(user: dict, tasks: list[dict], focus: list[dict], hobbies: list[dict], calendar_events: list[dict], activity_logs: list[dict]) -> dict:
    completed_tasks = sum(1 for task in tasks if task.get("status") == "completed")
    total_tasks = len(tasks)
    focus_minutes = sum(int(item.get("duration_minutes", 0)) for item in focus)
    hobby_minutes = sum(int(item.get("duration_minutes", 0)) for item in hobbies)
    completion_rate = int((completed_tasks / total_tasks) * 100) if total_tasks else 0
    score = productivity_score(tasks, focus, hobbies)
    status_counts = Counter(task.get("status", "pending") for task in tasks)
    priority_counts = Counter(task.get("priority", "medium") for task in tasks)
    daily_focus = defaultdict(int)
    for item in focus:
        daily_focus[item.get("date", "")] += int(item.get("duration_minutes", 0))

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
        "completion_rate": completion_rate,
        "task_status_counts": dict(status_counts),
        "task_priority_counts": dict(priority_counts),
        "daily_focus": dict(sorted(daily_focus.items())),
        "heatmap": build_heatmap(activity_logs),
        "recent_activity": sorted(activity_logs, key=lambda item: item.get("timestamp", ""), reverse=True)[:12],
        "next_event": upcoming[0] if upcoming else None,
        "upcoming_count": len(upcoming),
    }


def admin_analytics(users: list[dict], tasks: list[dict], focus: list[dict], hobbies: list[dict], calendar_events: list[dict], activity_logs: list[dict]) -> dict:
    leaderboard = []
    for user in users:
        if user.get("role") == "admin":
            continue
        user_id = user["id"]
        details = user_analytics(
            user,
            [item for item in tasks if item.get("user_id") == user_id],
            [item for item in focus if item.get("user_id") == user_id],
            [item for item in hobbies if item.get("user_id") == user_id],
            [item for item in calendar_events if item.get("user_id") == user_id],
            [item for item in activity_logs if item.get("user_id") == user_id],
        )
        leaderboard.append(
            {
                "id": user_id,
                "name": user.get("username", user.get("email")),
                "email": user.get("email", ""),
                "score": details["score"],
                "focus_minutes": details["focus_minutes"],
                "completed_tasks": details["completed_tasks"],
                "completion_rate": details["completion_rate"],
                "activity_count": len([item for item in activity_logs if item.get("user_id") == user_id]),
            }
        )
    leaderboard.sort(key=lambda item: (item["score"], item["focus_minutes"], item["completed_tasks"]), reverse=True)
    most_active = sorted(leaderboard, key=lambda item: item["activity_count"], reverse=True)[:10]
    task_rankings = sorted(leaderboard, key=lambda item: item["completion_rate"], reverse=True)[:10]
    focus_rankings = sorted(leaderboard, key=lambda item: item["focus_minutes"], reverse=True)[:10]
    return {
        "user_count": len([user for user in users if user.get("role") != "admin"]),
        "average_focus": int(sum(item["focus_minutes"] for item in leaderboard) / len(leaderboard)) if leaderboard else 0,
        "average_score": int(sum(item["score"] for item in leaderboard) / len(leaderboard)) if leaderboard else 0,
        "average_completed_tasks": int(sum(item["completed_tasks"] for item in leaderboard) / len(leaderboard)) if leaderboard else 0,
        "leaderboard": leaderboard[:10],
        "most_active": most_active,
        "task_rankings": task_rankings,
        "focus_rankings": focus_rankings,
        "chart_payload": {
            "topProductive": {
                "labels": [item["name"] for item in leaderboard[:8]],
                "values": [item["score"] for item in leaderboard[:8]],
            },
            "mostActive": {
                "labels": [item["name"] for item in most_active[:8]],
                "values": [item["activity_count"] for item in most_active[:8]],
            },
            "taskCompletion": {
                "labels": [item["name"] for item in task_rankings[:8]],
                "values": [item["completion_rate"] for item in task_rankings[:8]],
            },
            "focusComparison": {
                "labels": [item["name"] for item in focus_rankings[:8]],
                "values": [item["focus_minutes"] for item in focus_rankings[:8]],
            },
        },
    }
