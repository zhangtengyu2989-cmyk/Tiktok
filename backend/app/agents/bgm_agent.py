"""
BGM 分析师 Agent
分析背景音乐的推广价值和适配度。
"""
from __future__ import annotations

import logging
import os

from app.agents.base_agent import BaseAgent
from app.agents.prompts.bgm_agent import SYSTEM_PROMPT
from app.agents.research_data import build_data_prompt_for_agent, BGM_HEAT_LEVELS, get_heat_level

logger = logging.getLogger("tiktokrx.bgm_agent")


class BGMAgent(BaseAgent):
    """分析BGM热度、适配度和推流影响"""

    agent_name = "BGM分析师"
    system_prompt = SYSTEM_PROMPT

    async def diagnose(
        self,
        title: str,
        category: str,
        bgm_name: str = None,
        bgm_heat: int = 0,
        bgm_style: str = None,
        content_mood: str = None,
    ) -> dict:
        """
        诊断BGM的推广价值。

        @param title - 内容标题
        @param category - 内容品类
        @param bgm_name - BGM名称（可选）
        @param bgm_heat - BGM热度指数（可选）
        @param bgm_style - BGM风格（可选）
        @param content_mood - 内容情绪（可选）
        @returns dict 包含评分、issues、suggestions
        """
        # 构建数据驱动的提示词
        data_prompt = build_data_prompt_for_agent("bgm", category)
        system = self.system_prompt + data_prompt

        user_message = self.build_user_message(
            title=title,
            category=category,
            bgm_name=bgm_name,
            bgm_heat=bgm_heat,
            bgm_style=bgm_style,
            content_mood=content_mood,
        )

        result = await self.call_llm(user_message, system_override=system)

        # 如果没有返回有效结果，生成默认诊断
        if result.get("dimension") == "error" or not result.get("score"):
            return self._generate_default_diagnosis(
                title=title,
                category=category,
                bgm_name=bgm_name,
                bgm_heat=bgm_heat,
                bgm_style=bgm_style,
            )

        return result

    def build_user_message(self, **kwargs) -> str:
        title = kwargs.get("title", "")
        category = kwargs.get("category", "")
        bgm_name = kwargs.get("bgm_name", "")
        bgm_heat = kwargs.get("bgm_heat", 0)
        bgm_style = kwargs.get("bgm_style", "")
        content_mood = kwargs.get("content_mood", "")

        msg = f"""请分析以下内容的BGM：

【内容信息】
- 标题：{title}
- 品类：{category}
- BGM名称：{bgm_name or '未提供'}
- BGM热度指数：{bgm_heat or '未提供'}
- BGM风格：{bgm_style or '未提供'}
- 内容情绪：{content_mood or '未提供'}

请从以下维度进行诊断：
1. BGM热度等级评估
2. 内容适配度分析
3. 推流影响预测
4. 受众匹配度评估
5. 替代BGM推荐（如有）

请以JSON格式输出，包含：
- agent_name: "BGM分析师"
- dimension: "BGM适配"
- score: 0-100的总评分
- current_bgm: {{name, heat_index, heat_level}}
- issues: 问题列表
- suggestions: 建议列表
- traffic_impact: 推流影响预测
- alternatives: 推荐替代BGM列表
"""
        return msg

    def _generate_default_diagnosis(
        self,
        title: str,
        category: str,
        bgm_name: str = None,
        bgm_heat: int = 0,
        bgm_style: str = None,
    ) -> dict:
        """当LLM调用失败时，生成基于规则的默认诊断"""
        heat_level = get_heat_level(bgm_heat) if bgm_heat > 0 else "C"
        heat_info = BGM_HEAT_LEVELS.get(heat_level, BGM_HEAT_LEVELS["C"])

        # 根据热度等级计算基础评分
        base_scores = {
            "S+": 95,
            "S": 85,
            "A": 72,
            "B": 55,
            "C": 35,
        }
        score = base_scores.get(heat_level, 50)

        issues = []
        suggestions = []
        traffic_impact = heat_info.get("traffic_weight", "0%")

        if heat_level == "C":
            issues.append(f"BGM「{bgm_name or '未知'}」热度较低（{bgm_heat}），可能无法获得推流加权")
            suggestions.append("建议更换为热度等级A及以上BGM，可获得额外推流加权")
        elif heat_level == "B":
            issues.append(f"BGM热度为B级（{bgm_heat}），推流加权有限（+5%）")
            suggestions.append("可考虑升级到A级BGM，获得+15%推流加权")

        # 内容适配度检查
        category_styles = {
            "food": ["欢快", "温馨", "轻快"],
            "fashion": ["潮流", "节奏感", "动感"],
            "tech": ["电子", "未来感", "专业"],
            "travel": ["舒缓", "大气", "治愈"],
            "lifestyle": ["温馨", "生活化", "共鸣"],
        }
        if bgm_style:
            matching_styles = category_styles.get(category, [])
            if bgm_style not in matching_styles:
                issues.append(f"BGM风格「{bgm_style}」可能与{category}品类不太适配")
                suggestions.append(f"建议选择{category}品类的适配风格：{', '.join(matching_styles)}")

        return {
            "agent_name": "BGM分析师",
            "dimension": "BGM适配",
            "score": score,
            "current_bgm": {
                "name": bgm_name or "未知",
                "heat_index": bgm_heat or 0,
                "heat_level": heat_level,
            },
            "issues": issues,
            "suggestions": suggestions,
            "traffic_impact": traffic_impact,
            "alternatives": [],
            "reasoning": f"基于BGM热度等级{heat_level}的默认诊断",
        }
