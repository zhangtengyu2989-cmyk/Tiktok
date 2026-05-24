"""
咪咕音乐热榜爬虫
中国移动旗下音乐平台
"""
import requests
import logging
from typing import List, Dict

logger = logging.getLogger("tiktokrx.crawler.migu")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://music.migu.cn/",
    "Accept": "application/json",
}


def fetch_migu_music_hot(limit: int = 100) -> List[Dict]:
    """获取咪咕音乐热歌榜"""
    try:
        # 咪咕音乐新版API
        resp = requests.get(
            "https://music.migu.cn/v3/api/music/song/getRcmdSongList",
            params={"size": limit, "type": 1},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        songs = data.get("result", {}).get("songList", []) or []
        for i, song in enumerate(songs[:limit]):
            results.append({
                "song_name": song.get("name", "").strip(),
                "artist": song.get("artistName", "").strip(),
                "album": song.get("albumName", ""),
                "duration": song.get("duration", 0),
                "song_id": str(song.get("id", "")),
                "source": "migu",
                "heat_index": i + 1,
            })
        logger.info(f"咪咕音乐获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"咪咕音乐爬取失败: {e}")
        return fetch_migu_from_page(limit)


def fetch_migu_from_page(limit: int = 100) -> List[Dict]:
    """从HTML页面解析咪咕热榜"""
    try:
        resp = requests.get(
            "https://music.migu.cn/v3/music/rank/RCH05",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()

        import re
        content = resp.text

        # 咪咕页面歌曲解析模式
        pattern = r'"songName":"([^"]+)".*?"artistName":"([^"]+)"'
        matches = re.findall(pattern, content)

        results = []
        for i, (name, artist) in enumerate(matches[:limit]):
            results.append({
                "song_name": name.strip(),
                "artist": artist.strip(),
                "album": "",
                "duration": 0,
                "song_id": "",
                "source": "migu",
                "heat_index": i + 1,
            })

        logger.info(f"咪咕音乐页面解析获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"咪咕音乐页面解析失败: {e}")
        return []


def fetch_migu_new_songs(limit: int = 50) -> List[Dict]:
    """获取咪咕音乐新歌榜"""
    try:
        resp = requests.get(
            "https://music.migu.cn/v3/api/music/song/getRcmdSongList",
            params={"size": limit, "type": 2},
            headers=HEADERS,
            timeout=15,
        )
        data = resp.json()

        results = []
        songs = data.get("result", {}).get("songList", []) or []
        for i, song in enumerate(songs[:limit]):
            results.append({
                "song_name": song.get("name", "").strip(),
                "artist": song.get("artistName", "").strip(),
                "album": song.get("albumName", ""),
                "duration": song.get("duration", 0),
                "song_id": str(song.get("id", "")),
                "source": "migu_new",
                "heat_index": i + 1,
            })
        logger.info(f"咪咕新歌获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"咪咕新歌榜爬取失败: {e}")
        return []


if __name__ == "__main__":
    print("=== 咪咕音乐热歌榜 ===")
    for s in fetch_migu_music_hot(10):
        print(f"  {s['song_name']} - {s['artist']}")
