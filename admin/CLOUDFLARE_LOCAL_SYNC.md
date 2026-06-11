# Phase 2 本机自动同步 Cloudflare 数据

这个阶段不让网页直接访问 Cloudflare API。Token 只保存在你本机环境变量里，由本机脚本定时拉取数据，然后覆盖生成：

```text
admin/growth-data.js
```

增长后台仍然只读取 JSON/JS 数据文件。

## 1. 准备 Cloudflare 信息

需要两个值：

- `CLOUDFLARE_ZONE_ID`：站点的 Zone ID。
- `CLOUDFLARE_API_TOKEN`：Cloudflare API Token。

Token 权限建议最小化：

- Zone Read
- Analytics Read

只授权到 `worldcup.bluet.cc` 对应 zone。

## 2. 设置环境变量

在 PowerShell 中执行：

```powershell
[Environment]::SetEnvironmentVariable("CLOUDFLARE_ZONE_ID", "你的 Zone ID", "User")
[Environment]::SetEnvironmentVariable("CLOUDFLARE_API_TOKEN", "你的 API Token", "User")
```

然后关闭并重新打开 PowerShell。

## 3. 手动测试一次

在项目目录运行：

```powershell
python admin\sync_cloudflare.py
```

成功后会更新：

```text
admin/growth-data.js
```

刷新增长后台即可看到 Cloudflare 数据。

## 4. 安装每 3 小时同步

在项目目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File admin\install_cloudflare_sync_task.ps1
```

它会创建 Windows 计划任务：

```text
WorldCup2026 Cloudflare Growth Sync
```

频率：每 3 小时。

## 5. 数据口径

脚本读取最近 24 小时 Cloudflare Analytics：

- `users`：Cloudflare uniques
- `sessions`：用 requests 近似
- `pageViews`：用 requests 近似
- `topPages`：按请求路径聚合
- `countries`：按国家聚合
- `referrers`：按来源 host 聚合

Cloudflare 的请求数据不等于 GA/Plausible 的精确会话和页面停留时间，但足够作为增长后台的早期流量趋势信号。
