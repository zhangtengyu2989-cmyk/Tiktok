"""
QQ音乐热榜爬虫
官方接口，无反爬
"""
import requests
import logging
from typing import List, Dict

logger = logging.getLogger("tiktokrx.crawler.qq")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://y.qq.com/",
    "Accept": "application/json",
}

# QQ音乐巅峰榜接口（公开API）
QQ_HOT_URL = "https://c.y.qq.com/node/pc/hot_search_list.html"
QQ_NEWSONG_URL = "https://c.y.qq.com/node/pc/new_song.html"


def fetch_qq_music_hot(limit: int = 50) -> List[Dict]:
    """获取QQ音乐热歌榜"""
    try:
        params = {
            "page": 1,
            "pagesize": limit,
            "topid": 4,  # 4=热歌榜
            "sort": 1,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
        }
        resp = requests.get(
            "https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg",
            params={**params, "type": "top"},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        songs = data.get("songlist") or []
        results = []
        for song in songs[:limit]:
            info = song.get("data") or {}
            results.append({
                "song_name": info.get("songname", "").strip(),
                "artist": "/".join([a.get("name", "") for a in info.get("singer", [])]),
                "album": info.get("albumname", ""),
                "interval": info.get("interval", 0),
                "songmid": info.get("songmid", ""),
                "source": "qq_music",
                "heat_index": song.get("rank", 0),
            })
        logger.info(f"QQ音乐获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"QQ音乐爬取失败: {e}")
        return []


def fetch_qq_music_new(limit: int = 50) -> List[Dict]:
    """获取QQ音乐新歌榜"""
    try:
        params = {
            "page": 1,
            "pagesize": limit,
            "topid": 3,  # 3=新歌榜
            "sort": 1,
        }
        resp = requests.get(
            "https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg",
            params={**params, "type": "top"},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        songs = data.get("songlist") or []
        results = []
        for song in songs[:limit]:
            info = song.get("data") or {}
            results.append({
                "song_name": info.get("songname", "").strip(),
                "artist": "/".join([a.get("name", "") for a in info.get("singer", [])]),
                "album": info.get("albumname", ""),
                "interval": info.get("interval", 0),
                "songmid": info.get("songmid", ""),
                "source": "qq_music_new",
                "heat_index": song.get("rank", 0),
            })
        logger.info(f"QQ新歌获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"QQ新歌榜爬取失败: {e}")
        return []


if __name__ == "__main__":
    print("=== QQ音乐热歌榜 ===")
    for s in fetch_qq_music_hot(10):
        print(f"  {s['song_name']} - {s['artist']}")
