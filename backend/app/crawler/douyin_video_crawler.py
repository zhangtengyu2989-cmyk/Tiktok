"""
抖音视频完整数据采集器
采集同一作品的：标题、封面、BGM、统计、评论
"""
import httpx
import re
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime
from playwright.sync_api import sync_playwright
from .cover_analyzer import full_cover_analysis

logger = logging.getLogger("tiktokrx.crawler.douyin_video")

# HTTP请求Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.douyin.com/",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "application/json, text/plain, */*",
    "Cookie": "sessionid=eb5d32daa151b90805a5727e84299928; ttwid=1%7C4X1b9cU9HSf7Mo_6na1bdZEycApjXhvzcDAX1dAR0UQ; msToken=9uQlqdP2CpBozMzwEq9yjD9svzH3TRaoOlb3TRRXgKQOnJnHLKMxs37VnNi_C4y6FHDr4utJRI5apdngomz1FyCWLaxMH3w_jil0uYTCeFgt7jKB6mtXSrpR16VxDMKbpHUxhVPaNNbfp0Y7GMZx82cuvg690ML_Q_aPH8yOSxw3",
}


def get_user_videos() -> List[Dict]:
    """获取当前登录用户的作品列表"""
    try:
        resp = httpx.get(
            "https://www.douyin.com/aweme/v1/web/user/profile/self/",
            params={"device_platform": "webapp", "aid": "6383"},
            headers=HEADERS,
            timeout=15,
        )
        if resp.status_code != 200 or not resp.text:
            return []

        user = resp.json().get("user", {})
        sec_uid = user.get("sec_uid", "")
        if not sec_uid:
            return []

        # 获取作品列表
        resp2 = httpx.get(
            "https://www.douyin.com/aweme/v1/web/aweme/post/",
            params={
                "device_platform": "webapp",
                "aid": "6383",
                "sec_user_id": sec_uid,
                "max_cursor": 0,
                "count": 18,
            },
            headers=HEADERS,
            timeout=15,
        )

        if resp2.status_code != 200:
            return []

        aweme_list = resp2.json().get("aweme_list") or []
        videos = []
        for v in aweme_list:
            video = v.get("video", {})
            music = v.get("music", {})
            cover = video.get("cover", {})
            cover_urls = cover.get("url_list", [])
            stats = v.get("statistics", {})

            videos.append({
                "aweme_id": v.get("aweme_id", ""),
                "desc": v.get("desc", ""),
                "cover_url": cover_urls[0] if cover_urls else "",
                "music_id": music.get("id", ""),
                "music_title": music.get("title", ""),
                "music_author": music.get("author", ""),
                "music_duration": music.get("duration", 0),
                "view_count": stats.get("play_count", 0),
                "like_count": stats.get("digg_count", 0),
                "comment_count": stats.get("comment_count", 0),
                "share_count": stats.get("share_count", 0),
                "create_time": v.get("create_time", 0),
            })
        return videos
    except Exception as e:
        logger.warning(f"获取用户作品失败: {e}")
        return []


