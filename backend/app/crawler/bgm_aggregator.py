"""
BGM数据聚合器
统一调度各平台爬虫，去重后存入数据库
"""
import sqlite3
import logging
import time
import hashlib
from typing import List, Dict, Optional, Callable
from datetime import datetime

from .music_chart_spiders.qq_music import fetch_qq_music_hot, fetch_qq_music_new
from .music_chart_spiders.douyin_music import fetch_douyin_music_chart
from .music_chart_spiders.kugou import fetch_kugou_hot, fetch_kugou_new_songs
from .music_chart_spiders.kuwo import fetch_kuwo_music_hot, fetch_kuwo_new_songs
from .music_chart_spiders.migu import fetch_migu_music_hot, fetch_migu_new_songs
from .music_chart_spiders.apple_music import (
    fetch_apple_music_china, fetch_apple_music_us,
    fetch_apple_music_hk, fetch_apple_music_tw,
    fetch_apple_music_kr, fetch_apple_music_jp
)
from .music_chart_spiders.spotify import fetch_spotify_viral_global, fetch_spotify_regional
from .music_chart_spiders.youtube_music import fetch_youtube_trending_fallback
from .bgm_mapper import fuzzy_match, estimate_heat_by_name

logger = logging.getLogger("tiktokrx.bgm_aggregator")

DB_PATH = "data/tiktok_baseline.db"


def get_heat_level(heat_index: int) -> str:
    """根据排名估算热度等级"""
    if heat_index <= 10:
        return "S+"
    elif heat_index <= 30:
        return "S"
    elif heat_index <= 100:
        return "A"
    elif heat_index <= 300:
        return "B"
    return "C"


def infer_bgm_style(song_name: str, artist: str = "") -> str:
    """根据歌名/艺术家推断BGM风格"""
    name = (song_name + artist).lower()
    if any(k in name for k in ["欢快", "快乐", "happy", "joy"]):
        return "欢快"
    if any(k in name for k in ["抒情", "温柔", "安静", "钢琴", "吉他"]):
        return "舒缓"
    if any(k in name for k in ["动感", "舞曲", "disco", "dance", "电子"]):
        return "动感"
    if any(k in name for k in ["古风", "中国", "民谣", "山河"]):
        return "大气"
    if any(k in name for k in ["温馨", "治愈", "暖", "家"]):
        return "温馨"
    if any(k in name for k in ["搞笑", "幽默", "沙雕"]):
        return "欢快"
    if any(k in name for k in ["潮流", "hip", "rap", "说唱"]):
        return "潮流"
    return "动感"


def normalize_record(raw: Dict) -> Optional[Dict]:
    """标准化一条记录"""
    song_name = raw.get("song_name", "").strip()
    artist = raw.get("artist", "").strip()
    if not song_name or len(song_name) < 2:
        return None

    douyin_info = fuzzy_match(song_name, artist)
    heat_index = raw.get("heat_index", 0) or estimate_heat_by_name(song_name)

    if douyin_info:
        return {
            "song_name": song_name,
            "artist": artist,
            "bgm_name": douyin_info.get("bgm_name", song_name),
            "style": douyin_info.get("style", infer_bgm_style(song_name, artist)),
            "categories": ",".join(douyin_info.get("categories", [])),
            "heat_index": heat_index,
            "heat_level": get_heat_level(heat_index),
            "source": raw.get("source", "unknown"),
            "douyin_matched": True,
        }

    return {
        "song_name": song_name,
        "artist": artist,
        "bgm_name": song_name,
        "style": infer_bgm_style(song_name, artist),
        "categories": "",
        "heat_index": heat_index,
        "heat_level": get_heat_level(heat_index),
        "source": raw.get("source", "unknown"),
        "douyin_matched": False,
    }


