"""
抖音创作者数据爬虫
采集同一作品的标题+封面+BGM+标签等多维数据
"""
import httpx
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger("tiktokrx.crawler.douyin_creator")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.douyin.com/",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "application/json, text/plain, */*",
    "Cookie": "sessionid=eb5d32daa151b90805a5727e84299928; ttwid=1%7C4X1b9cU9HSf7Mo_6na1bdZEycApjXhvzcDAX1dAR0UQ; msToken=9uQlqdP2CpBozMzwEq9yjD9svzH3TRaoOlb3TRRXgKQOnJnHLKMxs37VnNi_C4y6FHDr4utJRI5apdngomz1FyCWLaxMH3w_jil0uYTCeFgt7jKB6mtXSrpR16VxDMKbpHUxhVPaNNbfp0Y7GMZx82cuvg690ML_Q_aPH8yOSxw3%5E%26a_bogus=",
}


def get_user_info() -> Optional[Dict]:
    """获取当前登录用户信息"""
    try:
        resp = httpx.get(
            "https://www.douyin.com/aweme/v1/web/user/profile/self/",
            params={"device_platform": "webapp", "aid": "6383"},
            headers=HEADERS,
            timeout=15,
        )
        if resp.status_code == 200 and resp.text:
            data = resp.json()
            user = data.get("user", {})
            return {
                "sec_uid": user.get("sec_uid", ""),
                "nickname": user.get("nickname", ""),
                "uid": user.get("uid", ""),
            }
    except Exception as e:
        logger.warning(f"获取用户信息失败: {e}")
    return None


def fetch_user_videos(sec_uid: str, max_cursor: int = 0, count: int = 12) -> List[Dict]:
    """获取用户作品列表"""
    try:
        resp = httpx.get(
            "https://www.douyin.com/aweme/v1/web/aweme/post/",
            params={
                "device_platform": "webapp",
                "aid": "6383",
                "sec_user_id": sec_uid,
                "max_cursor": max_cursor,
                "count": count,
            },
            headers=HEADERS,
            timeout=15,
        )
        if resp.status_code == 200 and resp.text:
            data = resp.json()
            aweme_list = data.get("aweme_list") or []
            results = []
            for v in aweme_list:
                video = v.get("video", {})
                music = v.get("music", {})
                cover = video.get("cover", {})
                cover_urls = cover.get("url_list", [])

                results.append({
                    "aweme_id": v.get("aweme_id", ""),
                    "desc": v.get("desc", ""),
                    "create_time": v.get("create_time", 0),
                    "cover_url": cover_urls[0] if cover_urls else "",
                    "music_id": music.get("id", ""),
                    "music_title": music.get("title", ""),
                    "music_author": music.get("author", ""),
                    "music_duration": music.get("duration", 0),
                    "statistics": v.get("statistics", {}),
                    "author": v.get("author", {}),
                })
            return results
    except Exception as e:
        logger.warning(f"获取用户作品失败: {e}")
    return []


def infer_category_from_desc(desc: str) -> str:
    """从描述推断品类"""
    keywords = {
        "food": ["美食", "吃", "烹饪", "菜谱", "探店", "烘焙", "小吃"],
        "fashion": ["穿搭", "美妆", "护肤", "衣服", "裙子", "搭配"],
        "tech": ["手机", "电脑", "测评", "科技", "数码", "教程"],
        "travel": ["旅行", "旅游", "打卡", "景点", "酒店", "攻略"],
        "lifestyle": ["生活", "日常", "vlog", "情感", "收纳", "职场"],
    }
    desc_lower = desc.lower()
    scores = {cat: sum(1 for kw in kws if kw.lower() in desc_lower) for cat, kws in keywords.items()}
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "other"


def crawl_own_videos(db_path: str = "data/tiktok_baseline.db") -> Dict:
    """采集当前登录用户的作品数据"""
    import sqlite3
    conn = sqlite3.connect(db_path)

    # 确保表存在
    conn.execute("""
        CREATE TABLE IF NOT EXISTS video_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aweme_id TEXT UNIQUE,
            title TEXT,
            desc TEXT,
            cover_url TEXT,
            music_id TEXT,
            music_title TEXT,
            music_author TEXT,
            music_duration INTEGER,
            category TEXT,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            share_count INTEGER,
            create_time INTEGER,
            crawled_at TEXT
        )
    """)

    user_info = get_user_info()
    if not user_info:
        logger.warning("无法获取用户信息")
        conn.close()
        return {"total": 0, "saved": 0}

    logger.info(f"登录用户: {user_info.get('nickname')}")

    # 采集作品列表
    all_videos = []
    max_cursor = 0
    for page in range(5):  # 最多5页
        videos = fetch_user_videos(user_info["sec_uid"], max_cursor, 12)
        if not videos:
            break
        all_videos.extend(videos)
        logger.info(f"第{page+1}页: 获取{len(videos)}个作品")
        if len(videos) < 12:
            break
        max_cursor += 12
        time.sleep(0.5)

    # 保存到数据库
    saved = 0
    for v in all_videos:
        try:
            stats = v.get("statistics", {})
            conn.execute("""
                INSERT OR REPLACE INTO video_database
                (aweme_id, title, desc, cover_url, music_id, music_title, music_author,
                 music_duration, category, view_count, like_count, comment_count,
                 share_count, create_time, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                v["aweme_id"],
                v["desc"][:100] if v["desc"] else "",
                v["desc"],
                v["cover_url"],
                v["music_id"],
                v["music_title"],
                v["music_author"],
                v["music_duration"],
                infer_category_from_desc(v["desc"]),
                stats.get("play_count", 0),
                stats.get("digg_count", 0),
                stats.get("comment_count", 0),
                stats.get("share_count", 0),
                v["create_time"],
                datetime.now().isoformat(),
            ))
            saved += 1
        except Exception as e:
            logger.warning(f"入库失败 {v.get('aweme_id')}: {e}")

    conn.commit()
    conn.close()
    logger.info(f"作品采集完成: 共{len(all_videos)}个，入库{saved}个")
    return {"total": len(all_videos), "saved": saved}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    print("=== 抖音创作者数据采集 ===")
    result = crawl_own_videos()
    print(f"采集结果: {result}")
