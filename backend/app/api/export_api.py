"""
诊断报告导出API - 后端渲染方案
使用Playwright/Chromium进行服务端截图生成
"""
import asyncio
import io
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

CARD_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=380">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}
.card {
  width: 340px;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0,0,0,0.1);
}
.header {
  background: linear-gradient(135deg, #25f4ee 0%, #fe2c55 100%);
  padding: 20px 24px 16px;
  color: #fff;
}
.header-sub {
  font-size: 11px;
  font-weight: 600;
  opacity: 0.85;
  margin-bottom: 8px;
}
.header-table { width: 100%; }
.header-table td:first-child { vertical-align: top; padding-right: 12px; }
.header-table td:last-child { vertical-align: top; text-align: right; white-space: nowrap; width: 70px; }
.title { font-size: 14px; font-weight: 700; line-height: 1.5; word-break: break-all; color: #fff; }
.score { font-size: 40px; font-weight: 900; line-height: 1; }
.grade {
  font-size: 12px;
  font-weight: 700;
  background: rgba(255,255,255,0.25);
  padding: 2px 8px;
  border-radius: 6px;
  margin-top: 4px;
  display: inline-block;
}
.content { padding: 16px 24px; }
.bar-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
.bar-label { font-size: 10px; color: #999; width: 28px; text-align: right; margin-right: 8px; }
.bar { flex: 1; height: 4px; background: #f0f0f0; border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, #25f4ee, #fe2c55); border-radius: 2px; transition: width 0.3s; }
.bar-value { font-size: 10px; font-weight: 600; color: #666; width: 24px; text-align: right; margin-left: 6px; }
.issues { padding: 12px 24px; border-top: 1px solid #f0f0f0; }
.issues-title { font-size: 10px; font-weight: 600; color: #999; margin-bottom: 8px; text-transform: uppercase; }
.issue { font-size: 11px; color: #555; line-height: 1.5; margin-bottom: 4px; }
.footer {
  padding: 10px 24px;
  background: #fafafa;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.footer-brand {
  display: flex;
  align-items: center;
  gap: 4px;
}
.footer-logo {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  background: linear-gradient(135deg, #25f4ee, #fe2c55);
}
.footer-name { font-size: 11px; font-weight: 700; color: #262626; }
.footer-url { font-size: 9px; color: #bbb; }
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <div class="header-sub">抖医诊断报告</div>
    <table class="header-table"><tr>
      <td><div class="title">{title}</div></td>
      <td>
        <div class="score">{score}</div>
        <div class="grade">{grade}</div>
      </td>
    </tr></table>
  </div>
  <div class="content">
    {bars}
  </div>
  <div class="issues">
    <div class="issues-title">主要发现</div>
    {issues}
  </div>
  <div class="footer">
    <div class="footer-brand">
      <div class="footer-logo"></div>
      <span class="footer-name">抖医 TiktokRx</span>
    </div>
    <span class="footer-url">tiktokrx.muran.tech</span>
  </div>
</div>
</body>
</html>
"""


class ExportRequest(BaseModel):
    title: str
    score: int
    grade: str
    radar_data: dict
    issues: List[str]
    format: str = "png"


def generate_html(req: ExportRequest) -> str:
    """生成诊断卡片的HTML"""
    labels = {
        "content": "内容",
        "visual": "视觉",
        "growth": "增长",
        "user_reaction": "互动",
        "overall": "综合",
    }

    bars_html = ""
    for key, val in req.radar_data.items():
        label = labels.get(key, key)
        bars_html += f'''
        <div class="bar-row">
          <span class="bar-label">{label}</span>
          <div class="bar"><div class="bar-fill" style="width:{val}%"></div></div>
          <span class="bar-value">{int(val)}</span>
        </div>'''

    issues_html = ""
    for i, issue in enumerate(req.issues[:3]):
        issues_html += f'<div class="issue">{i+1}. {issue}</div>'

    return CARD_HTML_TEMPLATE.format(
        title=req.title,
        score=req.score,
        grade=req.grade,
        bars=bars_html,
        issues=issues_html,
    )


async def render_with_playwright(html: str, format: str = "png") -> bytes:
    """使用Playwright渲染HTML并返回图片bytes"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise HTTPException(503, "Playwright未安装，请运行: pip install playwright && playwright install chromium")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 400, "height": 650})
        await page.set_content(html)

        if format == "pdf":
            pdf_data = await page.pdf(format="A4", margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            await browser.close()
            return pdf_data
        else:
            screenshot = await page.screenshot(type="png", full_page=False)
            await browser.close()
            return screenshot


@router.post("/export/render")
async def render_diagnosis_card(req: ExportRequest):
    """
    后端渲染诊断卡片
    优先使用Playwright渲染，失败时返回错误信息
    """
    try:
        html = generate_html(req)
        image_data = await render_with_playwright(html, req.format)

        if req.format == "pdf":
            return StreamingResponse(
                io.BytesIO(image_data),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename=抖医诊断-{req.title[:10]}.pdf'
                }
            )
        else:
            return StreamingResponse(
                io.BytesIO(image_data),
                media_type="image/png",
                headers={
                    "Content-Disposition": f'attachment; filename=抖医诊断-{req.title[:10]}.png'
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        router.error(f"渲染失败: {e}")
        raise HTTPException(500, f"渲染失败: {str(e)}")
