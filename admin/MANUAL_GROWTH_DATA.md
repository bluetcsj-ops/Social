# Phase 1 手动增长数据导入

如果你已经启用 Phase 2 本机自动同步，请优先看 `admin/CLOUDFLARE_LOCAL_SYNC.md`。本文件保留为手动导入和备用 JSON 格式说明。

当前阶段不接 Cloudflare API。增长后台只读取 JSON：

- 默认读取 `admin/growth-data.js`
- 也可以在后台“数据导入”里粘贴 JSON
- 也可以选择本地 `.json` 文件导入

## 最小可用格式

```json
{
  "generatedAt": "2026-06-11",
  "source": "Cloudflare Analytics manual copy",
  "traffic": {
    "users": 1840,
    "sessions": 2315,
    "pageViews": 6420,
    "returningVisitors": 412,
    "trafficGrowthPct": 18,
    "engagementGrowthPct": 0,
    "followersDelta": 0
  },
  "topPages": [
    { "page": "Homepage", "path": "/", "views": 1820, "avgTimeSec": 0, "improvement": "Improve homepage path to predictions." },
    { "page": "Schedule", "path": "/schedule", "views": 3860, "avgTimeSec": 0, "improvement": "Create more schedule-related content." }
  ],
  "countries": [
    { "country": "USA", "sessions": 470, "engagement": 0 },
    { "country": "Brazil", "sessions": 520, "engagement": 0 }
  ],
  "referrers": [
    { "source": "Google", "sessions": 880 },
    { "source": "Direct", "sessions": 520 },
    { "source": "X", "sessions": 410 }
  ],
  "posts": []
}
```

## 从 Cloudflare 手动复制时的对应关系

- Visitors 或 Unique visitors -> `traffic.users`
- Visits 或 Requests 可先近似填入 -> `traffic.sessions`
- Page views 或 Requests 可先近似填入 -> `traffic.pageViews`
- Top pages -> `topPages`
- Top countries -> `countries`
- Referrers -> `referrers`

Cloudflare 和 GA/Plausible 的统计口径不同。Phase 1 的目标是让后台先能根据手动 JSON 工作，观察趋势，不追求全自动精确归因。
