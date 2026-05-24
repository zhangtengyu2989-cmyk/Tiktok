"""
BGM数据扩充爬虫 - 批量采集多平台音乐榜单
目标：每个品类 ≥1000条BGM数据
"""
import requests
import logging
import time
import re
from typing import List, Dict

logger = logging.getLogger("tiktokrx.crawler.bgm_expand")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://y.qq.com/",
    "Accept": "application/json",
}


def get_heat_level_by_rank(rank: int) -> str:
    """
    根据排名估算热度等级
    rank越小表示越热门
    - 排名1-10: S+ (顶级热门)
    - 排名11-30: S (热门)
    - 排名31-100: A (较热门)
    - 排名101-300: B (普通)
    - 排名>300或0: C (冷门)
    """
    if rank <= 0 or rank > 300:
        return "C"
    elif rank <= 10:
        return "S+"
    elif rank <= 30:
        return "S"
    elif rank <= 100:
        return "A"
    elif rank <= 300:
        return "B"
    return "C"

# QQ音乐多个榜单ID
QQ_CHARTS = {
    "hot": {"topid": 4, "name": "QQ音乐巅峰榜·热歌"},
    "new": {"topid": 3, "name": "QQ音乐巅峰榜·新歌"},
    "pc": {"topid": 26, "name": "QQ音乐巅峰榜·PC端"},
    "asia": {"topid": 5, "name": "QQ音乐巅峰榜·亚洲"},
    "america": {"topid": 2, "name": "QQ音乐巅峰榜·欧美"},
    "korean": {"topid": 16, "name": "QQ音乐巅峰榜·韩国"},
    "japan": {"topid": 15, "name": "QQ音乐巅峰榜·日本"},
    "hongkong": {"topid": 1, "name": "QQ音乐巅峰榜·香港"},
    "rap": {"topid": 17, "name": "QQ音乐巅峰榜·说唱"},
    "classical": {"topid": 6, "name": "QQ音乐巅峰榜·古典"},
    "movie": {"topid": 12, "name": "QQ音乐巅峰榜·影视"},
    "cartoon": {"topid": 13, "name": "QQ音乐巅峰榜·动漫"},
}


