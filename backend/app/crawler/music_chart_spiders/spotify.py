"""
Spotify 热门歌曲爬虫
通过解析Spotify公开页面获取热门歌曲
"""
import requests
import logging
from typing import List, Dict

logger = logging.getLogger("tiktokrx.crawler.spotify")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://open.spotify.com/",
}


def fetch_spotify_viral_global(limit: int = 100) -> List[Dict]:
    """获取Spotify全球Viral榜单"""
    try:
        # Spotify Viral 50 Global
        # 使用Spotify的公开API
        resp = requests.get(
            "https://open.spotify.com/embedded-player/servlet/discovery/editorial/deeplink/target?uri=spotify:playlist:37i9dQZEVXblPG1W0mC7QK",
            headers=HEADERS,
            timeout=15,
        )

        # 备用方案：使用Spotify Charts
        if resp.status_code != 200:
            return fetch_spotify_charts_global(limit)

        return parse_spotify_page(resp.text, "spotify_viral_global")
    except Exception as e:
        logger.warning(f"Spotify Viral Global爬取失败: {e}")
        return fetch_spotify_charts_global(limit)


def fetch_spotify_charts_global(limit: int = 50) -> List[Dict]:
    """从Spotify Charts获取全球榜单"""
    try:
        resp = requests.get(
            "https://charts.spotify.com/charts/overview/global",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()

        import re
        content = resp.text

        # 解析页面中的曲目信息
        # Spotify Charts页面包含JSON数据
        pattern = r'"trackName":"([^"]+)".*?"artistName":"([^"]+)"'
        matches = re.findall(pattern, content)

        results = []
        for i, (name, artist) in enumerate(matches[:limit]):
            results.append({
                "song_name": name.strip(),
                "artist": artist.strip(),
                "album": "",
                "duration": 0,
                "song_id": "",
                "source": "spotify_charts",
                "heat_index": i + 1,
            })

        logger.info(f"Spotify Charts Global获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"Spotify Charts Global爬取失败: {e}")
        return []


def fetch_spotify_regional(region: str = "cn", limit: int = 50) -> List[Dict]:
    """获取Spotify地区榜单"""
    try:
        # Spotify Regional Charts
        region_codes = {
            "cn": "cn", "us": "us", "global": "global",
            "jp": "jp", "kr": "kr", "hk": "hk", "tw": "tw"
        }
        code = region_codes.get(region, "global")

        resp = requests.get(
            f"https://charts.spotify.com/charts/overview/{code}",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()

        import re
        content = resp.text
        pattern = r'"trackName":"([^"]+)".*?"artistName":"([^"]+)"'
        matches = re.findall(pattern, content)

        results = []
        for i, (name, artist) in enumerate(matches[:limit]):
            results.append({
                "song_name": name.strip(),
                "artist": artist.strip(),
                "album": "",
                "duration": 0,
                "song_id": "",
                "source": f"spotify_{code}",
                "heat_index": i + 1,
            })

        logger.info(f"Spotify {code}获取到 {len(results)} 首")
        return results
    except Exception as e:
        logger.warning(f"Spotify {region}爬取失败: {e}")
        return []


def parse_spotify_page(html: str, source: str) -> List[Dict]:
    """解析Spotify页面HTML"""
    import re
    results = []

    # 尝试多种模式匹配
    patterns = [
        r'"name":"([^"]+)","artist":"([^"]+)"',
        r'"trackName":"([^"]+)".*?"artistName":"([^"]+)"',
        r'data-testid="track-info".*?>([^<]+)<.*?data-testid="artist-info".*?>([^<]+)<',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, html)
        if matches:
            for i, match in enumerate(matches[:100]):
                if isinstance(match, tuple) and len(match) >= 2:
                    results.append({
                        "song_name": match[0].strip(),
                        "artist": match[1].strip(),
                        "album": "",
                        "duration": 0,
                        "song_id": "",
                        "source": source,
                        "heat_index": i + 1,
                    })
            break

    return results


if __name__ == "__main__":
    print("=== Spotify Viral Global ===")
    for s in fetch_spotify_viral_global(10):
        print(f"  {s['song_name']} - {s['artist']}")
