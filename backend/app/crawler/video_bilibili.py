"""
Bilibili 视频数据爬虫
从 Bilibili 排行榜 API 采集真实视频互动数据
无需认证：title/播放量/点赞/投币/收藏/分享/时长/描述/作者
"""
import requests
import logging
import time
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger("tiktokrx.crawler.bilibili")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
    "Accept": "application/json",
}

# Bilibili 分类ID（rid -> 名称）
BILIBILI_CATEGORIES = {
    0: "全站",
    1: "国产动画",
    3: "音乐",
    4: "游戏",
    5: "娱乐",
    11: "电视剧",
    13: "番剧",
    23: "电影",
    36: "科技",
    119: "美食",
    129: "舞蹈",
}


def infer_category_from_title(title: str, desc: str = "") -> str:
    """从标题和描述推断内容品类"""
    text = (title + desc).lower()
    scores = {
        "美食": ["美食", "吃播", "烹饪", "菜谱", "探店", "外卖", "烘焙", "小吃"],
        "科技": ["手机", "电脑", "测评", "科技", "软件", "iPhone", "相机", "无人机"],
        "时尚": ["穿搭", "美妆", "护肤", "衣服", "口红", "香水"],
        "旅行": ["旅行", "旅游", "攻略", "打卡", "景点", "酒店"],
        "生活": ["生活", "日常", "vlog", "情感", "解压", "收纳"],
        "音乐": ["音乐", "歌曲", "翻唱", "演奏", "作曲"],
        "游戏": ["游戏", "联机", "攻略", "通关", "电竞"],
    }
    max_score = 0
    best = "其他"
    for cat, keywords in scores.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > max_score:
            max_score = score
            best = cat
    return best if max_score > 0 else "其他"


def fetch_bilibili_ranking(rid: int = 0, limit: int = 50) -> List[Dict]:
    """获取 Bilibili 排行榜视频数据"""
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/ranking/v2",
            params={"rid": rid, "type": "all"},
            headers=HEADERS,
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning(f"Bilibili[rid={rid}] HTTP {resp.status_code}")
            return []
        data = resp.json()
        if data.get("code") != 0:
            logger.warning(f"Bilibili[rid={rid}] API error: {data.get('message')}")
            return []

        videos = data.get("data", []) or []
        results = []
        for v in videos[:limit]:
            title = v.get("title", "").strip().replace("<em>", "").replace("</em>", "")
            if not title:
                continue

            stat = v.get("stat", {}) or {}
            owner = v.get("owner", {}) or {}
            desc = v.get("desc", "").strip()
            inferred_cat = infer_category_from_title(title, desc)

            results.append({
                "platform": "bilibili",
                "bvid": v.get("bvid", ""),
                "title": title,
                "author": owner.get("name", ""),
                "category": inferred_cat,
                "description": desc,
                "duration": v.get("duration", 0),
                "view_count": stat.get("view", 0),
                "like_count": stat.get("like", 0),
                "coin_count": stat.get("coin", 0),
                "favorite_count": stat.get("favorite", 0),
                "share_count": stat.get("share", 0),
                "reply_count": stat.get("reply", 0),
                "pubdate": v.get("pubdate", 0),
                "source": f"bilibili_ranking_{rid}",
                "crawled_at": datetime.now().isoformat(),
            })

        logger.info(f"Bilibili[rid={rid}] 获取 {len(results)} 条")
        return results
    except Exception as e:
        logger.warning(f"Bilibili[rid={rid}] 失败: {e}")
        return []


def init_video_table(db_path: str = "data/tiktok_baseline.db") -> None:
    """初始化 video_database 表"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS video_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT DEFAULT 'bilibili',
            bvid TEXT UNIQUE,
            title TEXT NOT NULL,
            author TEXT DEFAULT '',
            category TEXT DEFAULT '其他',
            description TEXT DEFAULT '',
            duration INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            coin_count INTEGER DEFAULT 0,
            favorite_count INTEGER DEFAULT 0,
            share_count INTEGER DEFAULT 0,
            reply_count INTEGER DEFAULT 0,
            pubdate INTEGER DEFAULT 0,
            source TEXT DEFAULT 'bilibili_ranking',
            crawled_at TEXT,
            UNIQUE(bvid, source)
        )
    """)
    conn.commit()
    conn.close()
    logger.info("video_database 表初始化完成")


def save_video_records(records: List[Dict], db_path: str = "data/tiktok_baseline.db") -> int:
    """保存视频记录到数据库"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    init_video_table(db_path)
    count = 0
    for r in records:
        if not r.get("bvid") or not r.get("title"):
            continue
        try:
            conn.execute("""
                INSERT OR IGNORE INTO video_database
                (platform, bvid, title, author, category, description, duration,
                 view_count, like_count, coin_count, favorite_count, share_count,
                 reply_count, pubdate, source, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("platform", "bilibili"), r.get("bvid", ""), r["title"],
                r.get("author", ""), r.get("category", "其他"), r.get("description", ""),
                r.get("duration", 0), r.get("view_count", 0), r.get("like_count", 0),
                r.get("coin_count", 0), r.get("favorite_count", 0), r.get("share_count", 0),
                r.get("reply_count", 0), r.get("pubdate", 0),
                r.get("source", "bilibili_ranking"), r.get("crawled_at", "")
            ))
            count += 1
        except Exception as e:
            logger.warning(f"视频入库失败 {r.get('bvid')}: {e}")
    conn.commit()
    conn.close()
    return count


def crawl_all_categories(limit_per_category: int = 100, db_path: str = "data/tiktok_baseline.db") -> Dict:
    """采集所有分类的 Bilibili 视频数据"""
    init_video_table(db_path)
    total_saved = 0

    # 采集主要分类（全站、音乐、游戏、娱乐、科技、美食）
    main_rids = [0, 3, 4, 5, 36, 119]

    for rid in main_rids:
        cat_name = BILIBILI_CATEGORIES.get(rid, f"rid_{rid}")
        logger.info(f"=== 采集 Bilibili {cat_name} (rid={rid}) ===")
        records = fetch_bilibili_ranking(rid, limit_per_category)
        saved = save_video_records(records, db_path)
        total_saved += saved
        logger.info(f"Bilibili[{cat_name}] 入库 {saved} 条")
        time.sleep(0.5)

    return {"total_saved": total_saved}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    import sqlite3
    conn = sqlite3.connect("data/tiktok_baseline.db")
    before = conn.execute("SELECT COUNT(*) FROM video_database").fetchone()[0]
    conn.close()

    result = crawl_all_categories(limit_per_category=100)

    conn = sqlite3.connect("data/tiktok_baseline.db")
    after = conn.execute("SELECT COUNT(*) FROM video_database").fetchone()[0]
    per_cat = conn.execute("SELECT category, COUNT(*) FROM video_database GROUP BY category").fetchall()
    conn.close()

    print(f"\n采集前: {before}条 → 采集后: {after}条")
    print(f"各品类: {dict(per_cat)}")
    print(f"新增: {after - before}条")