def init_bgm_table(db_path: str = DB_PATH) -> None:
    """初始化BGM数据库表"""
    conn = sqlite3.connect(db_path)
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bgm_crawl_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            count INTEGER,
            douyin_matched_count INTEGER,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_bgm_records(records: List[Dict], source: str, db_path: str = DB_PATH) -> int:
    """保存BGM记录到数据库，返回新增/更新数量"""
    if not records:
        return 0
    conn = sqlite3.connect(db_path)
    count = 0
    for r in records:
        if not r:
            continue
        try:
            existing = conn.execute(
                "SELECT id FROM bgm_database WHERE song_name=? AND artist=? AND source=?",
                (r["song_name"], r["artist"], source)
            ).fetchone()
            if existing:
                conn.execute("""
                    UPDATE bgm_database SET
                        bgm_name=?, style=?, categories=?,
                        heat_index=?, heat_level=?, updated_at=CURRENT_TIMESTAMP
                    WHERE song_name=? AND artist=? AND source=?
                """, (r["bgm_name"], r["style"], r.get("categories", ""),
                      r["heat_index"], r["heat_level"],
                      r["song_name"], r["artist"], source))
            else:
                conn.execute("""
                    INSERT INTO bgm_database
                    (song_name, artist, bgm_name, style, categories, heat_index, heat_level, source, douyin_matched, song_id, album, duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r["song_name"], r["artist"], r["bgm_name"], r["style"],
                    r.get("categories", ""), r["heat_index"], r["heat_level"],
                    source, 1 if r.get("douyin_matched") else 0,
                    r.get("song_id", ""), r.get("album", ""), r.get("duration", 0)
                ))
            count += 1
        except Exception as e:
            logger.warning(f"入库失败 {r.get('song_name')}: {e}")
    conn.commit()
    matched = sum(1 for r in records if r and r.get("douyin_matched"))
    conn.execute("""
        INSERT INTO bgm_crawl_log (source, count, douyin_matched_count)
        VALUES (?, ?, ?)
    """, (source, count, matched))
    conn.commit()
    conn.close()
    logger.info(f"[{source}] 保存 {count} 条，抖音匹配 {matched} 条")
    return count


PLATFORM_CONFIGS = {
    # QQ音乐
    "qq_music": {
        "fetcher": fetch_qq_music_hot,
        "limit": 100,
        "delay": 1,
        "enabled": True,
    },
    "qq_music_new": {
        "fetcher": fetch_qq_music_new,
        "limit": 50,
        "delay": 1,
        "enabled": True,
    },
    # 抖音音乐
    "douyin_music": {
        "fetcher": fetch_douyin_music_chart,
        "limit": 100,
        "delay": 1,
        "enabled": True,
    },
    # 酷狗音乐
    "kugou": {
        "fetcher": fetch_kugou_hot,
        "limit": 100,
        "delay": 2,
        "enabled": True,
    },
    "kugou_new": {
        "fetcher": fetch_kugou_new_songs,
        "limit": 50,
        "delay": 2,
        "enabled": True,
    },
    # 酷我音乐
    "kuwo": {
        "fetcher": fetch_kuwo_music_hot,
        "limit": 100,
        "delay": 2,
        "enabled": True,
    },
    "kuwo_new": {
        "fetcher": fetch_kuwo_new_songs,
        "limit": 50,
        "delay": 2,
        "enabled": True,
    },
    # 咪咕音乐
    "migu": {
        "fetcher": fetch_migu_music_hot,
        "limit": 100,
        "delay": 2,
        "enabled": True,
    },
    "migu_new": {
        "fetcher": fetch_migu_new_songs,
        "limit": 50,
        "delay": 2,
        "enabled": True,
    },
    # Apple Music 多地区
    "apple_cn": {
        "fetcher": fetch_apple_music_china,
        "limit": 100,
        "delay": 1,
        "enabled": True,
    },
    "apple_us": {
        "fetcher": fetch_apple_music_us,
        "limit": 100,
        "delay": 1,
        "enabled": True,
    },
    "apple_jp": {
        "fetcher": fetch_apple_music_jp,
        "limit": 100,
        "delay": 1,
        "enabled": True,
    },
    "apple_kr": {
        "fetcher": fetch_apple_music_kr,
        "limit": 100,
        "delay": 1,
        "enabled": True,
    },
    # Spotify
    "spotify": {
        "fetcher": fetch_spotify_viral_global,
        "limit": 100,
        "delay": 2,
        "enabled": True,
    },
    # YouTube Music
    "youtube_music": {
        "fetcher": fetch_youtube_trending_fallback,
        "limit": 100,
        "delay": 2,
        "enabled": True,
    },
}


def crawl_platform(platform: str, db_path: str = DB_PATH) -> Dict:
    """采集单个平台的数据"""
    config = PLATFORM_CONFIGS.get(platform)
    if not config:
        return {"platform": platform, "status": "error", "message": "Unknown platform"}

    if not config.get("enabled", True):
        return {"platform": platform, "status": "skipped", "message": "Platform disabled"}

    fetcher: Callable = config["fetcher"]
    limit = config["limit"]
    delay = config["delay"]

    try:
        logger.info(f"开始采集 {platform}...")
        raw_data = fetcher(limit)
        if not raw_data:
            logger.warning(f"{platform} 返回空数据")
            return {"platform": platform, "status": "empty", "count": 0}

        records = [normalize_record(r) for r in raw_data]
        records = [r for r in records if r]

        saved = save_bgm_records(records, platform, db_path)
        logger.info(f"{platform} 采集完成，获取 {len(raw_data)} 条，入库 {saved} 条")

        time.sleep(delay)

        return {
            "platform": platform,
            "status": "success",
            "raw_count": len(raw_data),
            "saved_count": saved,
        }
    except Exception as e:
        logger.error(f"{platform} 采集失败: {e}")
        return {"platform": platform, "status": "error", "message": str(e)}


def crawl_all(db_path: str = DB_PATH, platforms: List[str] = None) -> Dict[str, int]:
    """从所有启用的平台采集BGM数据"""
    init_bgm_table(db_path)
    results = {}
    stats = {"total_raw": 0, "total_saved": 0, "failed": []}

    targets = platforms if platforms else [k for k, v in PLATFORM_CONFIGS.items() if v.get("enabled", True)]

    for platform in targets:
        result = crawl_platform(platform, db_path)
        if result["status"] == "success":
            results[platform] = result["saved_count"]
            stats["total_raw"] += result["raw_count"]
            stats["total_saved"] += result["saved_count"]
        elif result["status"] == "error":
            stats["failed"].append({platform: result.get("message", "Unknown error")})

    logger.info(f"全部采集完成，共入库 {stats['total_saved']} 条记录，失败 {len(stats['failed'])} 个平台")
    return results


def get_bgm_stats(db_path: str = DB_PATH) -> Dict:
    """获取BGM数据库统计信息"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    total = cursor.execute("SELECT COUNT(*) FROM bgm_database").fetchone()[0]
    matched = cursor.execute("SELECT COUNT(*) FROM bgm_database WHERE douyin_matched=1").fetchone()[0]

    source_stats = cursor.execute("""
        SELECT source, COUNT(*) as cnt, SUM(CASE WHEN douyin_matched=1 THEN 1 ELSE 0 END) as matched
        FROM bgm_database
        GROUP BY source
        ORDER BY cnt DESC
    """).fetchall()

    style_stats = cursor.execute("""
        SELECT style, COUNT(*) as cnt
        FROM bgm_database
        GROUP BY style
        ORDER BY cnt DESC
    """).fetchall()

    level_stats = cursor.execute("""
        SELECT heat_level, COUNT(*) as cnt
        FROM bgm_database
        GROUP BY heat_level
    """).fetchall()

    recent_crawl = cursor.execute("""
        SELECT source, count, douyin_matched_count, crawled_at
        FROM bgm_crawl_log
        ORDER BY crawled_at DESC
        LIMIT 20
    """).fetchall()

    conn.close()

    return {
        "total": total,
        "douyin_matched": matched,
        "match_rate": round(matched / total * 100, 1) if total > 0 else 0,
        "by_source": [{"source": s, "count": c, "matched": m} for s, c, m, _ in source_stats],
        "by_style": [{"style": s, "count": c} for s, c in style_stats],
        "by_level": [{"level": l, "count": c} for l, c in level_stats],
        "recent_crawl": [{"source": s, "count": c, "matched": m, "at": str(t)} for s, c, m, t in recent_crawl],
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    print("=== BGM 聚合采集 ===")
    results = crawl_all()
    print(f"采集结果: {results}")
    print("\n=== 数据库统计 ===")
    stats = get_bgm_stats()
    print(f"总计: {stats['total']} 条，抖音匹配: {stats['douyin_matched']} 条 ({stats['match_rate']}%)")
    print("\n各平台统计:")
    for s in stats["by_source"]:
        print(f"  {s['source']}: {s['count']} 条 (匹配 {s['matched']} 条)")
