from __future__ import annotations

from collections import Counter


def default_ai_entries() -> list[dict]:
    seed_topics = {
        "focus": ["How do I focus better?", "I keep getting distracted", "How long should I study?", "How can I improve deep work?"],
        "tasks": ["How do I finish tasks on time?", "I am behind on my to-do list", "How should I prioritize work?", "I keep postponing difficult tasks"],
        "motivation": ["I feel unmotivated today", "How do I stay consistent?", "I broke my streak", "How do I reset after a bad day?"],
        "balance": ["Are hobbies productive?", "How do I avoid burnout?", "Should I take breaks?", "How do I balance study and rest?"],
    }
    responses = {
        "focus": "Protect one clear block, silence distractions, and aim for a single measurable outcome before you stop.",
        "tasks": "Pick one high-impact task, define the next concrete step, and finish that before reorganizing your list.",
        "motivation": "Lower the bar for starting, keep the session short, and let momentum rebuild from action instead of mood.",
        "balance": "Sustainable productivity includes recovery. Short breaks and hobbies help your long-term output stay strong.",
    }
    entries = []
    counter = 1
    for topic, prompts in seed_topics.items():
        for prompt in prompts:
            for variant in range(55):
                entries.append(
                    {
                        "id": f"qa-{counter}",
                        "topic": topic,
                        "keywords": [topic, prompt.split()[0].lower(), f"variant-{variant % 5}"],
                        "question": f"{prompt} #{variant + 1}",
                        "answer": responses[topic],
                    }
                )
                counter += 1
    return entries


def coach_reply(message: str, analytics: dict, ai_entries: list[dict]) -> dict:
    lowered = message.lower()
    scored = []
    for entry in ai_entries:
        hits = sum(1 for keyword in entry.get("keywords", []) if keyword.lower() in lowered)
        if entry.get("topic", "") in lowered:
            hits += 2
        if hits:
            scored.append((hits, entry))
    scored.sort(key=lambda item: item[0], reverse=True)
    best = scored[0][1] if scored else None

    score = analytics["score"]
    if score >= 80:
        stat_line = "You are operating in a strong range right now. The goal is consistency, not squeezing harder."
    elif score >= 55:
        stat_line = "Your momentum is decent, but one cleaner focus block or one more completed task would lift the week noticeably."
    else:
        stat_line = "Your activity suggests a reset day: finish one small task, log one focused session, and rebuild from there."

    habit_line = (
        f"Current snapshot: {analytics['completed_tasks']} completed tasks, {analytics['focus_minutes']} focus minutes, "
        f"{analytics['hobby_minutes']} hobby minutes, and a {analytics['completion_rate']}% completion rate."
    )
    if best:
        answer = f"{best['answer']} {stat_line} {habit_line}"
        matched = best["topic"]
    else:
        answer = (
            "I did not find a direct match, so here is the practical move: choose one priority task, schedule a focused block, "
            "and protect a short recovery window after it. "
            f"{stat_line} {habit_line}"
        )
        matched = "fallback"

    return {
        "answer": answer,
        "matched_topic": matched,
        "actions": [
            "Finish one in-progress task before adding another.",
            "Schedule a 25 to 50 minute focus block with a single goal.",
            "Use a hobby or break as recovery after work, not as avoidance before it.",
        ],
    }


def topic_breakdown(messages: list[dict]) -> dict[str, int]:
    return dict(Counter(item.get("matched_topic", "fallback") for item in messages))
