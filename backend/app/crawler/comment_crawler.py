"""
评论区数据爬虫
注意：抖音评论区需要登录态才能访问，此处使用公开数据近似方案
"""
import requests
import logging
import re
import time
import os
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger("tiktokrx.crawler.comment")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Referer": "https://www.douyin.com/",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def detect_comment_type(comment: str) -> str:
    """检测评论类型"""
    comment_lower = comment.lower().strip()

    # 求同款/求链接
    if re.search(r'(求|想要|想知|哪.*买|链接|同款|色号|牌子|型号)', comment_lower):
        return "seeking_type"  # 求同款型

    # 质疑型
    if re.search(r'(假的|不靠谱|真的假|感觉|不会|有用吗|能行吗|质疑)', comment_lower):
        return "questioning_type"  # 质疑型

    # 经验型
    if re.search(r'(我之前|我也|其实|但是|不过|经验|以前|已经|用了|试过)', comment_lower):
        return "experience_type"  # 经验型

    # 凑热闹型（短评论，感叹词为主）
    if len(comment) <= 10 and re.search(r'([哈嘻哇哦呃啊呀啦滴呐]|了了|哒哒|嘿嘿|棒|赞|绝)', comment_lower):
        return "crowding_type"  # 凑热闹型

    # 种草型
    if re.search(r'(收藏|已入手|买了|真的|好用|推荐|种草|太好|绝了)', comment_lower):
        return "grass_type"  # 种草型

    # 求助型
    if re.search(r'(怎么|如何|请问|教教|教我|求助|帮忙|不会|不懂)', comment_lower):
        return "help_type"  # 求助型

    return "general_type"  # 一般评论


def analyze_sentiment(comment: str) -> str:
    """简单情感分析"""
    positive_words = ["赞", "好", "棒", "牛", "绝", "喜欢", "爱", "厉害", "支持", "太棒", "完美", "可爱", "甜", "美"]
    negative_words = ["差", "烂", "骗", "假", "坑", "垃圾", "失望", "后悔", "难吃", "难看", "无聊", "无语"]

    pos_count = sum(1 for w in positive_words if w in comment)
    neg_count = sum(1 for w in negative_words if w in comment)

    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"


