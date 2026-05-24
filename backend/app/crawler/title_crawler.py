"""
标题数据爬虫
采集抖音/热搜榜单的热门标题数据
"""
import requests
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger("tiktokrx.crawler.title")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Referer": "https://www.douyin.com/",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

CATEGORY_KEYWORDS = {
    "food": ["美食", "吃播", "探店", "烹饪", "菜谱", "厨房", "减肥", "外卖"],
    "fashion": ["穿搭", "美妆", "护肤", "发型", "衣服", "裙子", "裤子", "搭配"],
    "tech": ["手机", "电脑", "数码", "测评", "科技", "软件", "教程", "iPhone", "安卓"],
    "travel": ["旅行", "旅游", "攻略", "打卡", "景点", "酒店", "机票", "出国"],
    "lifestyle": ["生活", "日常", "vlog", "情感", "解压", "收纳", "清洁", "自律"],
}


def extract_hooks(title: str) -> Dict[str, int]:
    """提取标题中的钩子类型"""
    hooks = {
        "has_number": 0,
        "has_exclaim": 0,
        "has_emoji": 0,
        "has_question": 0,
        "has_suspense": 0,
        "has_digit": 0,
        "emotion_words": 0,
        "length": len(title),
    }

    hooks["has_digit"] = 1 if re.search(r'\d', title) else 0
    hooks["has_number"] = 1 if re.search(r'\d', title) else 0
    hooks["has_exclaim"] = 1 if re.search(r'[！？!]', title) else 0
    hooks["has_question"] = 1 if re.search(r'[？？?]', title) else 0
    hooks["has_emoji"] = 1 if re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF✨🔥]', title) else 0

    # 悬念词
    suspense_words = ["竟然", "没想到", "原来", "真相", "揭秘", "背后", "原因", "终于", "其实", "但是"]
    hooks["has_suspense"] = sum(1 for w in suspense_words if w in title)

    # 情绪词
    emotion_words = ["绝了", "太牛了", "哭了", "救命", "宝藏", "神仙", "炸裂", "封神", "无敌", "逆天"]
    hooks["emotion_words"] = sum(1 for w in emotion_words if w in title)

    return hooks


def infer_category(title: str) -> Optional[str]:
    """根据标题关键词推断品类"""
    title_lower = title.lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw.lower() in title_lower)
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return None


