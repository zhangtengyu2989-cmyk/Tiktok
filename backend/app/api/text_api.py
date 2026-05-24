"""
纯文字文章分析 API - 独立的纯文字内容质量评估
"""
from __future__ import annotations

import logging
import os
import sqlite3

from fastapi import APIRouter, HTTPException

from app.agents.research_data import MODEL_PARAMS, CATEGORY_CN

router = APIRouter()
logger = logging.getLogger("tiktokrx.text")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "tiktok_baseline.db")


def _analyze_text_structure(text: str) -> dict:
    """分析文字结构特征"""
    import re

    # 段落分析
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    paragraph_count = len(paragraphs)

    # 字数统计
    char_count = len(text)
    chinese_chars = len(re.findall(r'[一-鿿]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))

    # 句子分析
    sentences = re.split(r'[。！？.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)
    avg_sentence_len = char_count / max(sentence_count, 1)

    # emoji统计
    emojis = re.findall(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
        r'\U0001F900-\U0001F9FF\U00002702-\U000027B0✨🔥💡📌❗]',
        text
    )
    emoji_count = len(emojis)

    # 情绪词统计
    positive_words = ['好', '棒', '赞', '美', '爱', '喜欢', '开心', '快乐', '幸福', '完美', '绝了', '太', '超', '巨']
    negative_words = ['差', '坏', '难', '丑', '糟', '坑', '后悔', '失望', '难过', '生气']
    emotion_words = positive_words + negative_words

    positive_count = sum(1 for w in positive_words if w in text)
    negative_count = sum(1 for w in negative_words if w in text)

    # 互动引导词统计
    interaction_triggers = ['你们', '我们', '大家', '觉得', '认为', ' comment', '评论', '说说', '聊聊',
                           '点赞', '收藏', '转发', '关注', '一起', '来聊聊', '你们呢']
    trigger_count = sum(1 for t in interaction_triggers if t in text)

    # 数字统计
    numbers = re.findall(r'\d+', text)
    number_count = len(numbers)

    # 钩子词统计
    hook_words = ['竟然', '原来', '终于', '其实', '但是', '所以', '为什么', '怎么', '是不是', '一定',
                  '必须', '千万', '万万', '揭秘', '曝光', '真相', '必看', '收藏', '转发']
    hook_count = sum(1 for h in hook_words if h in text)

    return {
        "paragraph_count": paragraph_count,
        "char_count": char_count,
        "chinese_chars": chinese_chars,
        "english_chars": english_chars,
        "sentence_count": sentence_count,
        "avg_sentence_length": round(avg_sentence_len, 1),
        "emoji_count": emoji_count,
        "positive_emotion_count": positive_count,
        "negative_emotion_count": negative_count,
        "emotion_tendency": "positive" if positive_count > negative_count else ("negative" if negative_count > positive_count else "neutral"),
        "emotion_intensity": min(10, max(1, (positive_count + negative_count))),
        "interaction_trigger_count": trigger_count,
        "number_count": number_count,
        "hook_count": hook_count,
    }


def _score_text_dimensions(structure: dict, category: str) -> dict:
    """基于文字结构计算各维度评分"""
    p = MODEL_PARAMS.get(category, MODEL_PARAMS.get("lifestyle", {}))

    # 文字节奏评分（段落数量、句子长度）
    paragraph_score = 80
    if p.get("content_length"):
        opt_range = p["content_length"]
        if opt_range.get("min", 0) <= structure["char_count"] <= opt_range.get("max", 9999):
            paragraph_score = 90
        elif structure["char_count"] < opt_range.get("min", 0):
            paragraph_score = max(60, 80 - (opt_range.get("min", 0) - structure["char_count"]) // 20)
        else:
            paragraph_score = max(50, 80 - (structure["char_count"] - opt_range.get("max", 9999)) // 30)

    # 情绪分析评分
    emotion_score = 70
    if structure["emotion_intensity"] >= 3:
        emotion_score = min(95, 70 + structure["emotion_intensity"] * 5)
    elif structure["emotion_intensity"] == 0:
        emotion_score = 50

    # 互动引导评分
    interaction_score = 60
    if structure["interaction_trigger_count"] >= 2:
        interaction_score = min(95, 60 + structure["interaction_trigger_count"] * 15)
    elif structure["interaction_trigger_count"] == 1:
        interaction_score = 70

    # 信息密度评分
    density_score = 70
    if structure["char_count"] > 0:
        info_density = (structure["chinese_chars"] / structure["char_count"]) * 100
        if info_density >= 60:
            density_score = 85
        elif info_density >= 40:
            density_score = 70
        else:
            density_score = 55

    # 排版结构评分
    layout_score = 70
    if structure["paragraph_count"] >= 3:
        layout_score = min(90, 60 + structure["paragraph_count"] * 8)
    if structure["emoji_count"] >= 3:
        layout_score = min(95, layout_score + 10)

    # 综合内容质量
    content_quality = (
        paragraph_score * 0.25 +
        emotion_score * 0.25 +
        density_score * 0.20 +
        interaction_score * 0.20 +
        layout_score * 0.10
    )

    return {
        "文字节奏": {"score": round(paragraph_score, 1), "issues": [], "suggestions": []},
        "情绪分析": {
            "score": round(emotion_score, 1),
            "emotion_tendency": structure["emotion_tendency"],
            "intensity": structure["emotion_intensity"],
            "issues": [],
            "suggestions": []
        },
        "信息密度": {"score": round(density_score, 1), "issues": [], "suggestions": []},
        "互动引导": {
            "score": round(interaction_score, 1),
            "trigger_density": round(structure["interaction_trigger_count"] / max(structure["char_count"] / 100, 1), 2),
            "issues": [],
            "suggestions": []
        },
        "排版结构": {"score": round(layout_score, 1), "issues": [], "suggestions": []},
        "content_quality": round(content_quality, 1),
    }


def _generate_text_suggestions(structure: dict, scores: dict, category: str) -> list:
    """生成优化建议"""
    suggestions = []
    cn = CATEGORY_CN.get(category, category)

    if structure["char_count"] < 100:
        suggestions.append({
            "priority": 1,
            "description": f"内容过短（{structure['char_count']}字），建议补充至200-300字以提高信息密度",
            "expected_impact": "提升互动率和完播率"
        })
    elif structure["char_count"] > 500:
        suggestions.append({
            "priority": 2,
            "description": f"内容偏长（{structure['char_count']}字），建议精简至300字以内",
            "expected_impact": "提高用户完读率"
        })

    if structure["emotion_intensity"] < 3:
        suggestions.append({
            "priority": 2,
            "description": "情绪表达较弱，建议增加情绪词提升共鸣感",
            "expected_impact": "提升点赞和评论意愿"
        })

    if structure["interaction_trigger_count"] < 2:
        suggestions.append({
            "priority": 2,
            "description": "缺少互动引导词，建议添加'你们觉得呢'、'评论区告诉我'等",
            "expected_impact": "提升评论率和互动率"
        })

    if structure["emoji_count"] < 3:
        suggestions.append({
            "priority": 3,
            "description": "emoji使用较少，建议每段添加1-2个emoji作为视觉锚点",
            "expected_impact": "提升阅读体验和停留时间"
        })

    if structure["hook_count"] < 1:
        suggestions.append({
            "priority": 3,
            "description": "缺少钩子词，建议在开头使用'竟然'、'揭秘'等词吸引注意力",
            "expected_impact": "提升点击率和完播率"
        })

    return suggestions


@router.post("/analyze-text")
async def analyze_text(
    text: str,
    category: str = "lifestyle",
    title: str = ""
):
    """
    纯文字文章专项分析。
    分析维度：文字节奏、情绪分析、信息密度、互动引导、排版结构。
    """
    if not text or not text.strip():
        raise HTTPException(400, "请提供要分析的正文内容")

    # 结构分析
    structure = _analyze_text_structure(text)

    # 维度评分
    scores = _score_text_dimensions(structure, category)

    # 生成建议
    suggestions = _generate_text_suggestions(structure, scores, category)

    # 综合评分
    content_quality_score = scores.pop("content_quality", 70)

    # 获取品类基线
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    baseline_text = {}
    try:
        cursor.execute(
            """SELECT avg_text_length, optimal_text_length_min, optimal_text_length_max,
                      emotion_density, interaction_trigger_avg, optimal_paragraph_count
               FROM text_baseline
               WHERE category = ?""",
            (category,)
        )
        row = cursor.fetchone()
        if row:
            baseline_text = {
                "avg_text_length": row[0],
                "optimal_text_length_min": row[1],
                "optimal_text_length_max": row[2],
                "emotion_density": row[3],
                "interaction_trigger_avg": row[4],
                "optimal_paragraph_count": row[5],
            }
    except Exception:
        pass
    finally:
        conn.close()

    # 雷达数据
    radar_data = {
        "内容质量": content_quality_score,
        "增长策略": scores.get("互动引导", {}).get("score", 60),
        "用户共鸣": scores.get("情绪分析", {}).get("score", 60),
        "视觉呈现": scores.get("排版结构", {}).get("score", 60),
        "技术表现": 80,  # 纯文字无技术问题
        "综合评分": round(content_quality_score * 0.3 + 70 * 0.7, 1),
    }

    # 组装issues
    issues = []
    if structure["char_count"] < 100:
        issues.append({
            "severity": "high",
            "description": f"内容过短（{structure['char_count']}字），信息量不足",
            "from_agent": "文字分析"
        })
    if structure["emotion_intensity"] < 3:
        issues.append({
            "severity": "medium",
            "description": "情绪表达较弱，缺乏共鸣点",
            "from_agent": "文字分析"
        })
    if structure["interaction_trigger_count"] < 1:
        issues.append({
            "severity": "medium",
            "description": "缺少互动引导，可能影响评论率",
            "from_agent": "文字分析"
        })

    return {
        "overall_score": round(content_quality_score, 1),
        "grade": "S" if content_quality_score >= 90 else (
            "A" if content_quality_score >= 75 else (
                "B" if content_quality_score >= 60 else (
                    "C" if content_quality_score >= 40 else "D"
                )
            )
        ),
        "radar_data": radar_data,
        "sub_scores": scores,
        "structure": structure,
        "issues": issues,
        "suggestions": suggestions,
        "emotion_tendency": structure["emotion_tendency"],
        "emotion_intensity": structure["emotion_intensity"],
        "recommended_tags": _generate_recommended_tags(structure, category),
    }


def _generate_recommended_tags(structure: dict, category: str) -> list:
    """基于内容结构生成推荐标签"""
    tags = []

    # 基于品类添加基础标签
    category_tags = {
        "food": ["美食", "日常", "分享"],
        "fashion": ["穿搭", "时尚", "分享"],
        "tech": ["科技", "测评", "分享"],
        "travel": ["旅行", "攻略", "分享"],
        "lifestyle": ["生活", "日常", "分享"],
    }
    tags.extend(category_tags.get(category, ["日常"]))

    # 基于情绪添加标签
    if structure["emotion_tendency"] == "positive":
        tags.append("正能量")
    elif structure["emotion_tendency"] == "negative":
        tags.append("吐槽")

    # 基于互动触发词添加标签
    if structure["interaction_trigger_count"] >= 3:
        tags.append("讨论")

    # 基于钩子词添加标签
    if structure["hook_count"] >= 2:
        tags.append("必看")

    return list(set(tags))[:6]  # 去重，最多6个标签


@router.get("/text-baseline/{category}")
async def get_text_baseline(category: str):
    """获取品类的纯文字内容基线数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """SELECT category, avg_text_length, optimal_text_length_min, optimal_text_length_max,
                      emotion_density, interaction_trigger_avg, optimal_paragraph_count
               FROM text_baseline
               WHERE category = ?""",
            (category,)
        )
        row = cursor.fetchone()
        if not row:
            return {
                "category": category,
                "avg_text_length": 200,
                "optimal_text_length_min": 100,
                "optimal_text_length_max": 300,
                "emotion_density": 0.3,
                "interaction_trigger_avg": 2,
                "optimal_paragraph_count": 5,
            }
        return {
            "category": row[0],
            "avg_text_length": row[1],
            "optimal_text_length_min": row[2],
            "optimal_text_length_max": row[3],
            "emotion_density": row[4],
            "interaction_trigger_avg": row[5],
            "optimal_paragraph_count": row[6],
        }
    except Exception as e:
        logger.error("Failed to fetch text baseline: %s", e)
        raise HTTPException(500, "Failed to fetch baseline data")
    finally:
        conn.close()
