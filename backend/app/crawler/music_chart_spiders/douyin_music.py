"""
抖音音乐榜爬虫
注意：抖音网页版可能需要登录态或人机验证，此处使用备用方案
"""
import requests
import logging
from typing import List, Dict

logger = logging.getLogger("tiktokrx.crawler.douyin")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Referer": "https://www.douyin.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def fetch_douyin_music_chart(limit: int = 50) -> List[Dict]:
    """
    获取抖音热歌榜
    使用字节系公开接口尝试，无Cookie情况下可能降级处理
    """
    try:
        # 抖音音乐开放平台 - 热歌榜（部分公开）
        resp = requests.get(
            "https://www.douyin.com/aweme/v1/music/billboard/list/",
            params={"music_id": "", "aid": "6383", "version_name": "23.5.0"},
            headers={
                **HEADERS,
                "X-Bogus": "",
                "User-Agent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            },
            timeout=10,
            allow_redirects=False,
        )
        if resp.status_code == 200:
            data = resp.json()
            musics = data.get("music_list", [])[:limit]
            results = []
            for i, m in enumerate(musics):
                results.append({
                    "song_name": m.get("title", "").strip(),
                    "artist": m.get("author", ""),
                    "album": "",
                    "music_id": m.get("music_id", ""),
                    "source": "douyin",
                    "heat_index": i + 1,
                    "play_url": m.get("play_url", {}).get("url", ""),
                })
            logger.info(f"抖音音乐榜获取到 {len(results)} 首")
            return results
    except Exception as e:
        logger.warning(f"抖音音乐榜爬取失败: {e}")

    # 降级方案：返回空列表，后续用QQ音乐+网易云数据近似
    logger.info("抖音榜降级，使用QQ音乐+网易云数据作为替代")
    return []


def fetch_douyin_trending_songs(limit: int = 50) -> List[Dict]:
    """
    获取抖音近期热门BGM（通过视频标签关联）
    使用公开搜索接口
    """
    try:
        resp = requests.post(
            "https://www.douyin.com/aweme/v1/web/general/search/single/",
            data={
                "search_channel": "aweme_video_web",
                "keyword": "热门BGM",
                "search_source": "normal_search",
                "query_correct_type": 1,
                "is_filter_search": 0,
                "offset": 0,
                "count": limit,
            },
            headers={
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            videos = data.get("data", []) or []
            # 提取视频关联BGM
            bgm_map = {}
            for v in videos:
                m = v.get("music", {})
                if m:
                    mid = m.get("id")
                    if mid and mid not in bgm_map:
                        bgm_map[mid] = {
                            "song_name": m.get("title", "").strip() or m.get("author", ""),
                            "artist": m.get("author", ""),
                            "music_id": str(mid),
                            "source": "douyin_trending",
                            "heat_index": 0,
                        }
            results = list(bgm_map.values())[:limit]
            logger.info(f"抖音Trending BGM获取到 {len(results)} 首")
            return results
    except Exception as e:
        logger.warning(f"抖音Trending BGM爬取失败: {e}")
    return []


if __name__ == "__main__":
    print("=== 抖音音乐榜 ===")
    for s in fetch_douyin_music_chart(10):
        print(f"  {s['song_name']} - {s['artist']}")