def get_comments_by_playwright(aweme_id: str) -> List[str]:
    """使用Playwright获取视频评论"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            context.add_cookies([
                {"name": "sessionid", "value": "eb5d32daa151b90805a5727e84299928", "domain": ".douyin.com", "path": "/"},
                {"name": "ttwid", "value": "1%7C4X1b9cU9HSf7Mo_6na1bdZEycApjXhvzcDAX1dAR0UQ", "domain": ".douyin.com", "path": "/"},
                {"name": "msToken", "value": "9uQlqdP2CpBozMzwEq9yjD9svzH3TRaoOlb3TRRXgKQOnJnHLKMxs37VnNi_C4y6FHDr4utJRI5apdngomz1FyCWLaxMH3w_jil0uYTCeFgt7jKB6mtXSrpR16VxDMKbpHUxhVPaNNbfp0Y7GMZx82cuvg690ML_Q_aPH8yOSxw3", "domain": ".douyin.com", "path": "/"},
            ])

            page = context.new_page()
            page.goto(f"https://www.douyin.com/video/{aweme_id}", timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(8000)

            comments = []
            try:
                comment_list = page.query_selector("[data-e2e=\"comment-list\"]")
                if comment_list:
                    html = comment_list.inner_html()
                    pattern = r'>([^<]{10,200})<'
                    matches = re.findall(pattern, html)

                    for m in matches:
                        text = m.strip()
                        if len(text) > 5:
                            if not any(kw in text for kw in ["分享", "回复", "互相关", "作者赞过"]):
                                if not re.match(r"^\d+[万分]?$", text):
                                    if not re.search(r"\d+小时|\d+分钟|\d+天|\d+周|\d+月", text):
                                        comments.append(text[:200])
            except Exception as e:
                logger.warning(f"提取评论失败: {e}")

            # 去重
            seen = set()
            unique = []
            for c in comments:
                if c not in seen and len(c) > 5:
                    seen.add(c)
                    unique.append(c)

            browser.close()
            return unique[:50]
    except Exception as e:
        logger.warning(f"Playwright获取评论失败: {e}")
        return []


def infer_category(desc: str) -> str:
    """从描述推断品类"""
    keywords = {
        "food": ["美食", "吃", "烹饪", "菜谱", "探店", "烘焙", "小吃", "外卖"],
        "fashion": ["穿搭", "美妆", "护肤", "衣服", "裙子", "搭配", "化妆品"],
        "tech": ["手机", "电脑", "测评", "科技", "数码", "教程", "iPhone", "安卓"],
        "travel": ["旅行", "旅游", "打卡", "景点", "酒店", "攻略", "自驾"],
        "lifestyle": ["生活", "日常", "vlog", "情感", "收纳", "职场", "健康"],
    }
    desc_lower = desc.lower()
    scores = {cat: sum(1 for kw in kws if kw.lower() in desc_lower) for cat, kws in keywords.items()}
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "other"


def crawl_full_video_data(db_path: str = "data/tiktok_baseline.db") -> Dict:
    """采集完整视频数据并入库"""
    import sqlite3
    conn = sqlite3.connect(db_path)

    # 创建/确保表存在
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS comment_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aweme_id TEXT,
            video_title TEXT,
            comment_text TEXT,
            category TEXT,
            sentiment TEXT,
            source TEXT,
            crawled_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cover_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aweme_id TEXT,
            video_title TEXT,
            cover_url TEXT,
            color_tone TEXT,
            category TEXT,
            source TEXT,
            crawled_at TEXT
        )
    """)

    # 获取作品列表
    videos = get_user_videos()
    logger.info(f"获取到 {len(videos)} 个作品")

    total_saved = 0
    for v in videos:
        aweme_id = v["aweme_id"]

        # 入库视频基础数据
        try:
            conn.execute("""
                INSERT OR REPLACE INTO video_database
                (aweme_id, title, desc, cover_url, music_id, music_title, music_author,
                 music_duration, category, view_count, like_count, comment_count,
                 share_count, create_time, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                aweme_id, v["desc"][:100] if v["desc"] else "", v["desc"],
                v["cover_url"], v["music_id"], v["music_title"], v["music_author"],
                v["music_duration"], infer_category(v["desc"]), v["view_count"],
                v["like_count"], v["comment_count"], v["share_count"],
                v["create_time"], datetime.now().isoformat()
            ))
        except Exception as e:
            logger.warning(f"视频入库失败: {e}")

        # 入库封面（带完整视觉分析）
        if v["cover_url"]:
            try:
                analysis = full_cover_analysis(v["cover_url"])
                if analysis is None:
                    analysis = {"url": v["cover_url"], "color_tone": "", "avg_color": "",
                                "hue": 0, "saturation": 0, "lightness": 0,
                                "composition_type": "", "text_overlay_detected": 0,
                                "face_detected": 0, "analyzed_at": datetime.now().isoformat()}
                conn.execute("""
                    INSERT OR IGNORE INTO cover_database
                    (video_id, url, color_tone, avg_color, hue, saturation, lightness,
                     composition_type, text_overlay_detected, face_detected,
                     category, source, analyzed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    aweme_id, v["cover_url"],
                    analysis.get("color_tone", ""), analysis.get("avg_color", ""),
                    analysis.get("hue", 0), analysis.get("saturation", 0),
                    analysis.get("lightness", 0), analysis.get("composition_type", ""),
                    analysis.get("text_overlay_detected", 0), analysis.get("face_detected", 0),
                    infer_category(v["desc"]), "douyin_video", analysis.get("analyzed_at", "")
                ))
            except Exception as e:
                logger.warning(f"封面入库失败: {e}")

        # 获取并入库评论
        comments = []
        if v["comment_count"] > 0:
            comments = get_comments_by_playwright(aweme_id)
            for c in comments:
                try:
                    conn.execute("""
                        INSERT INTO comment_database
                        (aweme_id, text, category, sentiment, source, crawled_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        aweme_id,
                        c, infer_category(v["desc"]), "neutral", "douyin_video",
                        datetime.now().isoformat()
                    ))
                    total_saved += 1
                except:
                    pass

        conn.commit()
        logger.info(f"视频 {aweme_id[:15]}... 评论{len(comments)}条")
        time.sleep(1)  # 避免请求过快

    conn.close()
    return {"videos": len(videos), "comments": total_saved}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    print("=== 抖音完整视频数据采集 ===")
    result = crawl_full_video_data()
    print(f"采集结果: {result}")
