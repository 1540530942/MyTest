from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse


app = FastAPI(title="Remote Sensing Module")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"ok": "true"}


@app.get("/api/module")
def module() -> dict[str, object]:
    return {
        "id": "remote-sensing",
        "name": "Remote Sensing Module",
        "status": "scaffold",
        "capabilities": ["imagery", "map", "timeline", "alerts", "metadata"],
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Remote Sensing Module</title>
    <style>
      body { margin: 0; font-family: Inter, Arial, sans-serif; background: #f7faf9; color: #18211f; }
      main { max-width: 920px; margin: 0 auto; padding: 56px 24px; }
      .eyebrow { color: #47675f; font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }
      h1 { font-size: 40px; line-height: 1.1; margin: 12px 0 16px; }
      p { font-size: 18px; line-height: 1.6; color: #42514d; }
      code { background: #e7efec; padding: 2px 6px; border-radius: 4px; }
    </style>
  </head>
  <body>
    <main>
      <p class="eyebrow">sensing.wangyutang.com</p>
      <h1>遥感系统模块</h1>
      <p>这里是遥感数据接入、地图图层、时间轴和告警能力的可执行占位服务。</p>
      <p>健康检查：<code>/api/health</code></p>
    </main>
  </body>
</html>"""
