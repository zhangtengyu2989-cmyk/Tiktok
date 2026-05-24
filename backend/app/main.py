"""
TiktokRx 后端入口
"""
import logging
import os
import sqlite3
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router as api_router
from app import local_memory

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tiktok_baseline.db")


def _ensure_history_table():
    """启动时自动创建所有数据表（如不存在）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS diagnosis_history (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            input_type TEXT DEFAULT 'video',
            overall_score REAL,
            grade TEXT,
            report_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_history_created
        ON diagnosis_history(created_at DESC)
    """)
    # Usage tracking table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            action TEXT NOT NULL DEFAULT 'diagnose',
            title TEXT DEFAULT '',
            category TEXT DEFAULT '',
            total_tokens INTEGER DEFAULT 0,
            duration_sec REAL DEFAULT 0,
            status TEXT DEFAULT 'ok',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_log(created_at DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_ip ON usage_log(ip)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS visit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visitor_hash TEXT NOT NULL,
            user_agent_hash TEXT DEFAULT '',
            path TEXT NOT NULL,
            referrer TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_visit_created ON visit_log(created_at DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_visit_visitor ON visit_log(visitor_hash)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_visit_path ON visit_log(path)")

    # Baseline stats table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS baseline_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            metric_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, metric_name)
        )
    """)

    # BGM database table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bgm_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_name TEXT NOT NULL,
            artist TEXT DEFAULT '',
            bgm_name TEXT NOT NULL,
            style TEXT DEFAULT '动感',
            categories TEXT DEFAULT '',
            heat_index INTEGER DEFAULT 0,
            heat_level TEXT DEFAULT 'C',
            source TEXT DEFAULT '',
            douyin_matched INTEGER DEFAULT 0,
            song_id TEXT DEFAULT '',
            album TEXT DEFAULT '',
            duration INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(song_name, artist, source)
        )
    """)
    # 扩展旧表（兼容已有数据）
    for col, default in [("bgm_name", "song_name"), ("source", "''"), ("douyin_matched", 0),
                         ("song_id", "''"), ("album", "''"), ("duration", 0)]:
        try:
            conn.execute(f"ALTER TABLE bgm_database ADD COLUMN {col} {default}")
        except:
            pass

    # 用户表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login_at TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)

    # 设备表（支持多设备）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_devices (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            device_name TEXT,
            device_type TEXT DEFAULT 'unknown',
            last_sync_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 同步记录表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            device_id TEXT,
            action TEXT NOT NULL,
            record_id TEXT,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 诊断历史表添加user_id关联
    try:
        conn.execute("ALTER TABLE diagnosis_history ADD COLUMN user_id TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON diagnosis_history(user_id)")
    except:
        pass

    # Text baseline table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS text_baseline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            avg_text_length INTEGER DEFAULT 0,
            optimal_text_length_min INTEGER DEFAULT 100,
            optimal_text_length_max INTEGER DEFAULT 300,
            emotion_density REAL DEFAULT 0,
            interaction_trigger_avg REAL DEFAULT 0,
            optimal_paragraph_count INTEGER DEFAULT 5,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category)
        )
    """)

    # Comment baseline table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comment_baseline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            avg_like_rate REAL DEFAULT 0,
            avg_comment_rate REAL DEFAULT 0,
            avg_collect_rate REAL DEFAULT 0,
            avg_share_rate REAL DEFAULT 0,
            viral_engagement_ratio REAL DEFAULT 0,
            comment_sentiment_ratio TEXT DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category)
        )
    """)

    # Publish time baseline table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS publish_time_baseline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            weekday_best_hours TEXT DEFAULT '[]',
            weekend_best_hours TEXT DEFAULT '[]',
            golden_window TEXT DEFAULT '',
            avg_publish_interval_hours INTEGER DEFAULT 24,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category)
        )
    """)

    # Title baseline table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS title_baseline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            avg_title_length INTEGER DEFAULT 0,
            viral_title_avg_length INTEGER DEFAULT 0,
            optimal_length_min INTEGER DEFAULT 11,
            optimal_length_max INTEGER DEFAULT 19,
            numeric_title_ratio REAL DEFAULT 0,
            hook_word_ratio REAL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category)
        )
    """)

    # Tag baseline table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tag_baseline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            optimal_tag_count INTEGER DEFAULT 6,
            tag_count_range TEXT DEFAULT '4-8',
            broad_tag_ratio REAL DEFAULT 0,
            niche_tag_ratio REAL DEFAULT 0,
            hot_tag_retention_days INTEGER DEFAULT 7,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category)
        )
    """)

    conn.commit()
    conn.close()
    local_memory.ensure_memory_md()


def _seed_baseline_data():
    """初始化基线数据（如果不存在）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM baseline_stats")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # 品类基线数据
    categories_data = [
        ("美食", 15234, 89500, 67, 6, 45000, 16.5, 18.3),
        ("时尚", 8921, 52000, 45, 5, 38000, 14.2, 15.8),
        ("科技", 12456, 75000, 90, 7, 25000, 17.8, 17.5),
        ("旅行", 18762, 95000, 120, 6, 52000, 15.6, 14.3),
        ("生活", 9834, 58000, 60, 5, 42000, 18.1, 19.4),
    ]

    for cat_data in categories_data:
        cat, avg_eng, viral, duration, tags, bgm_heat, avg_title, viral_title = cat_data
        cursor.execute("""
            INSERT OR IGNORE INTO baseline_stats (category, metric_name, metric_value)
            VALUES (?, 'avg_engagement', ?)
        """, (cat, avg_eng))
        cursor.execute("""
            INSERT OR IGNORE INTO baseline_stats (category, metric_name, metric_value)
            VALUES (?, 'viral_threshold', ?)
        """, (cat, viral))
        cursor.execute("""
            INSERT OR IGNORE INTO baseline_stats (category, metric_name, metric_value)
            VALUES (?, 'optimal_duration_secs', ?)
        """, (cat, duration))
        cursor.execute("""
            INSERT OR IGNORE INTO baseline_stats (category, metric_name, metric_value)
            VALUES (?, 'optimal_tags', ?)
        """, (cat, tags))
        cursor.execute("""
            INSERT OR IGNORE INTO baseline_stats (category, metric_name, metric_value)
            VALUES (?, 'bgm_heat_baseline', ?)
        """, (cat, bgm_heat))

    # 发布时间基线
    publish_times = {
        "美食": (json.dumps([11, 12, 18]), json.dumps([10, 11, 19]), "午餐前1小时/晚餐前1小时"),
        "时尚": (json.dumps([19, 20, 21]), json.dumps([13, 21]), "下班后/睡前"),
        "科技": (json.dumps([12, 13, 21]), json.dumps([21]), "午休/晚间"),
        "旅行": (json.dumps([18, 19, 20]), json.dumps([21]), "晚间预热"),
        "生活": (json.dumps([12, 13, 22]), json.dumps([10, 21]), "碎片化时间"),
    }
    for cat, (weekday, weekend, golden) in publish_times.items():
        cursor.execute("""
            INSERT OR IGNORE INTO publish_time_baseline (category, weekday_best_hours, weekend_best_hours, golden_window)
            VALUES (?, ?, ?, ?)
        """, (cat, weekday, weekend, golden))

    # 评论互动基线
    comment_data = {
        "美食": (0.052, 0.012, 0.021, 0.005, 15.0),
        "时尚": (0.068, 0.015, 0.028, 0.006, 12.0),
        "科技": (0.041, 0.009, 0.015, 0.004, 18.0),
        "旅行": (0.072, 0.018, 0.032, 0.008, 10.0),
        "生活": (0.058, 0.013, 0.024, 0.005, 14.0),
    }
    sentiment = json.dumps({"positive": 0.6, "neutral": 0.2, "negative": 0.2})
    for cat, (like_r, comment_r, collect_r, share_r, ratio) in comment_data.items():
        cursor.execute("""
            INSERT OR IGNORE INTO comment_baseline (category, avg_like_rate, avg_comment_rate, avg_collect_rate, avg_share_rate, viral_engagement_ratio, comment_sentiment_ratio)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cat, like_r, comment_r, collect_r, share_r, ratio, sentiment))

    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用生命周期：启动时自动建表"""
    _ensure_history_table()
    _seed_baseline_data()
    from app.api.auth_api import init_auth_tables
    init_auth_tables()
    yield

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

app = FastAPI(
    title="TiktokRx API",
    description="AI驱动的抖音内容诊断平台",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8002",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

# ── Landing page ──
SPA_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
LANDING_HTML = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "landing.html")

@app.get("/")
async def serve_landing():
    """首页 → 着陆页"""
    if os.path.isfile(LANDING_HTML):
        return FileResponse(LANDING_HTML, media_type="text/html")
    if os.path.isdir(SPA_DIST):
        return FileResponse(os.path.join(SPA_DIST, "index.html"))
    return {"status": "ok", "service": "TiktokRx API"}


# ── Legal pages ──
TERMS_HTML = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "terms.html")
PRIVACY_HTML = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "privacy.html")
RESEARCH_HTML = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "research_whitepaper.html")
PAPER_HTML = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "research_paper.html")


