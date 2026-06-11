from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "admin" / "growth-data.js"
GRAPHQL_URL = "https://api.cloudflare.com/client/v4/graphql"


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing environment variable: {name}")
    return value


def graphql(token: str, query: str, variables: dict) -> dict:
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"], ensure_ascii=False, indent=2))
    return result["data"]


def first_zone(data: dict, field: str) -> list[dict]:
    zones = data.get("viewer", {}).get("zones", [])
    if not zones:
        raise RuntimeError("Cloudflare returned no zone data. Check CLOUDFLARE_ZONE_ID and token permissions.")
    return zones[0].get(field, [])


def sum_metric(rows: list[dict], key: str) -> int:
    return int(sum((row.get("sum") or {}).get(key, 0) or 0 for row in rows))


def uniq_metric(rows: list[dict], key: str) -> int:
    return int(sum((row.get("uniq") or {}).get(key, 0) or 0 for row in rows))


def ranked(rows: list[dict], label_fn, value_fn, limit: int = 8) -> list[dict]:
    buckets: dict[str, int] = {}
    for row in rows:
        label = label_fn(row) or "Unknown"
        buckets[label] = buckets.get(label, 0) + int(value_fn(row) or 0)
    return [
        {"name": name, "value": value}
        for name, value in sorted(buckets.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]


def page_name(path: str | None) -> str:
    if not path or path == "/":
        return "Homepage"
    first = path.strip("/").split("/")[0]
    names = {
        "schedule": "Schedule",
        "teams": "Teams",
        "predictions": "Predictions",
        "game": "Game",
        "admin": "Admin",
    }
    return names.get(first, f"/{path.strip('/')}")


def is_content_page(path: str | None) -> bool:
    if not path:
        return True
    clean = path.lower().split("?")[0]
    if clean == "/" or clean.endswith("/"):
        return True
    ignored_prefixes = (
        "/assets/",
        "/cdn-cgi/",
        "/images/",
        "/social/",
        "/admin/",
        "/favicon",
    )
    ignored_suffixes = (
        ".js",
        ".css",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".svg",
        ".ico",
        ".json",
        ".map",
        ".woff",
        ".woff2",
        ".ttf",
    )
    return not clean.startswith(ignored_prefixes) and not clean.endswith(ignored_suffixes)


def referrer_name(host: str | None) -> str:
    if not host:
        return "Direct"
    host = host.lower()
    if "google" in host:
        return "Google"
    if "twitter" in host or host == "t.co" or "x.com" in host:
        return "X"
    if "facebook" in host or "fb." in host:
        return "Facebook"
    if "discord" in host:
        return "Discord"
    if "telegram" in host or host == "t.me":
        return "Telegram"
    return host


def pct_change(current: int, previous: int) -> int:
    if previous <= 0:
        return 0
    return round(((current - previous) / previous) * 100)


def hourly_user_series(rows: list[dict]) -> list[dict]:
    buckets: dict[str, int] = {}
    for row in rows:
        raw = (row.get("dimensions") or {}).get("datetime")
        if not raw:
            continue
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        bucket = dt.replace(minute=0, second=0, microsecond=0)
        label = bucket.strftime("%H:00")
        buckets[label] = buckets.get(label, 0) + int((row.get("uniq") or {}).get("uniques") or 0)
    return [{"time": label, "users": value} for label, value in sorted(buckets.items())][-12:]


def daily_user_series(rows: list[dict]) -> list[dict]:
    buckets: dict[str, int] = {}
    for row in rows:
        raw = (row.get("dimensions") or {}).get("datetime")
        if not raw:
            continue
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        label = dt.strftime("%m/%d")
        buckets[label] = buckets.get(label, 0) + int((row.get("uniq") or {}).get("uniques") or 0)
    return [{"date": label, "users": value} for label, value in sorted(buckets.items())][-7:]


def fetch_cloudflare_growth_data() -> dict:
    zone_id = env("CLOUDFLARE_ZONE_ID")
    token = env("CLOUDFLARE_API_TOKEN")
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=24)
    previous_start = start - timedelta(hours=24)
    week_start = now - timedelta(days=7)

    hourly_query = """
    query ZoneTraffic($zoneTag: string!, $start: Time!, $end: Time!) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          httpRequests1hGroups(
            limit: 1000,
            filter: {datetime_geq: $start, datetime_lt: $end}
          ) {
            dimensions { datetime }
            sum { requests bytes cachedRequests }
            uniq { uniques }
          }
        }
      }
    }
    """

    breakdown_query = """
    query ZoneBreakdowns($zoneTag: string!, $start: Time!, $end: Time!) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          pages: httpRequestsAdaptiveGroups(
            limit: 1000,
            filter: {datetime_geq: $start, datetime_lt: $end}
          ) {
            dimensions { clientRequestPath }
            count
          }
          countries: httpRequestsAdaptiveGroups(
            limit: 1000,
            filter: {datetime_geq: $start, datetime_lt: $end}
          ) {
            dimensions { clientCountryName }
            count
          }
        }
      }
    }
    """

    current = graphql(token, hourly_query, {"zoneTag": zone_id, "start": iso(start), "end": iso(now)})
    previous = graphql(token, hourly_query, {"zoneTag": zone_id, "start": iso(previous_start), "end": iso(start)})
    weekly = graphql(token, hourly_query, {"zoneTag": zone_id, "start": iso(week_start), "end": iso(now)})
    breakdown = graphql(token, breakdown_query, {"zoneTag": zone_id, "start": iso(start), "end": iso(now)})

    current_rows = first_zone(current, "httpRequests1hGroups")
    previous_rows = first_zone(previous, "httpRequests1hGroups")
    weekly_rows = first_zone(weekly, "httpRequests1hGroups")
    zones = breakdown.get("viewer", {}).get("zones", [])
    if not zones:
        raise RuntimeError("Cloudflare returned no breakdown data.")
    zone = zones[0]

    page_views = sum_metric(current_rows, "requests")
    previous_page_views = sum_metric(previous_rows, "requests")
    users = uniq_metric(current_rows, "uniques")

    page_rows = [
        row for row in zone.get("pages", [])
        if is_content_page((row.get("dimensions") or {}).get("clientRequestPath"))
    ]

    top_pages = ranked(
        page_rows,
        lambda row: page_name((row.get("dimensions") or {}).get("clientRequestPath")),
        lambda row: row.get("count"),
    )
    countries = ranked(
        zone.get("countries", []),
        lambda row: (row.get("dimensions") or {}).get("clientCountryName"),
        lambda row: row.get("count"),
    )
    referrers = [{"name": "Cloudflare 未提供 Referrer", "value": page_views}]

    return {
        "generatedAt": iso(now),
        "source": "Cloudflare Analytics local sync",
        "notes": "Generated by admin/sync_cloudflare.py. Token stays in local environment variables, not in the browser.",
        "traffic": {
            "users": users,
            "sessions": page_views,
            "pageViews": page_views,
            "returningVisitors": max(0, page_views - users),
            "trafficGrowthPct": pct_change(page_views, previous_page_views),
            "engagementGrowthPct": 0,
            "followersDelta": 0,
        },
        "hourlyUsers": hourly_user_series(current_rows),
        "dailyUsers": daily_user_series(weekly_rows),
        "topPages": [
            {
                "page": item["name"],
                "path": "/" if item["name"] == "Homepage" else item["name"],
                "views": item["value"],
                "avgTimeSec": 0,
                "improvement": "Cloudflare request data imported. Add manual qualitative note if this page needs work.",
            }
            for item in top_pages
        ],
        "countries": [
            {"country": item["name"], "sessions": item["value"], "engagement": 0}
            for item in countries
        ],
        "referrers": [
            {"source": item["name"], "sessions": item["value"]}
            for item in referrers
        ],
        "posts": [],
    }


def write_growth_data(payload: dict) -> None:
    OUTPUT.write_text(
        "window.GROWTH_DASHBOARD_DATA = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    payload = fetch_cloudflare_growth_data()
    write_growth_data(payload)
    print(f"Wrote {OUTPUT}")
    print(f"Generated at: {payload['generatedAt']}")
    print(f"Users: {payload['traffic']['users']}")
    print(f"Page views: {payload['traffic']['pageViews']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Cloudflare sync failed: {exc}", file=sys.stderr)
        raise
