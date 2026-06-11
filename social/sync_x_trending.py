from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "social" / "x-trending-posts.js"
SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

QUERIES = [
    '"World Cup 2026" lang:en -is:retweet',
    '(#WorldCup2026 OR "FIFA World Cup 2026") lang:en -is:retweet',
    '("World Cup" football 2026) lang:en -is:retweet',
    '(Brazil OR Argentina OR France OR England) "World Cup" lang:en -is:retweet',
    '("World Cup prediction" OR "World Cup predictions") lang:en -is:retweet',
]


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def score(metrics: dict) -> int:
    return (
        int(metrics.get("like_count") or 0)
        + int(metrics.get("reply_count") or 0) * 3
        + int(metrics.get("retweet_count") or 0) * 5
        + int(metrics.get("quote_count") or 0) * 4
    )


def fetch_query(token: str, query: str) -> list[dict]:
    params = {
        "query": query,
        "max_results": "25",
        "tweet.fields": "author_id,created_at,public_metrics,lang,possibly_sensitive",
        "expansions": "author_id",
        "user.fields": "username,name,verified,public_metrics",
    }
    url = SEARCH_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    users = {
        user["id"]: user
        for user in payload.get("includes", {}).get("users", [])
    }
    posts = []
    for item in payload.get("data", []):
        if item.get("possibly_sensitive"):
            continue
        metrics = item.get("public_metrics") or {}
        author = users.get(item.get("author_id"), {})
        username = author.get("username", "")
        posts.append(
            {
                "id": item["id"],
                "url": f"https://x.com/{username}/status/{item['id']}" if username else f"https://x.com/i/web/status/{item['id']}",
                "author": author.get("name") or username or "Unknown",
                "username": username,
                "text": item.get("text", ""),
                "createdAt": item.get("created_at", ""),
                "likes": int(metrics.get("like_count") or 0),
                "replies": int(metrics.get("reply_count") or 0),
                "reposts": int(metrics.get("retweet_count") or 0),
                "quotes": int(metrics.get("quote_count") or 0),
                "score": score(metrics),
                "query": query,
            }
        )
    return posts


def dedupe(posts: list[dict]) -> list[dict]:
    seen = {}
    for post in posts:
        current = seen.get(post["id"])
        if current is None or post["score"] > current["score"]:
            seen[post["id"]] = post
    return list(seen.values())


def write_payload(posts: list[dict]) -> None:
    payload = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "X API recent search local sync",
        "notes": "Sorted by like + reply*3 + repost*5 + quote*4. Human review and manual replies only.",
        "posts": posts[:5],
    }
    OUTPUT.write_text(
        "window.X_TRENDING_POSTS = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    token = env("X_BEARER_TOKEN")
    posts: list[dict] = []
    for query in QUERIES:
        posts.extend(fetch_query(token, query))
    ranked = sorted(dedupe(posts), key=lambda item: item["score"], reverse=True)
    write_payload(ranked)
    print(f"Wrote {OUTPUT}")
    print(f"Generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"Posts: {min(5, len(ranked))}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"X trending sync failed: {exc}", file=sys.stderr)
        raise
