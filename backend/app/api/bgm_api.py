"""
BGM分析 API - 独立的BGM热度分析、适配度评估、替代推荐
"""
from __future__ import annotations

import logging
import os
import sqlite3

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.bgm_agent import BGMAgent
from app.agents.research_data import BGM_HEAT_LEVELS, get_heat_level

router = APIRouter()
logger = logging.getLogger("tiktokrx.bgm")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "tiktok_baseline.db")


class BGMAnalyzeRequest(BaseModel):
    """BGM分析请求"""
    bgm_name: str
    category: str = "food"
    bgm_style: str = None
    content_mood: str = None


class BGMHotResponse(BaseModel):
    """热门BGM响应"""
    items: list[dict]
    total: int


@router.post("/analyze-bgm")
async def analyze_bgm(req: BGMAnalyzeRequest):
    """
    独立分析BGM的推广价值和适配度。
    返回热度等级、内容适配度、推流预测和替代推荐。
    """
    agent = BGMAgent()

    result = await agent.diagnose(
        title="",
        category=req.category,
        bgm_name=req.bgm_name,
        bgm_style=req.bgm_style,
        content_mood=req.content_mood,
    )

    result.pop("_meta", None)
    return result


@router.get("/bgm-hot")
async def get_bgm_hot(category: str = None, limit: int = 20):
    """
    获取热门BGM列表。
    支持按品类筛选，返回热度等级、适配风格等信息。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        if category:
            cursor.execute(
                """SELECT id, song_name, artist, heat_index, heat_level, style, mood, categories
                   FROM bgm_database
                   WHERE categories LIKE ? OR style LIKE ?
                   ORDER BY heat_index DESC
                   LIMIT ?""",
                (f"%{category}%", f"%{category}%", limit)
            )
        else:
            cursor.execute(
                """SELECT id, song_name, artist, heat_index, heat_level, style, mood, categories
                   FROM bgm_database
                   ORDER BY heat_index DESC
                   LIMIT ?""",
                (limit,)
            )

        rows = cursor.fetchall()
        items = []
        for row in rows:
            items.append({
                "id": row[0],
                "song_name": row[1],
                "artist": row[2],
                "heat_index": row[3],
                "heat_level": row[4],
                "style": row[5],
                "mood": row[6],
                "categories": row[7].split(",") if row[7] else [],
            })

        return {"items": items, "total": len(items)}
    except Exception as e:
        logger.error("Failed to fetch bgm hot list: %s", e)
        raise HTTPException(500, "Failed to fetch BGM list")
    finally:
        conn.close()


@router.get("/bgm-levels")
async def get_bgm_levels():
    """获取BGM热度等级定义"""
    return {
        "levels": [
            {
                "level": k,
                "threshold": v["threshold"],
                "traffic_weight": v["traffic_weight"],
                "description": v["description"],
            }
            for k, v in sorted(
                BGM_HEAT_LEVELS.items(),
                key=lambda x: -x[1]["threshold"]
            )
        ]
    }


@router.post("/identify-bgm")
async def identify_bgm(bgm_name: str = None, category: str = None):
    """
    根据BGM名称或品类识别BGM并返回详细信息。
    如果数据库中没有完全匹配的记录，返回最接近的推荐。
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        if bgm_name:
            cursor.execute(
                """SELECT id, song_name, artist, heat_index, heat_level, style, mood, categories
                   FROM bgm_database
                   WHERE song_name LIKE ? OR artist LIKE ?
                   ORDER BY heat_index DESC
                   LIMIT 5""",
                (f"%{bgm_name}%", f"%{bgm_name}%")
            )
            rows = cursor.fetchall()
            if rows:
                items = []
                for row in rows:
                    items.append({
                        "id": row[0],
                        "song_name": row[1],
                        "artist": row[2],
                        "heat_index": row[3],
                        "heat_level": row[4],
                        "style": row[5],
                        "mood": row[6],
                        "categories": row[7].split(",") if row[7] else [],
                    })
                return {"items": items, "total": len(items), "source": "match"}

        if category:
            cursor.execute(
                """SELECT id, song_name, artist, heat_index, heat_level, style, mood, categories
                   FROM bgm_database
                   WHERE categories LIKE ? OR style LIKE ?
                   ORDER BY heat_index DESC
                   LIMIT 10""",
                (f"%{category}%", f"%{category}%")
            )
            rows = cursor.fetchall()
            if rows:
                items = []
                for row in rows:
                    items.append({
                        "id": row[0],
                        "song_name": row[1],
                        "artist": row[2],
                        "heat_index": row[3],
                        "heat_level": row[4],
                        "style": row[5],
                        "mood": row[6],
                        "categories": row[7].split(",") if row[7] else [],
                    })
                return {"items": items, "total": len(items), "source": "category"}

        return {"items": [], "total": 0, "source": "none"}
    except Exception as e:
        logger.error("Failed to identify BGM: %s", e)
        raise HTTPException(500, "Failed to identify BGM")
    finally:
        conn.close()
