import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

POSTS_FILE = Path("posts.json")
LOG_FILE = Path("log.json")
GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v25.0")


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


def build_message(post: dict, platform: str) -> str:
    base = (post.get("content", "") or "").strip()
    if platform == "x":
        trimmed = base[:240].strip()
    else:
        trimmed = base[:2200].strip()
    return f"{trimmed}\n\n#ZenWealthz #WealthWisdom"


def publish_to_facebook(post: dict, message: str):
    page_id = os.getenv("FB_PAGE_ID", "").strip()
    page_token = os.getenv("FB_PAGE_TOKEN", "").strip()
    if not page_id or not page_token:
        return {"status": "skipped", "error": "Missing FB_PAGE_ID or FB_PAGE_TOKEN"}

    payload = {"message": message, "access_token": page_token}
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{page_id}/feed"
    try:
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return {"status": "published", "platform": "facebook", "post_id": data.get("id")}
    except Exception as exc:
        return {"status": "failed", "platform": "facebook", "error": str(exc)}


def publish_to_x(post: dict, message: str):
    x_bearer_token = os.getenv("X_BEARER_TOKEN", "").strip()
    if not x_bearer_token:
        return {"status": "skipped", "platform": "x", "error": "Missing X_BEARER_TOKEN"}

    headers = {
        "Authorization": f"Bearer {x_bearer_token}",
        "Content-Type": "application/json",
    }
    payload = {"text": message[:280]}
    try:
        response = requests.post("https://api.x.com/2/tweets", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return {"status": "published", "platform": "x", "post_id": data.get("data", {}).get("id")}
    except Exception as exc:
        return {"status": "failed", "platform": "x", "error": str(exc)}


def fetch_pexels_image_url():
    pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not pexels_key:
        return None
    try:
        response = requests.get(
            "https://api.pexels.com/v1/search?query=finance%20success&per_page=1",
            headers={"Authorization": pexels_key},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        photos = data.get("photos", [])
        if photos:
            return photos[0].get("src", {}).get("original")
    except Exception:
        return None
    return None


def publish_to_instagram(post: dict, message: str):
    ig_user_id = os.getenv("IG_USER_ID", "").strip()
    ig_access_token = os.getenv("IG_ACCESS_TOKEN", "").strip()
    if not ig_user_id or not ig_access_token:
        return {"status": "skipped", "platform": "instagram", "error": "Missing IG_USER_ID or IG_ACCESS_TOKEN"}

    image_url = os.getenv("IG_MEDIA_URL", "").strip() or fetch_pexels_image_url()
    if not image_url:
        return {"status": "skipped", "platform": "instagram", "error": "No image URL available"}

    container_payload = {
        "image_url": image_url,
        "caption": message[:2200],
        "access_token": ig_access_token,
    }
    try:
        container_response = requests.post(
            f"https://graph.facebook.com/{GRAPH_VERSION}/{ig_user_id}/media",
            data=container_payload,
            timeout=60,
        )
        container_response.raise_for_status()
        container_data = container_response.json()
        creation_id = container_data.get("id")
        if not creation_id:
            return {"status": "failed", "platform": "instagram", "error": container_data}

        publish_response = requests.post(
            f"https://graph.facebook.com/{GRAPH_VERSION}/{creation_id}",
            data={"access_token": ig_access_token},
            timeout=60,
        )
        publish_response.raise_for_status()
        publish_data = publish_response.json()
        return {"status": "published", "platform": "instagram", "post_id": publish_data.get("id")}
    except Exception as exc:
        return {"status": "failed", "platform": "instagram", "error": str(exc)}


def publish_post(post: dict):
    message = build_message(post, "facebook")
    platform_results = {
        "facebook": publish_to_facebook(post, message),
        "x": publish_to_x(post, message),
        "instagram": publish_to_instagram(post, message),
    }

    statuses = [result.get("status") for result in platform_results.values()]
    if any(status == "published" for status in statuses):
        overall_status = "published"
    elif any(status == "failed" for status in statuses):
        overall_status = "failed"
    else:
        overall_status = "skipped"

    return {
        "status": overall_status,
        "post_id": post.get("id"),
        "platforms": platform_results,
    }


if __name__ == "__main__":
    posts = load_json(POSTS_FILE, [])
    if not isinstance(posts, list):
        posts = []

    pending = [post for post in posts if post.get("status") == "pending"]
    if not pending:
        print("No pending posts to publish.")
        raise SystemExit(0)

    post = pending[0]
    result = publish_post(post)
    result["executed_at"] = datetime.now(timezone.utc).isoformat()

    post["status"] = result["status"]
    post["pub_result"] = result
    save_json(POSTS_FILE, posts)

    logs = load_json(LOG_FILE, [])
    if not isinstance(logs, list):
        logs = []
    logs.append(result)
    save_json(LOG_FILE, logs)

    print(json.dumps(result, indent=2))