def fetch_douyin_hot_titles(limit: int = 50) -> List[Dict]:
    """
    获取抖音热搜标题列表
    通过抖音热点榜公开接口
    """
    try:
        resp = requests.get(
            "https://www.douyin.com/aweme/v1/web/hot/search/list/",
            params={"device_platform": "android", "aid": "6383", "version_name": "23.5.0"},
            headers={
                **HEADERS,
                "User-Agent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            words = data.get("data", {}).get("word_list", []) or []
            results = []
            for item in words[:limit]:
                word = item.get("word", "").strip()
                if not word:
                    continue
                hook_info = extract_hooks(word)
                inferred = infer_category(word)
                results.append({
                    "title": word,
                    "hot_value": item.get("hot_value", 0),
                    "category": inferred,
                    "word_cover": item.get("word_cover", ""),
                    "hook_info": hook_info,
                    "source": "douyin_hot_search",
                    "crawled_at": datetime.now().isoformat(),
                })
            logger.info(f"抖音热搜获取到 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"抖音热搜爬取失败: {e}")
    return []


def fetch_douyin_topic_titles(category: str = None, limit: int = 30) -> List[Dict]:
    """
    获取抖音话题下的热门视频标题
    """
    try:
        # 抖音挑战榜/话题榜
        resp = requests.get(
            "https://www.douyin.com/aweme/v1/web/challenge/search/",
            params={
                "keyword": category or "热门",
                "count": limit,
                "offset": 0,
                "aid": "6383",
            },
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            challenges = data.get("challenge_list", []) or []
            results = []
            for c in challenges[:limit]:
                cha_name = c.get("cha_name", "")
                desc = c.get("desc", "")
                if cha_name or desc:
                    results.append({
                        "title": cha_name or desc,
                        "description": desc,
                        "user_count": c.get("user_count", 0),
                        "view_count": c.get("view_count", 0),
                        "category": category,
                        "source": "douyin_topic",
                        "crawled_at": datetime.now().isoformat(),
                    })
            logger.info(f"抖音话题获取到 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"抖音话题爬取失败: {e}")
    return []


def fetch_weibo_hot(limit: int = 50) -> List[Dict]:
    """
    获取微博热搜标题（娱乐/社会/综合）
    微博热搜部分公开可爬
    """
    try:
        resp = requests.get(
            "https://weibo.com/ajax/side/hotSearch",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://weibo.com/",
                "Accept": "application/json",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            band_list = data.get("data", {}).get("band_list", []) or []
            results = []
            for item in band_list[:limit]:
                word = item.get("word", "").strip()
                if not word:
                    continue
                hook_info = extract_hooks(word)
                results.append({
                    "title": word,
                    "hot_value": item.get("raw_hot", 0),
                    "category": None,
                    "label": item.get("label", ""),
                    "flag": item.get("flag", 0),
                    "hook_info": hook_info,
                    "source": "weibo_hot",
                    "crawled_at": datetime.now().isoformat(),
                })
            logger.info(f"微博热搜获取到 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"微博热搜爬取失败: {e}")
    return []


def save_titles_to_db(records: List[Dict], db_path: str = "data/tiktok_baseline.db") -> int:
    """保存标题数据到数据库"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS title_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            hot_value INTEGER DEFAULT 0,
            category TEXT,
            label TEXT,
            source TEXT DEFAULT '',
            has_number INTEGER DEFAULT 0,
            has_exclaim INTEGER DEFAULT 0,
            has_emoji INTEGER DEFAULT 0,
            has_question INTEGER DEFAULT 0,
            has_suspense INTEGER DEFAULT 0,
            emotion_words INTEGER DEFAULT 0,
            title_length INTEGER DEFAULT 0,
            crawled_at TEXT,
            UNIQUE(title, source)
        )
    """)
    count = 0
    for r in records:
        if not r.get("title"):
            continue
        h = r.get("hook_info", {})
        try:
            conn.execute("""
                INSERT INTO title_database
                (title, hot_value, category, label, source,
                 has_number, has_exclaim, has_emoji, has_question,
                 has_suspense, emotion_words, title_length, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(title, source) DO UPDATE SET hot_value=excluded.hot_value
            """, (
                r["title"], r.get("hot_value", 0), r.get("category"),
                r.get("label", ""), r.get("source", ""),
                h.get("has_number", 0), h.get("has_exclaim", 0),
                h.get("has_emoji", 0), h.get("has_question", 0),
                h.get("has_suspense", 0), h.get("emotion_words", 0),
                h.get("length", 0), r.get("crawled_at", "")
            ))
            count += 1
        except Exception as e:
            logger.warning(f"标题入库失败 {r.get('title')[:20]}: {e}")
    conn.commit()
    conn.close()
    return count


def crawl_all_titles(db_path: str = "data/tiktok_baseline.db") -> Dict[str, int]:
    """从所有平台采集标题数据（带降级策略）"""
    results = {}

    # 1. 抖音热搜（主数据源）
    logger.info("开始采集 抖音热搜...")
    try:
        douyin_titles = fetch_douyin_hot_titles(50)
        results["douyin_hot"] = save_titles_to_db(douyin_titles, db_path)
    except Exception as e:
        logger.warning(f"抖音热搜采集失败: {e}")
        results["douyin_hot"] = 0

    # 2. B站热门（有限流保护，延迟采集）
    logger.info("开始采集 B站热门...")
    try:
        import time
        time.sleep(5)  # B站限流保护
        from .news_title_spiders import fetch_bilibili_hot
        bilibili_titles = fetch_bilibili_hot(50)
        results["bilibili_hot"] = save_titles_to_db(bilibili_titles, db_path)
    except Exception as e:
        logger.warning(f"B站热门采集失败: {e}")
        results["bilibili_hot"] = 0

    # 3. 今日头条热搜（替代方案）
    logger.info("开始采集 今日头条热搜...")
    try:
        from .social_spiders import fetch_toutiao_hot
        toutiao_titles = fetch_toutiao_hot(50)
        results["toutiao_hot"] = save_titles_to_db(toutiao_titles, db_path)
    except Exception as e:
        logger.warning(f"今日头条采集失败: {e}")
        results["toutiao_hot"] = 0

    # 4. 百度热搜
    logger.info("开始采集 百度热搜...")
    try:
        from .news_title_spiders import fetch_baidu_hot
        baidu_titles = fetch_baidu_hot(50)
        results["baidu_hot"] = save_titles_to_db(baidu_titles, db_path)
    except Exception as e:
        logger.warning(f"百度热搜采集失败: {e}")
        results["baidu_hot"] = 0

    total = sum(results.values())
    logger.info(f"标题采集完成，共入库 {total} 条")
    return results


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = crawl_all_titles()
    print(f"采集结果: {result}")
