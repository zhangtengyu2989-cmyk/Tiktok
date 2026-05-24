"""
网易云音乐热榜爬虫
使用官方公开接口
"""
import requests
import logging
from typing import List, Dict

logger = logging.getLogger("tiktokrx.crawler.netease")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://music.163.com/",
}

# 网易云音乐榜单API（官方公开接口）
NETEASE_HOT_URL = "https://music.163.com/api/v1/play/hat/lists"


def fetch_netease_hot(limit: int = 50) -> List[Dict]:
    """获取网易云音乐热歌榜"""
    try:
        resp = requests.get(
            "https://music.163.com/api/top/list?idx=1",
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        tracks = data.get("tracks") or []
        results = []
        for i, track in enumerate(tracks[:limit]):
            results.append({
                "song_name": track.get("name", "").strip(),
                "artist": "/".join([a.get("name", "") for a in track.get("artists", [])]),
                "album": track.get("album", {}).get("name", ""),
                "duration": track.get("duration", 0) // 1000,  # 毫秒转秒
                "song_id": track.get("id", ""),
                "source": "netease_cloud",
                "heat_index": i + 1,  # 排名即热度
            })
        logger.info(f"网易云获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"网易云热歌榜爬取失败: {e}")
        return []


def fetch_netease_douyin_hot(limit: int = 50) -> List[Dict]:
    """获取网易云音乐抖音专区热歌榜"""
    try:
        # 网易云有抖音专区榜单
        resp = requests.get(
            "https://music.163.com/api/top/list?idx=26",  # 26=抖音排行榜
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        tracks = data.get("tracks") or []
        results = []
        for i, track in enumerate(tracks[:limit]):
            results.append({
                "song_name": track.get("name", "").strip(),
                "artist": "/".join([a.get("name", "") for a in track.get("artists", [])]),
                "album": track.get("album", {}).get("name", ""),
                "duration": track.get("duration", 0) // 1000,
                "song_id": track.get("id", ""),
                "source": "netease_douyin",
                "heat_index": i + 1,
            })
        logger.info(f"网易云抖音榜获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"网易云抖音榜爬取失败: {e}")
        return []


if __name__ == "__main__":
    print("=== 网易云热歌榜 ===")
    for s in fetch_netease_hot(10):
        print(f"  {s['song_name']} - {s['artist']}")
