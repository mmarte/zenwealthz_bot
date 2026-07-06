import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

POSTS_FILE = Path("posts.json")
STATE_FILE = Path("bot_state.json")

try:
    from groq import Groq
except Exception:  # pragma: no cover - optional dependency
    Groq = None


def load_json(path: Path, default):
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return default
    return default


def save_json(path: Path, data):
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def load_state():
    return load_json(STATE_FILE, {"last_run": None, "posts_generated": 0})


def build_fallback_post() -> dict:
    topics = [
        "A simple budget system can reduce money stress faster than a new income stream.",
        "Wealth is often built by protecting what you already earn, not only by earning more.",
        "The best financial habits are boring, repeatable, and easy to maintain.",
        "Small consistency beats big motivation when it comes to money.",
        "Your money grows when your habits become automatic and predictable.",
        "Financial confidence starts with one calm, repeatable decision at a time.",
    ]
    topic = random.choice(topics)
    return {
        "id": f"zen-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "status": "pending",
        "type": "insight",
        "content": f"{topic}\n\nWhat is one money habit you want to improve this month?",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scheduled_at": datetime.now(timezone.utc).isoformat(),
        "brand": "ZenWealthz",
        "platforms": ["facebook", "x", "instagram"],
    }


def generate_with_groq() -> dict | None:
    if not Groq or not os.getenv("GROQ_API_KEY"):
        return None

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    prompt = (
        "Write one short social media post for a financial education brand called ZenWealthz. "
        "The post should feel encouraging, practical, and concise. It should include one question "
        "at the end to invite engagement. Return only the post text."
    )
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=180,
        )
        text = response.choices[0].message.content.strip()
        if text:
            return {
                "id": f"zen-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "status": "pending",
                "type": "ai_generated",
                "content": text,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "scheduled_at": datetime.now(timezone.utc).isoformat(),
                "brand": "ZenWealthz",
                "platforms": ["facebook", "x", "instagram"],
            }
    except Exception as exc:
        print(f"Groq generation failed: {exc}")
    return None


def ensure_queue():
    posts = load_json(POSTS_FILE, [])
    if not isinstance(posts, list):
        posts = []

    pending_posts = [post for post in posts if post.get("status") == "pending"]
    if pending_posts:
        return posts

    post = generate_with_groq() or build_fallback_post()
    posts.append(post)
    save_json(POSTS_FILE, posts)

    state = load_state()
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["posts_generated"] = int(state.get("posts_generated", 0)) + 1
    save_json(STATE_FILE, state)
    return posts


if __name__ == "__main__":
    posts = ensure_queue()
    print(f"Queued {len(posts)} posts. Latest: {posts[-1].get('content', '')[:120]}")
