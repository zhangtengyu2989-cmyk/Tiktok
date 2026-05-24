"""
BGM 数据采集主程序
从多个平台采集热歌数据，映射到抖音BGM，写入SQLite
"""
import sqlite3
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional

from .music_chart_spiders.qq_music import fetch_qq_music_hot, fetch_qq_music_new
from .music_chart_spiders.netease import fetch_netease_hot, fetch_netease_douyin_hot
from .music_chart_spiders.douyin_music import fetch_douyin_music_chart
from .music_chart_spiders.kugou import fetch_kugou_hot, fetch_kugou_new_songs
from .music_chart_spiders.apple_music import (
    fetch_apple_music_china, fetch_apple_music_us,
    fetch_apple_music_hk, fetch_apple_music_tw,
    fetch_apple_music_kr, fetch_apple_music_jp
)
from .music_chart_spiders.spotify import fetch_spotify_viral_global, fetch_spotify_regional
from .bgm_mapper import fuzzy_match, estimate_heat_by_name, KNOWN_DOUBIN_BGMS

logger = logging.getLogger("tiktokrx.crawler")

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


def get_heat_index_from_level(level: str) -> int:
    """热度等级转估算播放量（万）"""
    mapping = {"S+": 150, "S": 80, "A": 30, "B": 5, "C": 1}
    return mapping.get(level, 1)


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
    return "动感"  # 默认


def normalize_record(raw: Dict) -> Optional[Dict]:
    """标准化一条记录，尝试匹配抖音BGM"""
    song_name = raw.get("song_name", "").strip()
    artist = raw.get("artist", "").strip()
    if not song_name:
        return None

    # 尝试模糊匹配抖音BGM
    douyin_info = fuzzy_match(song_name, artist)
    if douyin_info:
        return {
            "song_name": song_name,
            "artist": artist,
            "bgm_name": douyin_info.get("bgm_name", song_name),
            "style": douyin_info.get("style", infer_bgm_style(song_name, artist)),
            "categories": ",".join(douyin_info.get("categories", [])),
            "heat_index": raw.get("heat_index", 0),
            "heat_level": get_heat_level(raw.get("heat_index", 9999)),
            "source": raw.get("source", "unknown"),
            "douyin_matched": True,
        }

    # 未匹配，按原数据+估算热度入库
    heat = raw.get("heat_index", 0) or estimate_heat_by_name(song_name)
    return {
        "song_name": song_name,
        "artist": artist,
        "bgm_name": song_name,
        "style": infer_bgm_style(song_name, artist),
        "categories": "",
        "heat_index": heat,
        "heat_level": get_heat_level(heat),
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(bgm_name, source)
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
    logger.info("BGM表初始化完成")


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
            # 先尝试更新已有记录
            existing = conn.execute(
                "SELECT id FROM bgm_database WHERE bgm_name=? AND source=?",
                (r["bgm_name"], source)
            ).fetchone()
            if existing:
                conn.execute("""
                    UPDATE bgm_database SET
                        heat_index=?, heat_level=?, updated_at=CURRENT_TIMESTAMP
                    WHERE bgm_name=? AND source=?
                """, (r["heat_index"], r["heat_level"], r["bgm_name"], source))
            else:
                conn.execute("""
                    INSERT INTO bgm_database
                    (song_name, artist, bgm_name, style, categories, heat_index, heat_level, source, douyin_matched)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r["song_name"], r["artist"], r["bgm_name"], r["style"],
                    r.get("categories", ""), r["heat_index"], r["heat_level"],
                    source, 1 if r.get("douyin_matched") else 0
                ))
            count += 1
        except Exception as e:
            logger.warning(f"入库失败 {r.get('song_name')}: {e}")
    conn.commit()
    # 记录爬取日志
    matched = sum(1 for r in records if r and r.get("douyin_matched"))
    conn.execute("""
        INSERT INTO bgm_crawl_log (source, count, douyin_matched_count)
        VALUES (?, ?, ?)
    """, (source, count, matched))
    conn.commit()
    conn.close()
    logger.info(f"[{source}] 保存 {count} 条，抖音匹配 {matched} 条")
    return count


def seed_known_bgm_mappings(db_path: str = DB_PATH) -> int:
    """从已知BGM映射表批量入库抖音热门BGM（确保基础数据）"""
    records = []
    for (song_name, artist), info in KNOWN_DOUBIN_BGMS.items():
        records.append({
            "song_name": song_name,
            "artist": artist or "",
            "bgm_name": info.get("bgm_name", song_name),
            "style": info.get("style", "动感"),
            "categories": ",".join(info.get("categories", [])),
            "heat_index": 100,  # 预设中等热度
            "heat_level": "A",  # 预设A级
            "source": "known_mapping",
            "douyin_matched": True,
        })
    return save_bgm_records(records, "known_mapping", db_path)


def crawl_all(db_path: str = DB_PATH) -> Dict[str, int]:
    """从所有平台采集BGM数据"""
    init_bgm_table(db_path)
    results = {}

    # 0. 从已知BGM映射表入库（确保基础数据）
    logger.info("正在导入已知BGM映射表...")
    results["known_mapping"] = seed_known_bgm_mappings(db_path)

    # 1. QQ音乐热歌榜
    logger.info("开始采集 QQ音乐热歌榜...")
    raw_qq = fetch_qq_music_hot(100)
    records_qq = [normalize_record(r) for r in raw_qq]
    results["qq_music"] = save_bgm_records(records_qq, "qq_music", db_path)
    time.sleep(1)

    # 2. QQ音乐新歌榜
    logger.info("开始采集 QQ音乐新歌榜...")
    raw_qq_new = fetch_qq_music_new(50)
    records_qq_new = [normalize_record(r) for r in raw_qq_new]
    results["qq_music_new"] = save_bgm_records(records_qq_new, "qq_music_new", db_path)

    total = sum(results.values())
    logger.info(f"全部采集完成，共入库 {total} 条记录")
    return results


def get_hot_bgm(limit: int = 20, db_path: str = DB_PATH) -> List[Dict]:
    """获取热门BGM列表"""
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT bgm_name, artist, style, categories, heat_index, heat_level, source
        FROM bgm_database
        ORDER BY heat_index DESC, heat_level ASC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [
        {"bgm_name": r[0], "artist": r[1], "style": r[2], "categories": r[3],
         "heat_index": r[4], "heat_level": r[5], "source": r[6]}
        for r in rows
    ]


def search_bgm(keyword: str, db_path: str = DB_PATH) -> List[Dict]:
    """搜索BGM"""
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT bgm_name, artist, style, categories, heat_index, heat_level, source
        FROM bgm_database
        WHERE bgm_name LIKE ? OR artist LIKE ? OR categories LIKE ?
        ORDER BY heat_index DESC
        LIMIT 20
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")).fetchall()
    conn.close()
    return [
        {"bgm_name": r[0], "artist": r[1], "style": r[2], "categories": r[3],
         "heat_index": r[4], "heat_level": r[5], "source": r[6]}
        for r in rows
    ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    result = crawl_all()
    print(f"采集结果: {result}")
