"""
Comment Persona Engine — 评论画像引擎
基于 6782 条真实评论数据，构建用户画像和评论生成能力
"""
from __future__ import annotations

import random
import re
import sqlite3
from typing import Optional

DB_PATH = "data/tiktok_baseline.db"

# ═══════════════════════════════════════════════════════════════
# 6种用户画像定义
# ═══════════════════════════════════════════════════════════════

COMMENT_PERSONAS = {
    "grass_type": {
        "name": "种草型",
        "description": "被内容打动，想要购买或尝试",
        "keywords": ["买了", "下单", "种草", "收藏", "必须买", "已购", "跟买", "推荐", "好物", "入手"],
        "sentiment": "positive",
        "emoji_hint": "😍✨",
        "example_templates": [
            "已入手！等快递中",
            "这也太香了吧，立刻下单",
            "收藏了，等搞活动就买",
            "跟老婆一起看的，已经下单了",
        ],
    },
    "experience_type": {
        "name": "经验型",
        "description": "分享自己类似经历或经验",
        "keywords": ["我之前", "我也", "我家", "以前", "上次", "经验", "其实", "不过", "个人感觉", "根据我"],
        "sentiment": "neutral",
        "emoji_hint": "🤔💭",
        "example_templates": [
            "我之前也买过，确实好用",
            "我家用的就是这个牌子",
            "根据我的经验，耐用",
            "不过要注意保养",
        ],
    },
    "questioning_type": {
        "name": "质疑型",
        "description": "对内容有疑问或不同看法",
        "keywords": ["但是", "不对", "假的", "真的吗", "我不信", "真的吗", "能信吗", "这是推广吧", "充值了", "质疑"],
        "sentiment": "negative",
        "emoji_hint": "🤨❓",
        "example_templates": [
            "真的假的？看着有点假",
            "这是广告吧，理性种草",
            "感觉有剧本",
            "说实话，不太敢信",
        ],
    },
    "crowding_type": {
        "name": "凑热闹型",
        "description": "路过围观，表达情绪反应",
        "keywords": ["哈哈哈", "笑死", "绝了", "太牛了", "救命", "哈哈", "笑死我了", "真绝", "厉害", "太强"],
        "sentiment": "positive",
        "emoji_hint": "😂🤣",
        "example_templates": [
            "哈哈哈笑死我了",
            "救命这也太绝了",
            "哈哈哈哈哈停不下来",
            "笑死，这谁能忍住",
        ],
    },
    "seeking_type": {
        "name": "求同款型",
        "description": "想要知道是什么产品或链接",
        "keywords": ["链接", "求", "哪里买", "什么牌子", "同款", "在哪", "型号", "多少钱", "求同款", "求链接"],
        "sentiment": "neutral",
        "emoji_hint": "🙏🙋",
        "example_templates": [
            "链接呢？求求了",
            "哪里买的？求告知",
            "同款在哪入的呀",
            "博主求链接！",
        ],
    },
    "help_type": {
        "name": "求助型",
        "description": "遇到问题寻求帮助",
        "keywords": ["怎么办", "求救", "求助", "问一下", "请问", "怎么弄", "求助", "新手", "不懂", "求教"],
        "sentiment": "neutral",
        "emoji_hint": "😢🙏",
        "example_templates": [
            "请问这个哪里有卖？",
            "新手第一次买，求教",
            "这个怎么选啊？",
            "求助，买哪个好",
        ],
    },
    "general_type": {
        "name": "普通型",
        "description": "一般性评论",
        "keywords": [],
        "sentiment": "neutral",
        "emoji_hint": "💬",
        "example_templates": [
            "不错",
            "已看",
            "好的",
            "收到",
            "👍",
        ],
    },
}

# 默认类型
DEFAULT_PERSONA = "general_type"

# ═══════════════════════════════════════════════════════════════
# 品类评论分布（基于数据分析）
# ═══════════════════════════════════════════════════════════════

CATEGORY_PERSONA_DIST = {
    "food": {"grass_type": 0.30, "experience_type": 0.22, "questioning_type": 0.18, "crowding_type": 0.10, "seeking_type": 0.10, "help_type": 0.10},
    "fashion": {"grass_type": 0.35, "experience_type": 0.15, "questioning_type": 0.15, "crowding_type": 0.10, "seeking_type": 0.20, "help_type": 0.05},
    "tech": {"grass_type": 0.20, "experience_type": 0.25, "questioning_type": 0.25, "crowding_type": 0.08, "seeking_type": 0.12, "help_type": 0.10},
    "travel": {"grass_type": 0.25, "experience_type": 0.20, "questioning_type": 0.15, "crowding_type": 0.15, "seeking_type": 0.15, "help_type": 0.10},
    "lifestyle": {"grass_type": 0.28, "experience_type": 0.20, "questioning_type": 0.18, "crowding_type": 0.15, "seeking_type": 0.10, "help_type": 0.09},
    "other": {"grass_type": 0.25, "experience_type": 0.20, "questioning_type": 0.18, "crowding_type": 0.12, "seeking_type": 0.15, "help_type": 0.10},
}

