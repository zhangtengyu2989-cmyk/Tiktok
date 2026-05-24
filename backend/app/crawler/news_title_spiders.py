"""
新闻/热搜标题爬虫
采集各平台热搜榜标题数据
"""
import requests
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger("tiktokrx.crawler.news_titles")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def extract_hooks(title: str) -> Dict[str, int]:
    """提取标题中的钩子类型"""
    hooks = {
        "has_number": 0,
        "has_exclaim": 0,
        "has_emoji": 0,
        "has_question": 0,
        "has_suspense": 0,
        "emotion_words": 0,
        "title_length": len(title),
    }

    hooks["has_number"] = 1 if re.search(r'\d', title) else 0
    hooks["has_exclaim"] = 1 if re.search(r'[！？!]', title) else 0
    hooks["has_question"] = 1 if re.search(r'[？？?]', title) else 0
    hooks["has_emoji"] = 1 if re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF✨🔥]', title) else 0

    suspense_words = ["竟然", "没想到", "原来", "真相", "揭秘", "背后", "原因", "终于", "其实", "但是"]
    hooks["has_suspense"] = sum(1 for w in suspense_words if w in title)

    emotion_words = ["绝了", "太牛了", "哭了", "救命", "宝藏", "神仙", "炸裂", "封神", "无敌", "逆天"]
    hooks["emotion_words"] = sum(1 for w in emotion_words if w in title)

    return hooks


def infer_category(title: str) -> Optional[str]:
    """根据标题关键词推断品类"""
    title_lower = title.lower()
    categories = {
        "food": ["美食", "吃播", "探店", "烹饪", "菜谱", "厨房", "减肥", "外卖", "餐厅"],
        "fashion": ["穿搭", "美妆", "护肤", "发型", "衣服", "裙子", "裤子", "搭配", "化妆"],
        "tech": ["手机", "电脑", "数码", "测评", "科技", "软件", "教程", "iPhone", "安卓", "华为"],
        "travel": ["旅行", "旅游", "攻略", "打卡", "景点", "酒店", "机票", "出国", "日本", "泰国"],
        "lifestyle": ["生活", "日常", "vlog", "情感", "解压", "收纳", "清洁", "自律", "租房"],
        "entertainment": ["明星", "综艺", "电影", "电视剧", "演唱会", "八卦", "偶像"],
        "sports": ["足球", "篮球", "NBA", "世界杯", "奥运", "比赛", "健身", "跑步"],
        "education": ["高考", "考研", "留学", "英语", "学习", "考试", "学校", "大学生"],
    }

    scores = {}
    for cat, keywords in categories.items():
        scores[cat] = sum(1 for kw in keywords if kw.lower() in title_lower)

    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return None


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
                title = item.get("query", "").strip()
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


def fetch_zhihu_hot(limit: int = 50) -> List[Dict]:
    """获取知乎热榜"""
    try:
        resp = requests.get(
            "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
            headers={
                **HEADERS,
                "Referer": "https://www.zhihu.com/",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("data", [])[:limit]:
                title = item.get("target", {}).get("title", "").strip()
                if not title:
                    continue
                hook_info = extract_hooks(title)
                results.append({
                    "title": title,
                    "hot_value": item.get("metrics", {}).get("detail_views", 0),
                    "category": infer_category(title),
                    "label": item.get("target", {}).get("excerpt", ""),
                    "source": "zhihu_hot",
                    "hook_info": hook_info,
                    "crawled_at": datetime.now().isoformat(),
                })
            logger.info(f"知乎热榜获取到 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"知乎热榜爬取失败: {e}")
    return []


def fetch_toutiao_hot(limit: int = 50) -> List[Dict]:
    """获取今日头条热搜"""
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
                title = item.get("Title", "").strip() or item.get("title", "").strip()
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


def fetch_bilibili_hot(limit: int = 50) -> List[Dict]:
    """获取B站热门视频标题"""
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/ranking/v2",
            params={"rid": 0, "type": "all"},
            headers={
                **HEADERS,
                "Referer": "https://www.bilibili.com/",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("data", {}).get("list", [])[:limit]:
                title = item.get("title", "").strip()
                if not title:
                    continue
                hook_info = extract_hooks(title)
                results.append({
                    "title": title,
                    "hot_value": item.get("stat", {}).get("score", 0),
                    "category": item.get("tname", ""),
                    "label": item.get("rcmd_reason", ""),
                    "source": "bilibili_hot",
                    "hook_info": hook_info,
                    "crawled_at": datetime.now().isoformat(),
                })
            logger.info(f"B站热门获取到 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"B站热门爬取失败: {e}")
    return []


def fetch_baidu_tieba_hot(limit: int = 50) -> List[Dict]:
    """获取百度贴吧热帖"""
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
                title = item.get("topic_name", "").strip()
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


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    print("=== 百度热搜 ===")
    for t in fetch_baidu_hot(5):
        print(f"  {t['title']}")

    print("\n=== B站热门 ===")
    for t in fetch_bilibili_hot(5):
        print(f"  {t['title']}")
