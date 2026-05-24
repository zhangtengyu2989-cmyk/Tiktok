"""
社交媒体热搜爬虫 - 替代被block平台
包括：今日头条、微信搜一搜、百度贴吧等
"""
import requests
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger("tiktokrx.crawler.social")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def extract_hooks(title: str) -> Dict:
    """提取标题钩子特征"""
    hooks = {
        "has_number": bool(re.search(r'\d', title)),
        "has_exclaim": bool(re.search(r'[！？!]+', title)),
        "has_emoji": bool(re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF✨🔥💄🎉]', title)),
        "has_question": bool(re.search(r'[？？?]+', title)),
        "has_suspense": bool(re.search(r'(竟然|没想到|原来|真相|揭秘|背后|原因|终于|其实|但是|必看|绝了)', title)),
        "emotion_words": len(re.findall(r'(绝了|太牛了|哭了|救命|宝藏|神仙|炸裂|封神|无敌|逆天|笑死|哭死)', title)),
        "length": len(title),
    }
    return hooks


def infer_category(title: str) -> Optional[str]:
    """推断标题所属品类"""
    categories = {
        "food": ["美食", "吃播", "探店", "烹饪", "菜谱", "厨房", "减肥", "外卖", "餐厅", "烘焙", "小吃"],
        "fashion": ["穿搭", "美妆", "护肤", "发型", "衣服", "裙子", "裤子", "搭配", "化妆", "香水"],
        "tech": ["手机", "电脑", "数码", "测评", "科技", "软件", "教程", "iPhone", "安卓", "华为"],
        "travel": ["旅行", "旅游", "攻略", "打卡", "景点", "酒店", "机票", "出国", "日本", "泰国"],
        "lifestyle": ["生活", "日常", "vlog", "情感", "解压", "收纳", "清洁", "自律", "租房"],
    }
    title_lower = title.lower()
    scores = {cat: sum(1 for kw in kws if kw.lower() in title_lower) for cat, kws in categories.items()}
    max_score = max(scores.values()) if scores else 0
    return max(scores, key=scores.get) if max_score > 0 else None


