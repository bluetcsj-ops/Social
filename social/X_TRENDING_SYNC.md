# X 热门帖子同步

这个模块用于把 X 上和 World Cup 2026 / football 相关的真实热门帖子拉到本地，并写入：

```text
social/x-trending-posts.js
```

页面会读取该文件，按互动分显示前 5 条，并让你点击打开原帖人工回复。

## 1. 设置 Token

需要 X API Bearer Token。拿到后在 PowerShell 里设置：

```powershell
[Environment]::SetEnvironmentVariable("X_BEARER_TOKEN", "你的 X Bearer Token", "User")
```

重新打开 PowerShell 后生效。

## 2. 手动同步

```powershell
cd "J:\promotion helper"
python social\sync_x_trending.py
```

成功后刷新 `social-dashboard.html`。

## 3. 定期同步

默认每 2 小时同步一次：

```powershell
cd "J:\promotion helper"
powershell -ExecutionPolicy Bypass -File social\install_x_trending_sync_task.ps1
```

测试任务：

```powershell
schtasks.exe /Run /TN WorldCup2026XTrendingSync
```

## 4. 安全原则

- 不自动发帖。
- 不自动回复。
- 不自动点赞或转发。
- 只读取公开搜索结果和公开互动指标。
- 你点击“打开原帖回复”后，仍由你人工判断是否参与讨论。

## 没有 Bearer Token 怎么办？

可以使用手动导入方式，效果接近，只是“采集帖子”这一步由你人工完成：

1. 打开页面左侧的 5 个 X 搜索入口。
2. 在 X 上找到真实热门帖子。
3. 把帖子链接、正文、点赞、回复、转发、引用数填入：

```text
social/x-trending-manual.json
```

4. 运行：

```powershell
cd "J:\promotion helper"
python social\import_x_trending_manual.py
```

页面会按同样公式排序，显示前 5 条，并指向原帖。