# ═══════════════════════════════════════════════════════════════
# 点赞预估模型参数
# ═══════════════════════════════════════════════════════════════

LIKE_MODEL_PARAMS = {
    "grass_type": {"base": 5, "viral_base": 500, "decay": 0.7},
    "experience_type": {"base": 3, "viral_base": 300, "decay": 0.8},
    "questioning_type": {"base": 8, "viral_base": 800, "decay": 0.6},  # 争议性评论点赞更高
    "crowding_type": {"base": 15, "viral_base": 2000, "decay": 0.5},  # 搞笑评论点赞最高
    "seeking_type": {"base": 2, "viral_base": 200, "decay": 0.9},
    "help_type": {"base": 1, "viral_base": 150, "decay": 0.9},
    "general_type": {"base": 2, "viral_base": 300, "decay": 0.8},
}


def classify_comment(text: str) -> str:
    """
    根据评论内容分类到6种用户画像
    """
    if not text:
        return DEFAULT_PERSONA

    text_lower = text.lower()

    # 关键词匹配
    scores = {}
    for persona_type, persona_info in COMMENT_PERSONAS.items():
        score = 0
        for keyword in persona_info["keywords"]:
            if keyword.lower() in text_lower:
                score += 1
        scores[persona_type] = score

    # 返回得分最高的类型
    best_type = DEFAULT_PERSONA
    best_score = 0
    for p_type, score in scores.items():
        if score > best_score:
            best_score = score
            best_type = p_type

    # 如果没有匹配，返回 general_type
    if best_score == 0:
        return DEFAULT_PERSONA

    return best_type


def predict_likes(persona_type: str, comment_length: int, sentiment: str, engagement_level: str = "normal") -> int:
    """
    预估评论点赞数

    Args:
        persona_type: 用户画像类型
        comment_length: 评论长度
        sentiment: 情感 (positive/neutral/negative)
        engagement_level: 内容互动水平 (low/normal/high/viral)

    Returns:
        预估点赞数
    """
    params = LIKE_MODEL_PARAMS.get(persona_type, LIKE_MODEL_PARAMS["general_type"])

    # 基础点赞
    base = params["base"]

    # 内容长度调整
    if comment_length < 10:
        length_factor = 0.8
    elif comment_length < 30:
        length_factor = 1.0
    elif comment_length < 60:
        length_factor = 1.2
    else:
        length_factor = 0.9  # 太长的评论点赞反而少

    # 情感调整
    sentiment_factor = 1.0
    if sentiment == "positive":
        sentiment_factor = 1.2
    elif sentiment == "negative":
        sentiment_factor = 1.5  # 争议评论点赞更高

    # 互动水平调整
    engagement_factor = 1.0
    if engagement_level == "high":
        engagement_factor = 3.0
    elif engagement_level == "viral":
        engagement_factor = 10.0
    elif engagement_level == "low":
        engagement_factor = 0.3

    predicted = base * length_factor * sentiment_factor * engagement_factor

    # 添加随机波动
    noise = random.uniform(0.7, 1.3)
    predicted *= noise

    return max(0, int(predicted))


def generate_comment(
    category: str,
    persona_type: str,
    context: Optional[dict] = None,
    existing_comments: Optional[list] = None,
    engagement_level: str = "normal",
) -> dict:
    """
    生成一条模拟评论

    Args:
        category: 内容品类
        persona_type: 用户画像类型
        context: 可选，包含视频/内容信息的上下文
        existing_comments: 可选，已有的评论列表（避免重复）
        engagement_level: 内容互动水平 (low/normal/high/viral)

    Returns:
        dict: {text, like_count, persona, sentiment, tips}
    """
    persona = COMMENT_PERSONAS.get(persona_type, COMMENT_PERSONAS["general_type"])

    # 选择模板或生成
    templates = persona["example_templates"]

    # 如果有上下文，可以个性化
    if context:
        template = random.choice(templates)
        text = template
    else:
        text = random.choice(templates)

    # 随机添加emoji或变化
    if random.random() < 0.3:
        emoji = random.choice(["😂", "🤣", "😭", "😍", "🤔", "👍", "✨", "💕", "🙈", "🤷"])
        if random.random() < 0.5:
            text = f"{text} {emoji}"
        else:
            text = f"{emoji} {text}"

    # 随机调整长度
    if random.random() < 0.2:
        additions = ["+1", "真的", "确实", "哈哈", "～", "!!"]
        text = text + random.choice(additions)

    # 预估点赞（考虑 engagement_level）
    sentiment = persona["sentiment"]
    like_count = predict_likes(persona_type, len(text), sentiment, engagement_level)

    return {
        "text": text,
        "like_count": like_count,
        "persona": persona_type,
        "persona_name": persona["name"],
        "sentiment": sentiment,
        "tips": f"这是一个{persona['name']}评论，{persona['description']}",
    }


