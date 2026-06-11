from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "social" / "x-trending-manual.json"
OUTPUT = ROOT / "social" / "x-trending-posts.js"


def score(post: dict) -> int:
    return (
        int(post.get("likes") or 0)
        + int(post.get("replies") or 0) * 3
        + int(post.get("reposts") or 0) * 5
        + int(post.get("quotes") or 0) * 4
    )


def main() -> None:
    posts = json.loads(INPUT.read_text(encoding="utf-8"))
    cleaned = []
    for post in posts:
        if not post.get("url") or "example/status" in post.get("url", ""):
            continue
        item = {
            "url": post.get("url", ""),
            "author": post.get("author") or post.get("username") or "X post",
            "username": post.get("username", ""),
            "text": post.get("text", ""),
            "createdAt": post.get("createdAt", ""),
            "likes": int(post.get("likes") or 0),
            "replies": int(post.get("replies") or 0),
            "reposts": int(post.get("reposts") or 0),
            "quotes": int(post.get("quotes") or 0),
        }
        item["score"] = score(item)
        cleaned.append(item)

    ranked = sorted(cleaned, key=lambda item: item["score"], reverse=True)[:5]
    payload = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Manual X post import",
        "notes": "Sorted by like + reply*3 + repost*5 + quote*4. Human review and manual replies only.",
        "posts": ranked,
    }
    OUTPUT.write_text(
        "window.X_TRENDING_POSTS = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT}")
    print(f"Posts: {len(ranked)}")


if __name__ == "__main__":
    main()
