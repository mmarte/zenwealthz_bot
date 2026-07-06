import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

POSTS_FILE = Path("posts.json")
LOG_FILE = Path("log.json")


def load_json(path: Path, default):
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return default
    return default


if __name__ == "__main__":
    posts = load_json(POSTS_FILE, [])
    logs = load_json(LOG_FILE, [])
    pending = sum(1 for post in posts if post.get("status") == "pending")
    published = sum(1 for entry in logs if entry.get("status") == "published")
    print(f"ZenWealthz Bot report")
    print(f"Pending posts: {pending}")
    print(f"Published posts: {published}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