def generate_comment_section(
    category: str,
    num_comments: int = 8,
    engagement_level: str = "normal",
    existing_comments: Optional[list] = None,
) -> list:
    """
    生成一组模拟评论（模拟真实评论区）

    Args:
        category: 内容品类
        num_comments: 评论数量
        engagement_level: 内容互动水平
        existing_comments: 可选，避免重复的已有评论

    Returns:
        list[dict]: 评论列表
    """
    # 获取品类分布
    dist = CATEGORY_PERSONA_DIST.get(category, CATEGORY_PERSONA_DIST["other"])

    # 按分布生成各类型数量
    persona_counts = {}
    remaining = num_comments
    for p_type, ratio in sorted(dist.items(), key=lambda x: -x[1]):
        if remaining <= 0:
            break
        count = int(num_comments * ratio)
        count = min(count, remaining)
        persona_counts[p_type] = count
        remaining -= count

    # 确保数量足够
    if remaining > 0 and persona_counts:
        # 加到最常见的类型
        first_type = list(persona_counts.keys())[0]
        persona_counts[first_type] += remaining

    # 生成评论
    comments = []
    for p_type, count in persona_counts.items():
        for _ in range(count):
            comment = generate_comment(category, p_type, engagement_level=engagement_level)
            # 避免完全重复
            if existing_comments and any(c["text"] == comment["text"] for c in existing_comments):
                comment["text"] = comment["text"] + " " + random.choice(["+1", "确实", "哈哈"])
            comments.append(comment)

    # 打乱顺序
    random.shuffle(comments)

    # 按点赞数排序（高赞在前）
    comments.sort(key=lambda x: x["like_count"], reverse=True)

    return comments


def get_persona_distribution(category: str) -> dict:
    """
    获取指定品类的评论画像分布
    """
    dist = CATEGORY_PERSONA_DIST.get(category, CATEGORY_PERSONA_DIST["other"])
    return {
        "category": category,
        "distribution": {p: round(r * 100, 1) for p, r in dist.items()},
        "total_types": len(dist),
    }


# ═══════════════════════════════════════════════════════════════
# 数据库分析功能
# ═══════════════════════════════════════════════════════════════

def analyze_comment_patterns() -> dict:
    """
    分析数据库中评论的分布模式
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    results = {}

    # 各品类评论数
    cursor.execute("""
        SELECT category, COUNT(*) as cnt
        FROM comment_database
        GROUP BY category
    """)
    results["category_count"] = {row[0]: row[1] for row in cursor.fetchall()}

    # 各类型分布
    cursor.execute("""
        SELECT comment_type, COUNT(*) as cnt
        FROM comment_database
        GROUP BY comment_type
        ORDER BY cnt DESC
    """)
    results["type_distribution"] = {row[0]: row[1] for row in cursor.fetchall()}

    # 情感分布
    cursor.execute("""
        SELECT sentiment, COUNT(*) as cnt
        FROM comment_database
        GROUP BY sentiment
    """)
    results["sentiment_distribution"] = {row[0]: row[1] for row in cursor.fetchall()}

    # 平均评论长度
    cursor.execute("""
        SELECT AVG(LENGTH(text)) as avg_len
        FROM comment_database
    """)
    results["avg_comment_length"] = cursor.fetchone()[0]

    conn.close()
    return results


def get_real_comments_by_type(persona_type: str, category: str, limit: int = 10) -> list:
    """
    从数据库获取指定类型和品类的真实评论示例
    """
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = lambda b: b.decode("utf-8", errors="ignore")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT text, like_count, sentiment
        FROM comment_database
        WHERE comment_type = ? AND category = ?
        ORDER BY like_count DESC
        LIMIT ?
    """, (persona_type, category, limit))

    comments = []
    for text, like_count, sentiment in cursor.fetchall():
        if text:
            comments.append({
                "text": text[:100],  # 截断
                "like_count": like_count,
                "sentiment": sentiment,
            })

    conn.close()
    return comments


if __name__ == "__main__":
    # 测试评论生成
    print("=== Comment Persona Engine Test ===\n")

    # 测试各类评论生成
    personas = list(COMMENT_PERSONAS.keys())
    for cat in ["food", "tech", "lifestyle"]:
        print(f"\n[{cat}] Generated comments:")
        comments = generate_comment_section(cat, num_comments=6, engagement_level="normal")
        for i, c in enumerate(comments[:4], 1):
            print(f"  {i}. [{c['persona_name']}] {c['text'][:40]}... (❤{c['like_count']})")

    # 测试分类
    print("\n\n=== Comment Classification Test ===")
    test_texts = [
        "已入手，等快递中",
        "这也太假了吧",
        "哈哈哈笑死我了",
        "求链接，求求了",
        "请问这个在哪里买",
    ]
    for text in test_texts:
        persona = classify_comment(text)
        print(f"  '{text[:20]}' -> {persona}")

    print("\n=== Analysis ===")
    analysis = analyze_comment_patterns()
    print(f"  Total comments: {sum(analysis['category_count'].values())}")
    print(f"  Type distribution: {analysis['type_distribution']}")
