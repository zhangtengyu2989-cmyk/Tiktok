"""
用户模拟 Agent
模拟目标受众看到作品的第一反应和评论。

集成 Comment Persona Engine：
- 基于 6782 条真实评论训练的算法引擎
- 6种用户画像分布 + 点赞预估模型
- 无 LLM 调用的即时评论生成
"""
from __future__ import annotations

import json
import random

from app.agents.base_agent import BaseAgent
from app.agents.prompts.user_sim_agent import SYSTEM_PROMPT
from app.agents.research_data import build_data_prompt_for_agent
from app.agents.comment_persona_engine import (
    generate_comment_section,
    get_persona_distribution,
    COMMENT_PERSONAS,
)


# 抖音风格昵称生成
NICKNAME_PREFIXES = [
    "爱吃的", "减脂打卡", "北漂", "暴躁", "奶茶续命", "考研倒计时",
    "爱音乐", "健身日记", "职场妈妈", "数码控", "旅行家", "吃货本货",
    "生活家", "宝藏发现", "测评小能手", "新手妈妈", "上班族",
]
NICKNAME_SUFFIXES = [
    "阳阳", "小张", "小林", "小王", "阿花", "肉肉", "泡泡", "豆豆",
    "明明", "婷婷", "小雨", "小雪", "阿杰", "老王", "小鱼", "小七",
]
IP_LOCATIONS = ["北京", "广东", "浙江", "四川", "上海", "江苏", "湖北", "山东", "河南", "福建"]


def _generate_douyin_nickname() -> str:
    """生成抖音风格昵称"""
    if random.random() < 0.3:
        # 带数字的昵称（如"减脂第30天"）
        prefix = random.choice(NICKNAME_PREFIXES)
        suffix = random.choice(["第", ""]) + str(random.randint(1, 365)) + random.choice(["天", "天啦", "天打卡"])
        return prefix + suffix
    return random.choice(NICKNAME_PREFIXES) + random.choice(NICKNAME_SUFFIXES)


def _generate_douyin_style_comments(category: str, num_comments: int = 8, engagement_level: str = "normal") -> list[dict]:
    """
    基于 comment_persona_engine 生成抖音风格评论
    直接使用算法，无需 LLM 调用
    """
    # 使用 comment_persona_engine 的算法生成评论
    engine_comments = generate_comment_section(
        category=category,
        num_comments=num_comments,
        engagement_level=engagement_level,
    )

    # 转换为抖音格式
    douyin_comments = []
    emoji_map = {
        "grass_type": "🛒",
        "experience_type": "💭",
        "questioning_type": "🤔",
        "crowding_type": "😂",
        "seeking_type": "🙏",
        "help_type": "😢",
        "general_type": "💬",
    }

    for c in engine_comments:
        persona_type = c.get("persona", "general_type")
        emoji = emoji_map.get(persona_type, "💬")

        # 生成时间（1小时前～30天前）
        days = random.randint(0, 30)
        hours = random.randint(1, 23)
        if days == 0:
            time_ago = f"{hours}小时前"
        elif days == 1:
            time_ago = "昨天"
        else:
            time_ago = f"{days}天前"

        # 抖音用户名
        username = _generate_douyin_nickname()

        douyin_comments.append({
            "username": username,
            "avatar_emoji": emoji,
            "comment": c.get("text", ""),
            "sentiment": c.get("sentiment", "neutral"),
            "likes": c.get("like_count", 0),
            "time_ago": time_ago,
            "ip_location": random.choice(IP_LOCATIONS),
            "persona": c.get("persona_name", "普通型"),
        })

    return douyin_comments


class UserSimAgent(BaseAgent):
    """模拟目标用户的反应和评论"""

    agent_name = "用户模拟器"
    system_prompt = SYSTEM_PROMPT

    def build_user_message(
        self,
        title: str,
        content: str,
        category: str,
        tags: list[str],
        simulated_comments: list = None,
    ) -> str:
        """构建完整作品内容供模拟"""
        category_names = {"food": "美食", "fashion": "穿搭", "tech": "科技", "travel": "旅行", "lifestyle": "生活"}
        cat_cn = category_names.get(category, category)

        # 如果已有算法生成的评论，将其作为上下文
        comments_context = ""
        if simulated_comments:
            comments_str = "\n".join([
                f'- {c.get("comment", "")[:50]} (❤{c.get("likes", 0)}, {c.get("persona", "")})'
                for c in simulated_comments[:6]
            ])
            comments_context = f"\n\n## 已生成的模拟评论（基于{category}品类真实数据分布）\n{comments_str}\n\n请分析以上评论的用户画像分布，并给出诊断意见。"

        msg = f"""## 待模拟的作品
- **垂类**: {cat_cn}
- **标题**: {title}
- **标签**: {json.dumps(tags, ensure_ascii=False)}
- **正文**:
{content if content else '（正文为空，仅有标题和封面）'}
{comments_context}

请模拟不同类型的抖音用户看到这条视频后的反应，并分析用户画像分布。"""
        msg += build_data_prompt_for_agent("user_sim", category)
        return msg

    async def diagnose(
        self,
        title: str = "",
        content: str = "",
        category: str = "food",
        tags: list = None,
        engagement_level: str = "normal",
        **kwargs,
    ) -> dict:
        """
        执行用户模拟。
        优先使用算法生成的评论（无需 LLM），再由 LLM 分析用户画像。
        """
        tags = tags or []

        # Step 1: 使用 comment_persona_engine 立即生成评论（无 LLM 调用）
        douyin_comments = _generate_douyin_style_comments(
            category=category,
            num_comments=8,
            engagement_level=engagement_level,
        )

        # Step 2: 获取品类用户画像分布
        persona_dist = get_persona_distribution(category)

        # Step 3: 用 LLM 分析用户反应（传入已生成的评论作为上下文）
        msg = self.build_user_message(
            title=title,
            content=content,
            category=category,
            tags=tags,
            simulated_comments=douyin_comments,
        )

        try:
            llm_result = await self.call_llm(msg)
        except Exception as e:
            # LLM 失败时，返回算法生成的结果
            llm_result = {"dimension": "用户反应", "reasoning": f"LLM 调用失败: str(e)"}

        # 合并结果：算法评论 + LLM 分析
        return {
            "agent_name": self.agent_name,
            "dimension": "用户反应",
            "score": llm_result.get("score", 75),
            "persona_distribution": persona_dist.get("distribution", {}),
            "persona_insights": llm_result.get("reasoning", "基于品类真实评论分布生成"),
            "issues": llm_result.get("issues", []),
            "suggestions": llm_result.get("suggestions", []),
            "simulated_comments": douyin_comments,  # 算法生成的评论
            "reasoning": llm_result.get("reasoning", ""),
        }
