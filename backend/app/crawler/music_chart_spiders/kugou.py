"""
酷狗音乐热榜爬虫
官方公开接口
"""
import requests
import logging
from typing import List, Dict

logger = logging.getLogger("tiktokrx.crawler.kugou")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.kugou.com/",
}


def fetch_kugou_hot(limit: int = 100) -> List[Dict]:
    """获取酷狗音乐热歌榜"""
    try:
        # 酷狗音乐PC版热榜API
        resp = requests.get(
            "https://www.kugou.com/yy/html/rank.html",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()

        # 使用酷狗音乐API获取榜单
        params = {
            "page": 1,
            "pagesize": limit,
            "type": 1,  # 1=热榜
        }
        api_resp = requests.get(
            "https://gateway.kugou.com/open/v1/rank/lists",
            params=params,
            headers={
                **HEADERS,
                "kg-rc": "1",
            },
            timeout=10,
        )

        if api_resp.status_code != 200:
            # 备用方案：直接解析HTML
            return fetch_kugou_from_html(limit)

        data = api_resp.json()
        songs = data.get("data", {}).get("lists", []) or []
        results = []
        for i, song in enumerate(songs[:limit]):
            results.append({
                "song_name": song.get("name", "").strip(),
                "artist": song.get("author_name", "").strip(),
                "album": song.get("album_name", ""),
                "duration": song.get("duration", 0),
                "song_id": str(song.get("id", "")),
                "source": "kugou",
                "heat_index": i + 1,
            })
        logger.info(f"酷狗音乐获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"酷狗音乐爬取失败: {e}，尝试备用方案")
        return fetch_kugou_from_html(limit)


def fetch_kugou_from_html(limit: int = 100) -> List[Dict]:
    """从HTML页面解析酷狗热榜"""
    try:
        resp = requests.get(
            "https://www.kugou.com/yy/html/rank.html",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        # 简单解析（实际生产环境建议用BeautifulSoup）
        content = resp.text
        results = []
        import re
        # 匹配歌曲信息模式
        pattern = r'"name":"([^"]+)".*?"author":"([^"]+)"'
        matches = re.findall(pattern, content)
        for i, (name, author) in enumerate(matches[:limit]):
            results.append({
                "song_name": name.strip(),
                "artist": author.strip(),
                "album": "",
                "duration": 0,
                "song_id": "",
                "source": "kugou",
                "heat_index": i + 1,
            })
        logger.info(f"酷狗音乐HTML解析获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"酷狗HTML解析失败: {e}")
        return []


def fetch_kugou_new_songs(limit: int = 50) -> List[Dict]:
    """获取酷狗音乐新歌榜"""
    try:
        # 酷狗新歌榜
        resp = requests.get(
            "https://gateway.kugou.com/open/v1/rank/lists",
            params={"page": 1, "pagesize": limit, "type": 2},
            headers={
                **HEADERS,
                "kg-rc": "1",
            },
            timeout=10,
        )
        data = resp.json()
        songs = data.get("data", {}).get("lists", []) or []
        results = []
        for i, song in enumerate(songs[:limit]):
            results.append({
                "song_name": song.get("name", "").strip(),
                "artist": song.get("author_name", "").strip(),
                "album": song.get("album_name", ""),
                "duration": song.get("duration", 0),
                "song_id": str(song.get("id", "")),
                "source": "kugou_new",
                "heat_index": i + 1,
            })
        logger.info(f"酷狗新歌获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"酷狗新歌榜爬取失败: {e}")
        return []


if __name__ == "__main__":
    print("=== 酷狗音乐热歌榜 ===")
    for s in fetch_kugou_hot(10):
        print(f"  {s['song_name']} - {s['artist']}")