def fetch_toutiao_hot(limit: int = 50) -> List[Dict]:
    """获取今日头条热搜（替代小红书/知乎）"""
    try:
        resp = requests.get(
            "https://www.toutiao.com/c/toutiao/hot-list/",
            headers={
                **HEADERS,
                "Referer": "https://www.toutiao.com/",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("data", [])[:limit]:
                title = (item.get("Title") or item.get("title") or "").strip()
                if not title:
                    continue
                hook_info = extract_hooks(title)
                results.append({
                    "title": title,
                    "hot_value": item.get("hot_index", 0) or item.get("hotScore", 0),
                    "category": infer_category(title),
                    "label": item.get("cluster_tag", ""),
                    "source": "toutiao_hot",
                    "hook_info": hook_info,
                    "crawled_at": datetime.now().isoformat(),
                })
            logger.info(f"今日头条热搜获取到 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"今日头条热搜爬取失败: {e}")
    return []


def fetch_toutiao_search(keyword: str, limit: int = 30) -> List[Dict]:
    """搜索今日头条相关内容"""
    try:
        resp = requests.get(
            "https://www.toutiao.com/api/search/content/",
            params={"keyword": keyword, "pd": "article", "count": limit},
            headers={
                **HEADERS,
                "Referer": "https://so.toutiao.com/",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("data", [])[:limit]:
                title = (item.get("title") or "").strip()
                if not title:
                    continue
                hook_info = extract_hooks(title)
                results.append({
                    "title": title,
                    "hot_value": item.get("user_info", {}).get("Fans", 0),
                    "category": infer_category(title),
                    "source": "toutiao_search",
                    "hook_info": hook_info,
                    "crawled_at": datetime.now().isoformat(),
                })
            logger.info(f"今日头条搜索[{keyword}]获取到 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"今日头条搜索失败: {e}")
    return []


def fetch_wechat_search(limit: int = 30) -> List[Dict]:
    """获取微信搜一搜热点（替代小红书）"""
    try:
        resp = requests.get(
            "https://mp.weixin.qq.com/cgi-bin/searchbiz",
            params={"action": "search_biz", "query": "热点", "limit": limit},
            headers={
                **HEADERS,
                "Referer": "https://weixin.qq.com/",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("list", [])[:limit]:
                title = (item.get("nickname") or "").strip()
                if not title:
                    continue
                hook_info = extract_hooks(title)
                results.append({
                    "title": f"公众号: {title}",
                    "hot_value": item.get("user_total", 0),
                    "category": infer_category(title),
                    "source": "wechat_search",
                    "hook_info": hook_info,
                    "crawled_at": datetime.now().isoformat(),
                })
            logger.info(f"微信搜一搜获取到 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"微信搜一搜获取失败: {e}")
    return []


def fetch_baidu_tieba_hot(limit: int = 50) -> List[Dict]:
    """获取百度贴吧热帖（替代知乎）"""
    try:
        resp = requests.get(
            "https://tieba.baidu.com/hottopic/browse/topicList",
            headers={
                **HEADERS,
                "Referer": "https://tieba.baidu.com/",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("data", {}).get("topic_list", [])[:limit]:
                title = (item.get("topic_name") or "").strip()
                if not title:
                    continue
                hook_info = extract_hooks(title)
                results.append({
                    "title": title,
                    "hot_value": item.get("discuss_num", 0),
                    "category": infer_category(title),
                    "label": item.get("topic_desc", ""),
                    "source": "baidu_tieba",
                    "hook_info": hook_info,
                    "crawled_at": datetime.now().isoformat(),
                })
            logger.info(f"百度贴吧热帖获取到 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"百度贴吧热帖爬取失败: {e}")
    return []


def fetch_baidu_hot(limit: int = 50) -> List[Dict]:
    """获取百度热搜榜"""
    try:
        resp = requests.get(
            "https://top.baidu.com/api.php",
            params={"type": "top", "话": "10"},
            headers={
                **HEADERS,
                "Referer": "https://top.baidu.com/",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("data", [])[:limit]:
                title = (item.get("query") or "").strip()
                if not title:
                    continue
                hook_info = extract_hooks(title)
                results.append({
                    "title": title,
                    "hot_value": item.get("hotScore", 0),
                    "category": infer_category(title),
                    "label": item.get("desc", ""),
                    "source": "baidu_hot",
                    "hook_info": hook_info,
                    "crawled_at": datetime.now().isoformat(),
                })
            logger.info(f"百度热搜获取到 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"百度热搜爬取失败: {e}")
    return []


def fetch_sina_hot(limit: int = 50) -> List[Dict]:
    """获取新浪微博移动端热搜（备用方案）"""
    try:
        resp = requests.get(
            "https://m.weibo.cn/api/container/getIndex",
            params={"type": "hot", "containerid": "102803"},
            headers={
                **HEADERS,
                "Referer": "https://m.weibo.cn/",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("data", {}).get("cards", [])[:limit]:
                title = (item.get("card_title") or "").strip()
                if not title:
                    continue
                hook_info = extract_hooks(title)
                results.append({
                    "title": title,
                    "hot_value": 0,
                    "category": infer_category(title),
                    "source": "sina_mobile",
                    "hook_info": hook_info,
                    "crawled_at": datetime.now().isoformat(),
                })
            logger.info(f"新浪微博移动端获取到 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"新浪微博移动端获取失败: {e}")
    return []


def save_to_db(records: List[Dict], db_path: str) -> int:
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
                int(h.get("has_number", False)), int(h.get("has_exclaim", False)),
                int(h.get("has_emoji", False)), int(h.get("has_question", False)),
                int(h.get("has_suspense", False)), h.get("emotion_words", 0),
                h.get("length", 0), r.get("crawled_at", "")
            ))
            count += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return count


def crawl_all_with_fallback(db_path: str = "data/tiktok_baseline.db") -> Dict[str, int]:
    """带降级策略的标题采集"""
    results = {}

    # 1. 抖音热搜（主数据源）
    try:
        from .title_crawler import fetch_douyin_hot_titles, save_titles_to_db
        douyin_titles = fetch_douyin_hot_titles(50)
        results["douyin_hot"] = save_titles_to_db(douyin_titles, db_path)
    except Exception as e:
        logger.warning(f"抖音热搜采集失败: {e}")
        results["douyin_hot"] = 0

    # 2. 今日头条热搜（替代方案）
    try:
        results["toutiao_hot"] = save_to_db(fetch_toutiao_hot(50), db_path)
    except Exception as e:
        logger.warning(f"今日头条采集失败: {e}")
        results["toutiao_hot"] = 0

    # 3. 百度热搜
    try:
        results["baidu_hot"] = save_to_db(fetch_baidu_hot(50), db_path)
    except Exception as e:
        logger.warning(f"百度热搜采集失败: {e}")
        results["baidu_hot"] = 0

    # 4. 百度贴吧（知乎替代）
    try:
        results["baidu_tieba"] = save_to_db(fetch_baidu_tieba_hot(50), db_path)
    except Exception as e:
        logger.warning(f"百度贴吧采集失败: {e}")
        results["baidu_tieba"] = 0

    # 5. B站热门（有限流保护，间隔5秒）
    try:
        import time
        time.sleep(5)
        from .news_title_spiders import fetch_bilibili_hot
        results["bilibili_hot"] = save_to_db(fetch_bilibili_hot(30), db_path)
    except Exception as e:
        logger.warning(f"B站热门采集失败: {e}")
        results["bilibili_hot"] = 0

    # 6. 新浪微博移动端（备用）
    try:
        results["sina_mobile"] = save_to_db(fetch_sina_hot(50), db_path)
    except Exception as e:
        logger.warning(f"新浪微博采集失败: {e}")
        results["sina_mobile"] = 0

    total = sum(results.values())
    logger.info(f"标题采集完成，共入库 {total} 条")
    return results


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    print("=== 今日头条热搜 ===")
    for t in fetch_toutiao_hot(5):
        print(f"  {t['title']}")

    print("\n=== 百度热搜 ===")
    for t in fetch_baidu_hot(5):
        print(f"  {t['title']}")

    print("\n=== 百度贴吧 ===")
    for t in fetch_baidu_tieba_hot(5):
        print(f"  {t['title']}")