def fetch_qq_chart(topic: str, chart_id: int, limit: int = 100) -> List[Dict]:
    """获取QQ音乐指定榜单"""
    try:
        resp = requests.get(
            "https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg",
            params={"type": "top", "topid": chart_id, "sort": 1, "page": 1, "pagesize": limit},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        songs = data.get("songlist") or []
        results = []
        for i, song in enumerate(songs[:limit]):
            info = song.get("data") or {}
            song_name = info.get("songname", "").strip()
            if not song_name:
                continue
            artist = "/".join([a.get("name", "") for a in info.get("singer", [])])
            # 使用列表索引+1作为排名（索引从0开始，所以i+1）
            rank = i + 1
            results.append({
                "song_name": song_name,
                "artist": artist,
                "album": info.get("albumname", ""),
                "interval": info.get("interval", 0),
                "songmid": info.get("songmid", ""),
                "rank": rank,
                "heat_index": rank,
                "source": f"qq_{topic}",
                "chart_name": QQ_CHARTS[topic]["name"] if topic in QQ_CHARTS else topic,
            })
        logger.info(f"QQ音乐[{topic}]获取{len(results)}首")
        return results
    except Exception as e:
        logger.warning(f"QQ音乐[{topic}]失败: {e}")
        return []


def fetch_qq_playlist_songs(playlist_id: str, limit: int = 200) -> List[Dict]:
    """从QQ音乐公开歌单获取歌曲"""
    try:
        resp = requests.get(
            "https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids.cfc",
            params={"disstids": playlist_id, "type": 1, "json": 1, "utf8": 1, "onlysong": 0},
            headers={**HEADERS, "Referer": f"https://y.qq.com/n/ryqq/playlist/{playlist_id}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        cdlist = data.get("cdlist", [])
        results = []
        for cd in cdlist:
            songs = cd.get("songlist", []) or []
            for song in songs[:limit]:
                song_name = song.get("songname", "").strip()
                if not song_name:
                    continue
                singer = "/".join([s.get("name", "") for s in song.get("singer", [])])
                results.append({
                    "song_name": song_name,
                    "artist": singer,
                    "album": song.get("albumname", ""),
                    "interval": song.get("interval", 0),
                    "songmid": song.get("songmid", ""),
                    "heat_index": 0,
                    "source": f"qq_playlist_{playlist_id}",
                    "chart_name": f"qq_playlist_{playlist_id}",
                })
        logger.info(f"QQ歌单{playlist_id}获取{len(results)}首")
        return results
    except Exception as e:
        logger.warning(f"QQ歌单{playlist_id}失败: {e}")
        return []


# 已知热门公开歌单ID
# 注意: QQ音乐歌单接口已变更,部分ID可能失效
QQ_PUBLIC_PLAYLISTS = [
    "8679647128",  # 抖音热歌榜
]


def crawl_all_bgm_sources(limit_per_chart: int = 100, db_path: str = "data/tiktok_baseline.db") -> Dict:
    """从所有BGM源批量采集"""
    import sqlite3
    conn = sqlite3.connect(db_path)

    # 确保表存在且有source和chart_name列
    try:
        conn.execute("ALTER TABLE bgm_database ADD COLUMN chart_name TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE bgm_database ADD COLUMN rank INTEGER DEFAULT 0")
    except Exception:
        pass

    total_saved = 0

    # 1. QQ音乐多个榜单
    logger.info("=== 采集QQ音乐多榜单 ===")
    for topic, info in QQ_CHARTS.items():
        records = fetch_qq_chart(topic, info["topid"], limit_per_chart)
        for r in records:
            try:
                # 计算热度等级（根据排名）
                heat_level = get_heat_level_by_rank(r.get("heat_index", 999))
                conn.execute("""
                    INSERT OR IGNORE INTO bgm_database
                    (song_name, artist, heat_index, heat_level, source, chart_name, rank, bgm_name, douyin_matched)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (
                    r["song_name"], r["artist"], r["heat_index"],
                    heat_level, r["source"], r.get("chart_name", ""), r.get("rank", 0),
                    r["song_name"],
                ))
                total_saved += 1
            except Exception:
                pass
        conn.commit()
        time.sleep(0.5)

    # 2. QQ音乐公开歌单
    logger.info("=== 采集QQ音乐公开歌单 ===")
    for pid in QQ_PUBLIC_PLAYLISTS:
        records = fetch_qq_playlist_songs(pid, limit_per_chart)
        for r in records:
            try:
                # 计算热度等级
                heat_level = get_heat_level_by_rank(r.get("heat_index", 999))
                conn.execute("""
                    INSERT OR IGNORE INTO bgm_database
                    (song_name, artist, heat_index, heat_level, source, chart_name, rank, bgm_name, douyin_matched)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (
                    r["song_name"], r["artist"], r["heat_index"],
                    heat_level, r["source"], r.get("chart_name", ""), 0,
                    r["song_name"],
                ))
                total_saved += 1
            except Exception:
                pass
        conn.commit()
        time.sleep(0.3)

    conn.close()
    logger.info(f"BGM批量采集完成，新增{total_saved}条")
    return {"total_saved": total_saved}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    import sqlite3
    conn = sqlite3.connect("data/tiktok_baseline.db")
    before = conn.execute("SELECT COUNT(*) FROM bgm_database").fetchone()[0]
    conn.close()

    result = crawl_all_bgm_sources()

    conn = sqlite3.connect("data/tiktok_baseline.db")
    after = conn.execute("SELECT COUNT(*) FROM bgm_database").fetchone()[0]
    conn.close()

    print(f"\n采集前: {before}条 → 采集后: {after}条")
    print(f"新增: {after - before}条")
