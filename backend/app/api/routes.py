"""
API 路由定义
"""
from fastapi import APIRouter

from app.api.diagnose import router as diagnose_router
from app.api.baseline_api import router as baseline_router
from app.api.comments_api import router as comments_router
from app.api.history_api import router as history_router
from app.api.screenshot_api import router as screenshot_router
from app.api.optimize_api import router as optimize_router
from app.api.visit_api import router as visit_router
from app.api.bgm_api import router as bgm_router
from app.api.text_api import router as text_router
from app.api.auth_api import router as auth_router
from app.api.sync_api import router as sync_router
from app.api.export_api import router as export_router
from app.api.admin_api import router as admin_router

router = APIRouter()


@router.get("/health")
async def api_health():
    """轻量探活：前端可用来判断 Vite 代理到后端是否通畅（不调用外网 LLM）。"""
    return {"ok": True, "service": "tiktokrx-api"}


router.include_router(diagnose_router, tags=["diagnose"])
router.include_router(baseline_router, tags=["baseline"])
router.include_router(comments_router, tags=["comments"])
# history_router disabled — #58 fix: history is local-only (IndexedDB), server endpoints were a data leak
# router.include_router(history_router, tags=["history"])
router.include_router(screenshot_router, tags=["screenshot"])
router.include_router(optimize_router, tags=["optimize"])
router.include_router(visit_router, tags=["visit"])
router.include_router(bgm_router, tags=["bgm"])
router.include_router(text_router, tags=["text"])
router.include_router(auth_router, tags=["auth"])
router.include_router(sync_router, tags=["sync"])
router.include_router(export_router, tags=["export"])
router.include_router(admin_router, tags=["admin"])