@app.get("/terms")
async def serve_terms():
    if os.path.isfile(TERMS_HTML):
        return FileResponse(TERMS_HTML, media_type="text/html")
    return {"error": "Terms page not found"}


@app.get("/privacy")
async def serve_privacy():
    if os.path.isfile(PRIVACY_HTML):
        return FileResponse(PRIVACY_HTML, media_type="text/html")
    return {"error": "Privacy page not found"}


@app.get("/research")
async def serve_research():
    """研究白皮书页面：数据驱动的抖音内容诊断方法论"""
    if os.path.isfile(RESEARCH_HTML):
        return FileResponse(RESEARCH_HTML, media_type="text/html")
    return {"error": "Research whitepaper not found"}


@app.get("/paper")
async def serve_paper():
    """研究论文页面：基于多Agent辩论的抖音内容诊断系统"""
    if os.path.isfile(PAPER_HTML):
        return FileResponse(PAPER_HTML, media_type="text/html")
    return {"error": "Research paper not found"}

# ── SPA: product app at /app and sub-routes ──
SPA_ROUTES = {"/app", "/diagnosing", "/report", "/history", "/screenshot", "/bgm"}

if os.path.isdir(SPA_DIST):
    from starlette.middleware.base import BaseHTTPMiddleware

    # 静态页面路由，不走 SPA fallback
    STATIC_ROUTES = {"/paper", "/research", "/terms", "/privacy"}

    class SPAMiddleware(BaseHTTPMiddleware):
        """Serve SPA index.html for SPA_ROUTES"""
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            path = request.url.path
            if (response.status_code == 404
                    and not path.startswith("/api")
                    and not path.startswith("/assets")
                    and path != "/"
                    and not path.startswith("/admin")
                    and path not in STATIC_ROUTES):
                return FileResponse(os.path.join(SPA_DIST, "index.html"))
            return response

    app.mount("/assets", StaticFiles(directory=os.path.join(SPA_DIST, "assets")), name="static")
    app.add_middleware(SPAMiddleware)

    @app.get("/app")
    async def serve_app():
        """产品主页面"""
        return FileResponse(os.path.join(SPA_DIST, "index.html"))


@app.get("/api/health")
async def health():
    """详细健康检查，含数据库探测"""
    db_ok = False
    bgm_count = 0
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM bgm_database")
        bgm_count = cur.fetchone()[0]
        conn.close()
        db_ok = True
    except Exception:
        pass
    return {
        "status": "ok" if db_ok else "degraded",
        "database": {"connected": db_ok, "bgm_count": bgm_count},
        "service": "TiktokRx API",
    }
