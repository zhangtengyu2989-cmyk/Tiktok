"""
数据同步API - 跨设备诊断历史同步
"""
import json
import sqlite3
import secrets
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.api.auth_api import get_current_user, security

router = APIRouter()

DB_PATH = "data/tiktok_baseline.db"


class SyncRecord(BaseModel):
    id: str
    title: str
    category: str
    input_type: str = "video"
    overall_score: float
    grade: str
    report_json: dict
    created_at: str
    server_id: Optional[str] = None


class SyncPushRequest(BaseModel):
    records: List[SyncRecord]
    device_id: str


class SyncPullResponse(BaseModel):
    records: List[SyncRecord]
    synced_at: str


@router.post("/sync/push")
async def sync_push(
    req: SyncPushRequest,
    user: dict = Depends(get_current_user)
):
    """推送本地诊断记录到服务器"""
    user_id = user["id"]
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pushed = 0

    try:
        for record in req.records:
            # 生成服务端ID
            server_id = secrets.token_urlsafe(16)

            # 检查是否已存在（通过local_id匹配）
            existing = conn.execute("""
                SELECT id FROM diagnosis_history
                WHERE user_id = ? AND id = ?
            """, (user_id, record.id)).fetchone()

            if existing:
                # 更新已有记录
                conn.execute("""
                    UPDATE diagnosis_history SET
                        title = ?, category = ?, input_type = ?,
                        overall_score = ?, grade = ?, report_json = ?,
                        user_id = ?
                    WHERE id = ?
                """, (
                    record.title, record.category, record.input_type,
                    record.overall_score, record.grade,
                    json.dumps(record.report_json), user_id,
                    record.id
                ))
            else:
                # 插入新记录
                conn.execute("""
                    INSERT INTO diagnosis_history
                    (id, user_id, title, category, input_type, overall_score, grade, report_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.id, user_id, record.title, record.category,
                    record.input_type, record.overall_score, record.grade,
                    json.dumps(record.report_json)
                ))

            # 记录同步日志
            conn.execute("""
                INSERT INTO sync_log (user_id, device_id, action, record_id)
                VALUES (?, ?, 'push', ?)
            """, (user_id, req.device_id, record.id))
            pushed += 1

        conn.commit()
    finally:
        conn.close()

    return {
        "status": "ok",
        "pushed": pushed,
        "synced_at": datetime.now().isoformat()
    }


@router.get("/sync/pull", response_model=SyncPullResponse)
async def sync_pull(
    since: Optional[str] = Query(None, description="仅返回指定时间之后的记录 ISO格式"),
    user: dict = Depends(get_current_user)
):
    """从服务器拉取诊断记录"""
    user_id = user["id"]
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        if since:
            rows = conn.execute("""
                SELECT id, title, category, input_type, overall_score, grade,
                       report_json, created_at
                FROM diagnosis_history
                WHERE user_id = ? AND created_at > ?
                ORDER BY created_at DESC
            """, (user_id, since)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, title, category, input_type, overall_score, grade,
                       report_json, created_at
                FROM diagnosis_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 100
            """, (user_id,)).fetchall()

        records = []
        for row in rows:
            records.append(SyncRecord(
                id=row["id"],
                title=row["title"],
                category=row["category"],
                input_type=row["input_type"],
                overall_score=row["overall_score"],
                grade=row["grade"],
                report_json=json.loads(row["report_json"]),
                created_at=row["created_at"],
                server_id=row["id"]
            ))

        return SyncPullResponse(
            records=records,
            synced_at=datetime.now().isoformat()
        )
    finally:
        conn.close()


@router.get("/sync/status")
async def sync_status(user: dict = Depends(get_current_user)):
    """获取同步状态"""
    user_id = user["id"]
    conn = sqlite3.connect(DB_PATH)

    try:
        total = conn.execute("""
            SELECT COUNT(*) FROM diagnosis_history WHERE user_id = ?
        """, (user_id,)).fetchone()[0]

        recent = conn.execute("""
            SELECT synced_at, action, record_id FROM sync_log
            WHERE user_id = ?
            ORDER BY synced_at DESC
            LIMIT 10
        """, (user_id,)).fetchall()

        return {
            "user_id": user_id,
            "total_records": total,
            "recent_sync": [
                {"at": str(r[0]), "action": r[1], "record_id": r[2]}
                for r in recent
            ],
            "server_time": datetime.now().isoformat()
        }
    finally:
        conn.close()


@router.delete("/sync/records/{record_id}")
async def delete_sync_record(
    record_id: str,
    user: dict = Depends(get_current_user)
):
    """删除服务器上的诊断记录"""
    user_id = user["id"]
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("""
            DELETE FROM diagnosis_history
            WHERE id = ? AND user_id = ?
        """, (record_id, user_id))

        conn.execute("""
            INSERT INTO sync_log (user_id, action, record_id)
            VALUES (?, 'delete', ?)
        """, (user_id, record_id))

        conn.commit()
        return {"status": "ok", "deleted": record_id}
    finally:
        conn.close()