def fetch_douyin_comments_by_aweme(aweme_id: str, limit: int = 20) -> List[Dict]:
    """
    根据视频ID获取评论区
    注意：需要有效的aweme_id，可从视频分享链接提取
    """
    try:
        resp = requests.get(
            f"https://www.douyin.com/aweme/v1/web/comment/list/",
            params={
                "aweme_id": aweme_id,
                "count": limit,
                "offset": 0,
                "device_platform": "android",
                "aid": "6383",
            },
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            comments = data.get("comments", []) or []
            results = []
            for c in comments[:limit]:
                text = c.get("text", "").strip()
                if not text:
                    continue
                results.append({
                    "text": text,
                    "like_count": c.get("digg_count", 0),
                    "comment_type": detect_comment_type(text),
                    "sentiment": analyze_sentiment(text),
                    "user_nickname": c.get("user", {}).get("nickname", ""),
                    "user_region": c.get("user", {}).get("region", ""),
                    "aweme_id": aweme_id,
                    "source": "douyin_comment",
                    "crawled_at": datetime.now().isoformat(),
                })
            logger.info(f"获取评论 {len(results)} 条")
            return results
    except Exception as e:
        logger.warning(f"评论区获取失败: {e}")
    return []


def fetch_simulated_comments_from_db(category: str, limit: int = 20, db_path: str = "data/tiktok_baseline.db") -> List[Dict]:
    """
    从数据库已有评论数据中按品类检索
    降级方案：当无法爬取时使用
    """
    import sqlite3
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("""
            SELECT text, comment_type, sentiment, source
            FROM comment_database
            WHERE category = ?
            ORDER BY RANDOM()
            LIMIT ?
        """, (category, limit)).fetchall()
        conn.close()
        return [
            {"text": r[0], "comment_type": r[1], "sentiment": r[2], "source": r[3]}
            for r in rows
        ]
    except Exception:
        conn.close()
        return []


def save_comments_to_db(records: List[Dict], category: str = None, db_path: str = "data/tiktok_baseline.db") -> int:
    """保存评论数据到数据库，并触发 xlsx 同步"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comment_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            like_count INTEGER DEFAULT 0,
            comment_type TEXT DEFAULT 'general_type',
            sentiment TEXT DEFAULT 'neutral',
            user_nickname TEXT DEFAULT '',
            user_region TEXT DEFAULT '',
            aweme_id TEXT DEFAULT '',
            category TEXT,
            source TEXT DEFAULT '',
            crawled_at TEXT,
            UNIQUE(text, source, aweme_id)
        )
    """)
    count = 0
    for r in records:
        if not r.get("text"):
            continue
        try:
            conn.execute("""
                INSERT OR IGNORE INTO comment_database
                (text, like_count, comment_type, sentiment, user_nickname,
                 user_region, aweme_id, category, source, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["text"], r.get("like_count", 0), r.get("comment_type", "general_type"),
                r.get("sentiment", "neutral"), r.get("user_nickname", ""),
                r.get("user_region", ""), r.get("aweme_id", ""),
                category or r.get("category", ""),
                r.get("source", ""), r.get("crawled_at", "")
            ))
            count += 1
        except Exception as e:
            logger.warning(f"评论入库失败: {e}")
    conn.commit()
    conn.close()

    # 触发 xlsx 同步（每 100 条或每 5 分钟）
    if count > 0:
        try:
            from .xlsx_sync import get_xlsx_sync
            db_dir = os.path.dirname(os.path.abspath(db_path))
            xlsx_dir = os.path.join(db_dir, "抖音原始数据")
            sync = get_xlsx_sync(db_path, xlsx_dir)
            sync.on_records_saved(count)
        except Exception as e:
            logger.warning(f"xlsx 同步失败: {e}")

    return count


def seed_sample_comments(db_path: str = "data/tiktok_baseline.db") -> int:
    """
    预置各品类高质量评论样例（基于PRD中的真实评论风格）
    当无法爬取时使用此数据
    """
    SAMPLE_COMMENTS = {
        "food": [
            ("啊啊啊看着好香！明天就做", "grass_type", "positive", "douyin_sample"),
            ("这成本得多少钱啊？", "questioning_type", "neutral", "douyin_sample"),
            ("已收藏，等我下班试试", "grass_type", "positive", "douyin_sample"),
            ("为什么我做的和你的不一样😭", "questioning_type", "negative", "douyin_sample"),
            ("老婆饼里没有老婆，这个里面也没有", "crowding_type", "neutral", "douyin_sample"),
            ("收藏了！周末试试", "grass_type", "positive", "douyin_sample"),
            ("这个做法真的绝了，全家抢着吃", "grass_type", "positive", "douyin_sample"),
            ("跟着做了一次，失败了怎么办", "help_type", "neutral", "douyin_sample"),
            ("感觉材料不好买啊", "questioning_type", "negative", "douyin_sample"),
            ("哈哈哈笑死了", "crowding_type", "positive", "douyin_sample"),
        ],
        "fashion": [
            ("链接！必须要链接！", "seeking_type", "neutral", "douyin_sample"),
            ("158穿出170的效果，服了", "experience_type", "positive", "douyin_sample"),
            ("有没有男款啊，给我老公也来一套", "seeking_type", "neutral", "douyin_sample"),
            ("省吃俭用买基金，终于等到回调", "crowding_type", "neutral", "douyin_sample"),
            ("感觉普通身材穿不出来效果", "questioning_type", "negative", "douyin_sample"),
            ("真的绝了，买了！", "grass_type", "positive", "douyin_sample"),
            ("已入手，等发货", "grass_type", "positive", "douyin_sample"),
            ("这个颜色适合黄皮吗", "help_type", "neutral", "douyin_sample"),
            ("太好看了吧！", "crowding_type", "positive", "douyin_sample"),
            ("真的假的？感觉不靠谱", "questioning_type", "negative", "douyin_sample"),
        ],
        "tech": [
            ("等等党永远在胜利", "experience_type", "positive", "douyin_sample"),
            ("说的挺好，买了后悔两年", "questioning_type", "negative", "douyin_sample"),
            ("终于有人说实话了", "grass_type", "positive", "douyin_sample"),
            ("测评视频看多了，都不知道怎么选了", "questioning_type", "neutral", "douyin_sample"),
            ("已经下单了，坐等打脸", "crowding_type", "neutral", "douyin_sample"),
            ("质量怎么样，用过的来说说", "help_type", "neutral", "douyin_sample"),
            ("性价比很高，推荐", "grass_type", "positive", "douyin_sample"),
            ("这个价格还要啥自行车", "experience_type", "positive", "douyin_sample"),
            ("等降价了再买", "experience_type", "neutral", "douyin_sample"),
            ("买了，用了三个月说说感受", "experience_type", "positive", "douyin_sample"),
        ],
        "travel": [
            ("收藏了！五一刚好去", "grass_type", "positive", "douyin_sample"),
            ("滤镜很重吧，实际很坑", "questioning_type", "negative", "douyin_sample"),
            ("去年去过，确实很美", "experience_type", "positive", "douyin_sample"),
            ("求详细攻略！交通住宿", "seeking_type", "neutral", "douyin_sample"),
            ("假装在国外系列", "crowding_type", "positive", "douyin_sample"),
            ("周末去人会不会很多", "help_type", "neutral", "douyin_sample"),
            ("好美啊，必须去！", "grass_type", "positive", "douyin_sample"),
            ("这个季节去合适吗", "help_type", "neutral", "douyin_sample"),
            ("已收藏，准备去", "grass_type", "positive", "douyin_sample"),
            ("照片比实物好看", "questioning_type", "negative", "douyin_sample"),
        ],
        "lifestyle": [
            ("看完我默默放下了手机", "experience_type", "positive", "douyin_sample"),
            ("太真实了，说的就是我", "experience_type", "positive", "douyin_sample"),
            ("同龄人，差距怎么这么大", "questioning_type", "negative", "douyin_sample"),
            ("拒绝焦虑，从刷到这条视频开始", "grass_type", "positive", "douyin_sample"),
            ("博主活得通透，支持", "grass_type", "positive", "douyin_sample"),
            ("哈哈哈太准了", "crowding_type", "positive", "douyin_sample"),
            ("我就是这样的人", "experience_type", "neutral", "douyin_sample"),
            ("自律真的好难啊", "questioning_type", "negative", "douyin_sample"),
            ("怎么做到的，教教我", "help_type", "neutral", "douyin_sample"),
            ("收藏了开始自律", "grass_type", "positive", "douyin_sample"),
        ],
    }

    total = 0
    for cat, comments in SAMPLE_COMMENTS.items():
        count = save_comments_to_db([
            {"text": t, "comment_type": ct, "sentiment": s, "source": src, "category": cat}
            for t, ct, s, src in comments
        ], cat, db_path)
        total += count
    logger.info(f"预置评论样例入库 {total} 条")
    return total


def init_comment_table(db_path: str = "data/tiktok_baseline.db") -> None:
    """确保评论表存在"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comment_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            like_count INTEGER DEFAULT 0,
            comment_type TEXT DEFAULT 'general_type',
            sentiment TEXT DEFAULT 'neutral',
            user_nickname TEXT DEFAULT '',
            user_region TEXT DEFAULT '',
            aweme_id TEXT DEFAULT '',
            category TEXT,
            source TEXT DEFAULT '',
            crawled_at TEXT,
            UNIQUE(text, source, aweme_id)
        )
    """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    init_comment_table()
    seed_sample_comments()
