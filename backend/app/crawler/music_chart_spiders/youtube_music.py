"""
YouTube Music Trending 爬虫
获取国际热门音乐趋势
"""
import requests
import logging
from typing import List, Dict

logger = logging.getLogger("tiktokrx.crawler.youtube")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_youtube_music_trending(limit: int = 100, region: str = "US") -> List[Dict]:
    """获取YouTube MusicTrending音乐列表"""
    try:
        # YouTube Music API
        url = "https://www.youtube.com/youtubei/v1/browse"
        data = {
            "context": {
                "client": {
                    "clientName": "WEB_REMIX",
                    "clientVersion": "1.20240601",
                }
            },
            "params": "EgJGBQeBAEBCA%3D%3D",  # music trending
            "query": ""
        }

        resp = requests.post(
            url,
            json=data,
            headers=HEADERS,
            timeout=15,
        )

        if resp.status_code != 200:
            # 备用方案：使用YouTube Data API v3
            return fetch_youtube_trending_fallback(limit, region)

        # 解析响应
        # YouTube Music API响应较复杂，需要完整解析
        results = []
        # ... 解析逻辑

        logger.info(f"YouTube Music获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"YouTube Music爬取失败: {e}")
        return []


def fetch_youtube_trending_fallback(limit: int = 50, region: str = "US") -> List[Dict]:
    """备用方案：通过YouTube视频趋势获取音乐相关视频"""
    try:
        # 获取YouTube trending视频（音乐类别）
        params = {
            "part": "snippet",
            "maxResults": limit,
            "regionCode": region,
            "videoCategoryId": 10,  # 10=Music
            "key": "",  # 需要API Key，留空则尝试无Key方式
        }

        # 尝试不需要API Key的接口
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={**params, "chart": "mostPopular"},
            headers=HEADERS,
            timeout=15,
        )

        if resp.status_code != 200:
            return fetch_youtube_music_videos(limit, region)

        data = resp.json()
        results = []
        for i, item in enumerate(data.get("items", [])[:limit]):
            snippet = item.get("snippet", {})
            title = snippet.get("title", "")
            channel = snippet.get("channelTitle", "")

            results.append({
                "song_name": title,
                "artist": channel,
                "album": "",
                "duration": 0,
                "song_id": item.get("id", ""),
                "source": "youtube_music",
                "heat_index": i + 1,
            })

        logger.info(f"YouTube Music备用方案获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"YouTube备用方案失败: {e}")
        return []


def fetch_youtube_music_videos(limit: int = 50, region: str = "US") -> List[Dict]:
    """获取YouTube音乐视频（通过解析trending页面）"""
    try:
        resp = requests.get(
            f"https://www.youtube.com/channel/UC-9-kyTW8ZkZNDHQJ6FgpwQ/videos",
            headers=HEADERS,
            timeout=15,
        )

        # 从页面提取视频信息
        import re
        content = resp.text

        # 提取视频ID和标题
        pattern = r'"videoId":"([^"]+)","title":"([^"]+)","channelTitle":"([^"]+)"'
        matches = re.findall(pattern, content)

        results = []
        for i, (video_id, title, channel) in enumerate(matches[:limit]):
            results.append({
                "song_name": title[:100],  # 限制长度
                "artist": channel[:50],
                "album": "",
                "duration": 0,
                "song_id": video_id,
                "source": "youtube_music",
                "heat_index": i + 1,
            })

        logger.info(f"YouTube音乐视频获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"YouTube音乐视频获取失败: {e}")
        return []


if __name__ == "__main__":
    print("=== YouTube Music Trending ===")
    for s in fetch_youtube_trending_fallback(10):
        print(f"  {s['song_name']} - {s['artist']}")
