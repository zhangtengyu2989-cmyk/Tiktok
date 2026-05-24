"""
酷我音乐热榜爬虫
"""
import requests
import logging
from typing import List, Dict

logger = logging.getLogger("tiktokrx.crawler.kuwo")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.kuwo.cn/",
    "Accept": "application/json",
}


def fetch_kuwo_music_hot(limit: int = 100) -> List[Dict]:
    """获取酷我音乐热歌榜"""
    try:
        # 酷我音乐API
        params = {
            "format": "json",
            "pn": 0,
            "rn": limit,
            "type": "hot",
            "httpsStatus": 1,
        }
        resp = requests.get(
            "http://www.kuwo.cn/api/www/bang/bang/musicList",
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        songs = data.get("data", {}).get("musicList", []) or []
        for i, song in enumerate(songs[:limit]):
            results.append({
                "song_name": song.get("name", "").strip(),
                "artist": song.get("artist", "").strip(),
                "album": song.get("album", ""),
                "duration": song.get("duration", 0),
                "song_id": str(song.get("rid", "")),
                "source": "kuwo",
                "heat_index": i + 1,
            })
        logger.info(f"酷我音乐获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"酷我音乐爬取失败: {e}")
        return fetch_kuwo_from_page(limit)


def fetch_kuwo_from_page(limit: int = 100) -> List[Dict]:
    """从HTML页面解析酷我热榜"""
    try:
        resp = requests.get(
            "https://www.kuwo.cn/rank",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()

        import re
        content = resp.text

        # 解析酷我页面歌曲
        pattern = r'"name":"([^"]+)".*?"artist":"([^"]+)"'
        matches = re.findall(pattern, content)

        results = []
        for i, (name, artist) in enumerate(matches[:limit]):
            results.append({
                "song_name": name.strip(),
                "artist": artist.strip(),
                "album": "",
                "duration": 0,
                "song_id": "",
                "source": "kuwo",
                "heat_index": i + 1,
            })

        logger.info(f"酷我音乐页面解析获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"酷我音乐页面解析失败: {e}")
        return []


def fetch_kuwo_new_songs(limit: int = 50) -> List[Dict]:
    """获取酷我音乐新歌榜"""
    try:
        params = {
            "format": "json",
            "pn": 0,
            "rn": limit,
            "type": "new",
            "httpsStatus": 1,
        }
        resp = requests.get(
            "http://www.kuwo.cn/api/www/bang/bang/musicList",
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        data = resp.json()

        results = []
        songs = data.get("data", {}).get("musicList", []) or []
        for i, song in enumerate(songs[:limit]):
            results.append({
                "song_name": song.get("name", "").strip(),
                "artist": song.get("artist", "").strip(),
                "album": song.get("album", ""),
                "duration": song.get("duration", 0),
                "song_id": str(song.get("rid", "")),
                "source": "kuwo_new",
                "heat_index": i + 1,
            })
        logger.info(f"酷我新歌获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"酷我新歌榜爬取失败: {e}")
        return []


if __name__ == "__main__":
    print("=== 酷我音乐热歌榜 ===")
    for s in fetch_kuwo_music_hot(10):
        print(f"  {s['song_name']} - {s['artist']}")
