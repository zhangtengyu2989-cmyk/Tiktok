"""
Apple Music 热歌榜爬虫
获取各地区Apple Music热门歌曲榜单
"""
import requests
import logging
from typing import List, Dict

logger = logging.getLogger("tiktokrx.crawler.apple")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def fetch_apple_music_hot_songs(limit: int = 100, region: str = "cn") -> List[Dict]:
    """
    获取Apple Music热门歌曲榜
    region: cn(中国), us(美国), jp(日本), kr(韩国), hk(香港), tw(台湾)
    """
    try:
        # Apple Music API endpoint
        url = f"https://r.music.apple.com/cn/v1/catalog/{region}/charts?types=songs"

        resp = requests.get(
            url,
            headers={
                **HEADERS,
                "Origin": "https://music.apple.com",
                "Referer": f"https://music.apple.com/{region}/charts",
            },
            timeout=15,
        )
        resp.raise_for_status()

        data = resp.json()
        results = []

        # 解析响应结构
        # Apple Music API返回结构: data[0].data[].attributes
        for i, item in enumerate(data.get("data", [])[:limit]):
            attrs = item.get("attributes", {})
            results.append({
                "song_name": attrs.get("name", "").strip(),
                "artist": attrs.get("artistName", "").strip(),
                "album": attrs.get("albumName", ""),
                "duration": attrs.get("durationInMillis", 0) // 1000,  # 毫秒转秒
                "song_id": item.get("id", ""),
                "source": f"apple_music_{region}",
                "heat_index": i + 1,
            })

        logger.info(f"Apple Music {region}获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"Apple Music {region}爬取失败: {e}")
        return []


def fetch_apple_music_china(limit: int = 100) -> List[Dict]:
    """获取Apple Music中国区热门歌曲"""
    return fetch_apple_music_hot_songs(limit, "cn")


def fetch_apple_music_us(limit: int = 100) -> List[Dict]:
    """获取Apple Music美国区热门歌曲"""
    return fetch_apple_music_hot_songs(limit, "us")


def fetch_apple_music_hk(limit: int = 100) -> List[Dict]:
    """获取Apple Music香港区热门歌曲"""
    return fetch_apple_music_hot_songs(limit, "hk")


def fetch_apple_music_tw(limit: int = 100) -> List[Dict]:
    """获取Apple Music台湾区热门歌曲"""
    return fetch_apple_music_hot_songs(limit, "tw")


def fetch_apple_music_kr(limit: int = 100) -> List[Dict]:
    """获取Apple Music韩国区热门歌曲"""
    return fetch_apple_music_hot_songs(limit, "kr")


def fetch_apple_music_jp(limit: int = 100) -> List[Dict]:
    """获取Apple Music日本区热门歌曲"""
    return fetch_apple_music_hot_songs(limit, "jp")


if __name__ == "__main__":
    print("=== Apple Music 中国区热歌榜 ===")
    for s in fetch_apple_music_china(10):
        print(f"  {s['song_name']} - {s['artist']}")
