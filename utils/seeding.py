from __future__ import annotations

import random
import uuid
from datetime import date, timedelta

from config import DEMO_USER_COUNT


FIRST_NAMES = ["Ava", "Liam", "Noah", "Mia", "Ivy", "Aria", "Ethan", "Sara", "Leo", "Nina"]
LAST_NAMES = ["Shah", "Patel", "Khan", "Rao", "Das", "Verma", "Ali", "Jain", "Kapoor", "Singh"]
TASK_TITLES = [
    "Finish assignment",
    "Review notes",
    "Plan tomorrow",
    "Ship feature",
    "Read research paper",
    "Clean inbox",
    "Practice coding",
    "Prepare presentation",
]
HOBBIES = ["Reading", "Music", "Workout", "Painting", "Gaming", "Cycling", "Cooking", "Chess"]


def seed_demo_data(store, count: int = DEMO_USER_COUNT, reset: bool = False) -> None:
    random.seed(42)
    users = store.read("users")
    admin_user = next(user for user in users if user["role"] == "admin")
    if not reset and len(users) - 1 >= count:
        return

    users = [admin_user]
    tasks = []
    focus = []
    hobbies = []
    events = []
    activity_logs = []

    for index in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        username = f"{first.lower()}{last.lower()}{index}"
        user_id = str(uuid.uuid4())
        users.append(
            {
                "id": user_id,
                "username": username,
                "email": f"{username}@example.com",
                "password_hash": admin_user["password_hash"],
                "role": "user",
                "theme": random.choice(["light", "dark"]),
                "created_at": (date.today() - timedelta(days=random.randint(10, 300))).isoformat(),
            }
        )

        for _ in range(random.randint(6, 18)):
            task_date = date.today() - timedelta(days=random.randint(0, 50))
            title = random.choice(TASK_TITLES)
            status = random.choices(["completed", "in_progress", "pending"], weights=[0.5, 0.2, 0.3])[0]
            tasks.append(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "title": title,
                    "priority": random.choice(["low", "medium", "high"]),
                    "difficulty": random.choice(["easy", "medium", "hard"]),
                    "due_date": (task_date + timedelta(days=random.randint(0, 10))).isoformat(),
                    "status": status,
                    "created_at": task_date.isoformat(),
                }
            )
            activity_logs.append(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "category": "task",
                    "description": f"{status} task: {title}",
                    "value": 2 if status == "completed" else 1,
                    "date": task_date.isoformat(),
                    "timestamp": f"{task_date.isoformat()}T09:00:00",
                }
            )

        for _ in range(random.randint(4, 14)):
            focus_date = date.today() - timedelta(days=random.randint(0, 45))
            minutes = random.choice([25, 30, 45, 50, 60, 75, 90])
            focus.append(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "duration_minutes": minutes,
                    "date": focus_date.isoformat(),
                    "notes": random.choice(["Deep work", "Study", "Revision", "Project sprint"]),
                    "created_at": focus_date.isoformat(),
                }
            )
            activity_logs.append(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "category": "focus",
                    "description": f"Logged {minutes} focus minutes",
                    "value": max(1, minutes // 25),
                    "date": focus_date.isoformat(),
                    "timestamp": f"{focus_date.isoformat()}T11:00:00",
                }
            )

        for _ in range(random.randint(3, 10)):
            hobby_date = date.today() - timedelta(days=random.randint(0, 45))
            name = random.choice(HOBBIES)
            minutes = random.choice([20, 30, 45, 60, 90])
            hobbies.append(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "name": name,
                    "duration_minutes": minutes,
                    "date": hobby_date.isoformat(),
                    "notes": random.choice(["Recovery", "Routine", "Fun session", "Practice"]),
                    "created_at": hobby_date.isoformat(),
                }
            )
            activity_logs.append(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "category": "hobby",
                    "description": f"Logged {name} for {minutes} minutes",
                    "value": 1,
                    "date": hobby_date.isoformat(),
                    "timestamp": f"{hobby_date.isoformat()}T18:30:00",
                }
            )

        for _ in range(random.randint(2, 8)):
            event_date = date.today() + timedelta(days=random.randint(-5, 20))
            events.append(
                {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "title": random.choice(["Sprint review", "Study plan", "Workout block", "Project milestone"]),
                    "date": event_date.isoformat(),
                    "time": random.choice(["08:30", "10:00", "14:00", "18:00"]),
                    "type": random.choice(["task", "focus", "hobby", "meeting"]),
                    "notes": "Seeded event",
                    "created_at": event_date.isoformat(),
                }
            )

    store.write("users", users)
    store.write("tasks", tasks)
    store.write("focus", focus)
    store.write("hobbies", hobbies)
    store.write("calendar_events", events)
    store.write("activity_logs", activity_logs)
