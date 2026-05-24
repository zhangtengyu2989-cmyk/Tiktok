"""
抖音热搜爬虫
从抖音热搜榜获取热门标题数据
无需登录态，直接调用公开API
"""
import httpx
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger("tiktokrx.crawler.douyin_hot")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.douyin.com/user/self?from_tab_name=main",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "application/json, text/plain, */*",
    "Cookie": "sessionid=eb5d32daa151b90805a5727e84299928; ttwid=1%7C4X1b9cU9HSf7Mo_6na1bdZEycApjXhvzcDAX1dAR0UQ; msToken=9uQlqdP2CpBozMzwEq9yjD9svzH3TRaoOlb3TRRXgKQOnJnHLKMxs37VnNi_C4y6FHDr4utJRI5apdngomz1FyCWLaxMH3w_jil0uYTCeFgt7jKB6mtXSrpR16VxDMKbpHUxhVPaNNbfp0Y7GMZx82cuvg690ML_Q_aPH8yOSxw3%5E%26a_bogus=",
}

CATEGORY_KEYWORDS = {
    "food": ["美食", "吃播", "探店", "烹饪", "菜谱", "厨房", "减肥", "外卖", "烘焙", "小吃", "家常菜", "甜品", "饮品"],
    "fashion": ["穿搭", "美妆", "护肤", "发型", "衣服", "裙子", "裤子", "搭配", "化妆品", "口红", "香水", "医美"],
    "tech": ["手机", "电脑", "数码", "测评", "科技", "软件", "教程", "iPhone", "安卓", "显卡", "耳机", "相机", "无人机"],
    "travel": ["旅行", "旅游", "攻略", "打卡", "景点", "酒店", "机票", "出国", "签证", "自驾", "露营", "海岛"],
    "lifestyle": ["生活", "日常", "vlog", "情感", "解压", "收纳", "清洁", "自律", "理财", "职场", "人际", "心理", "健康"],
}

HOOK_PATTERNS = {
    "number": r'\d+[万千万百亿个点件杯斤克]+',
    "exclaim": r'[！？!！]+',
    "emoji": r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF✨🔥💄🎉🎵🏠👗📱🍜🏖️🎬]',
    "question": r'[？？?]+',
    "suspense": r'(竟然|没想到|原来|真相|揭秘|背后|原因|终于|其实|但是|必看|绝了)',
    "emotion": r'(绝了|太牛了|哭了|救命|宝藏|神仙|炸裂|封神|无敌|逆天|笑死|哭死)',
}


def extract_hook_info(title: str) -> Dict:
    """提取标题钩子特征"""
    hooks = {
        "has_number": bool(re.search(HOOK_PATTERNS["number"], title)),
        "has_exclaim": bool(re.search(HOOK_PATTERNS["exclaim"], title)),
        "has_emoji": bool(re.search(HOOK_PATTERNS["emoji"], title)),
        "has_question": bool(re.search(HOOK_PATTERNS["question"], title)),
        "has_suspense": bool(re.search(HOOK_PATTERNS["suspense"], title)),
        "emotion_words": len(re.findall(HOOK_PATTERNS["emotion"], title)),
        "length": len(title),
    }
    hooks["hook_score"] = (
        (1 if hooks["has_number"] else 0) * 2 +
        (1 if hooks["has_exclaim"] else 0) * 1 +
        (1 if hooks["has_emoji"] else 0) * 1 +
        (1 if hooks["has_question"] else 0) * 2 +
        (1 if hooks["has_suspense"] else 0) * 2 +
        min(hooks["emotion_words"], 3) * 1
    )
    return hooks


def infer_category(title: str) -> Optional[str]:
    """根据标题关键词推断品类"""
    title_lower = title.lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw.lower() in title_lower)
    max_score = max(scores.values()) if scores else 0
    if max_score > 0:
        return max(scores, key=scores.get)
    return "other"


def decode_text(text: str) -> str:
    """处理响应中的中文乱码"""
    try:
        return text.encode('latin1').decode('utf-8')
    except:
        return text


def fetch_douyin_hot_search(limit: int = 50) -> List[Dict]:
    """
    获取抖音热搜榜单
    公开API，无需登录态
    """
    try:
        resp = httpx.get(
            "https://www.douyin.com/aweme/v1/web/hot/search/list/",
            params={
                "device_platform": "android",
                "aid": "6383",
                "version_name": "23.5.0",
            },
            headers=HEADERS,
            timeout=10.0,
        )
        resp.raise_for_status()

        data = resp.json()
        word_list = data.get("data", {}).get("word_list", []) or []

        results = []
        for item in word_list[:limit]:
            # 处理标题，可能需要编码转换
            title = item.get("word", "")
            if not title:
                continue

            # 尝试修复编码
            try:
                if any(ord(c) > 127 for c in title):
                    title = decode_text(title)
            except:
                pass

            hook_info = extract_hook_info(title)
            category = infer_category(title)

            results.append({
                "title": title.strip(),
                "hot_value": item.get("hot_value", 0),
                "category": category,
                "label": item.get("label", ""),
                "sentence_id": item.get("sentence_id", ""),
                "word_type": item.get("word_type", 0),
                "hook_info": hook_info,
                "source": "douyin_hot_search",
                "crawled_at": datetime.now().isoformat(),
            })

        logger.info(f"抖音热搜获取到 {len(results)} 条")
        return results

    except Exception as e:
        logger.warning(f"抖音热搜获取失败: {e}")
        return []


def save_to_database(records: List[Dict], db_path: str = "data/tiktok_baseline.db") -> int:
    """保存热搜数据到数据库"""
    import sqlite3
    conn = sqlite3.connect(db_path)

    # 确保表存在
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
                INSERT OR IGNORE INTO title_database
                (title, hot_value, category, label, source,
                 has_number, has_exclaim, has_emoji, has_question,
                 has_suspense, emotion_words, title_length, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["title"], r.get("hot_value", 0), r.get("category"),
                r.get("label", ""), r.get("source", ""),
                int(h.get("has_number", False)),
                int(h.get("has_exclaim", False)),
                int(h.get("has_emoji", False)),
                int(h.get("has_question", False)),
                int(h.get("has_suspense", False)),
                h.get("emotion_words", 0),
                h.get("length", 0),
                r.get("crawled_at", "")
            ))
            count += 1
        except Exception as e:
            logger.warning(f"入库失败 {r.get('title')[:20]}: {e}")

    conn.commit()
    conn.close()
    logger.info(f"抖音热搜入库 {count} 条")
    return count


def crawl_and_save(db_path: str = "data/tiktok_baseline.db") -> int:
    """爬取抖音热搜并保存到数据库"""
    records = fetch_douyin_hot_search(50)
    if records:
        return save_to_database(records, db_path)
    return 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    print("=== 抖音热搜爬虫 ===")
    records = fetch_douyin_hot_search()
    print(f"获取到 {len(records)} 条热搜")

    for i, r in enumerate(records[:10]):
        print(f"  {i+1}. {r['title']} (热度: {r['hot_value']}, 品类: {r['category']})")

    if records:
        count = save_to_database(records)
        print(f"入库 {count} 条")
