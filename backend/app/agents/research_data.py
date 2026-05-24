"""
数据驱动模块：基于真实抖音数据的研究成果。
提供品类评分参数、数据驱动提示词注入、Model A 预评分。
"""
from __future__ import annotations

import re
from typing import Optional

# ═══════════════════════════════════════════════════════════════
# BGM 热度等级定义
# ═══════════════════════════════════════════════════════════════

BGM_HEAT_LEVELS = {
    "S+": {"threshold": 1_000_000, "traffic_weight": "+30%", "description": "顶流BGM"},
    "S": {"threshold": 500_000, "traffic_weight": "+20%", "description": "热门BGM"},
    "A": {"threshold": 100_000, "traffic_weight": "+15%", "description": "上升BGM"},
    "B": {"threshold": 10_000, "traffic_weight": "+5%", "description": "普通BGM"},
    "C": {"threshold": 0, "traffic_weight": "0%", "description": "冷门BGM"},
}


def get_heat_level(heat_index: int) -> str:
    """根据热度指数返回等级"""
    if heat_index >= 1_000_000:
        return "S+"
    elif heat_index >= 500_000:
        return "S"
    elif heat_index >= 100_000:
        return "A"
    elif heat_index >= 10_000:
        return "B"
    return "C"


# ═══════════════════════════════════════════════════════════════
# 真实爆款标题（从抖音数据提取，用于 few-shot 参考）
# ═══════════════════════════════════════════════════════════════

VIRAL_TITLES: dict[str, list[str]] = {
    "food": [
        "这做法真的绝了！全家都抢着吃",
        "低成本！路边摆摊日入1000的爆款",
        "99%人不知道的隐藏吃法！赶紧收藏",
        "这一口下去，直接原地封神",
    ],
    "fashion": [
        "救命！这条裙子也太显瘦了吧",
        "158小个子｜一周穿搭不重样",
        "贫民窟女孩的宝藏店铺！质感绝了",
        "评论区问疯了的链接来了",
    ],
    "tech": [
        "买了！苹果全家桶真实使用感受",
        "2026年手机推荐！等等党终将胜利",
        "这个功能设置好，效率翻10倍",
        "深度使用一个月，憋了一肚子话",
    ],
    "travel": [
        "被问麻了！这里真的不是国外",
        "小众秘境！99%的人都不知道",
        "人均2000！穷游三天两夜攻略",
        "此生必去的绝美目的地，治愈心灵",
    ],
    "lifestyle": [
        "救命！这个东西让我戒掉手机瘾",
        "室友以为我花了多少钱，其实才",
        "极简生活一年，改变了什么",
        "当代年轻人精神状态实录",
    ],
}

# ═══════════════════════════════════════════════════════════════
# 真实用户评论（模拟抖音评论风格）
# ═══════════════════════════════════════════════════════════════

REAL_COMMENTS: dict[str, list[str]] = {
    "food": [
        "啊啊啊看着好香！明天就做",
        "这成本得多少钱啊？",
        "已收藏，等我下班试试",
        "为什么我做的和你的不一样😭",
        "老婆饼里没有老婆，这个里面也没有",
    ],
    "fashion": [
        "链接！必须要链接！",
        "158穿出170的效果，服了",
        "有没有男款啊，给我老公也来一套",
        "省吃俭用买基金，终于等到回调",
        "感觉普通身材穿不出来效果",
    ],
    "tech": [
        "等等党永远在胜利",
        "说的挺好，买了后悔两年",
        "终于有人说实话了",
        "测评视频看多了，都不知道怎么选了",
        "已经下单了，坐等打脸",
    ],
    "travel": [
        "收藏了！五一刚好去",
        "滤镜很重吧，实际很坑",
        "去年去过，确实很美",
        "求详细攻略！交通住宿",
        "假装在国外系列",
    ],
    "lifestyle": [
        "看完我默默放下了手机",
        "太真实了，说的就是我",
        "同龄人，差距怎么这么大",
        "拒绝焦虑，从刷到这条视频开始",
        "博主活得通透，支持",
    ],
}

# ═══════════════════════════════════════════════════════════════
# Model A 品类评分参数（从 876 条真实数据训练得出，2026-05-07）
# ═══════════════════════════════════════════════════════════════

MODEL_PARAMS: dict[str, dict] = {
    "food": {
        # 美食：BGM适配权重最高（0.383），内容质量其次
        "weights": {
            "content_quality": 0.163,
            "visual_performance": 0.128,
            "bgm_adaptation": 0.383,
            "growth_strategy": 0.136,
            "user_resonance": 0.064,
            "technical_performance": 0.128,
            "overall": 0.05,
        },
        "title_length": {"min": 11, "max": 30, "viral_avg": 18.3},  # 中文标题优化范围
        "content_length": {"min": 50, "max": 200},
        "video_duration": {"min": 45, "max": 90, "optimal": 60},
        "tag_count": {"min": 5, "max": 9, "best": 7},
        "image_count": {"min": 2, "max": 10},
        "baseline": {
            "avg_engagement": 142133,
            "median": 49369,
            "viral_threshold": 406554,
            "sample_size": 60,
        },
        "bgm_heat_baseline": 45000,
        "best_hours": [11, 12, 18, 19],
        "best_days": [1, 5, 6],
    },
    "fashion": {
        # 时尚：视觉权重最高（穿搭是视觉驱动型内容）
        "weights": {
            "content_quality": 0.20,
            "visual_performance": 0.30,
            "bgm_adaptation": 0.12,
            "growth_strategy": 0.15,
            "user_resonance": 0.10,
            "technical_performance": 0.08,
            "overall": 0.05,
        },
        "title_length": {"min": 11, "max": 25, "viral_avg": 14.0},
        "content_length": {"min": 50, "max": 150},
        "video_duration": {"min": 30, "max": 60, "optimal": 45},
        "tag_count": {"min": 4, "max": 8, "best": 5},
        "image_count": {"min": 2, "max": 10},
        "baseline": {
            "avg_engagement": 37058,
            "median": 12000,
            "viral_threshold": 150000,
            "sample_size": 4,  # 样本不足，使用参考值
        },
        "bgm_heat_baseline": 38000,
        "best_hours": [19, 20, 21, 12, 13],
        "best_days": [4, 5, 6],
    },
    "tech": {
        # 科技：视觉、BGM、技术并重（0.2），增长策略也很重要（0.198）
        "weights": {
            "content_quality": 0.10,
            "visual_performance": 0.20,
            "bgm_adaptation": 0.20,
            "growth_strategy": 0.198,
            "user_resonance": 0.10,
            "technical_performance": 0.20,
            "overall": 0.05,
        },
        "title_length": {"min": 15, "max": 35, "viral_avg": 17.5},
        "content_length": {"min": 100, "max": 500},
        "video_duration": {"min": 60, "max": 120, "optimal": 90},
        "tag_count": {"min": 5, "max": 9, "best": 7},
        "image_count": {"min": 1, "max": 6},
        "baseline": {
            "avg_engagement": 78901,
            "median": 31752,
            "viral_threshold": 304424,
            "sample_size": 21,
        },
        "bgm_heat_baseline": 25000,
        "best_hours": [12, 13, 20, 21, 22],
        "best_days": [2, 3, 4],
    },
    "travel": {
        # 旅行：视觉、BGM、技术均衡（~0.195），增长策略略高（0.201）
        "weights": {
            "content_quality": 0.112,
            "visual_performance": 0.195,
            "bgm_adaptation": 0.195,
            "growth_strategy": 0.201,
            "user_resonance": 0.10,
            "technical_performance": 0.195,
            "overall": 0.05,
        },
        "title_length": {"min": 15, "max": 35, "viral_avg": 14.3},
        "content_length": {"min": 100, "max": 500},
        "video_duration": {"min": 60, "max": 180, "optimal": 120},
        "tag_count": {"min": 7, "max": 11, "best": 9},
        "image_count": {"min": 4, "max": 14},
        "baseline": {
            "avg_engagement": 250893,
            "median": 78233,
            "viral_threshold": 366822,
            "sample_size": 27,
        },
        "bgm_heat_baseline": 52000,
        "best_hours": [18, 19, 20, 21],
        "best_days": [5, 6, 7],
    },
    "lifestyle": {
        # 生活：内容质量和用户共鸣重要（0.182），增长策略（0.2）
        "weights": {
            "content_quality": 0.182,
            "visual_performance": 0.174,
            "bgm_adaptation": 0.174,
            "growth_strategy": 0.20,
            "user_resonance": 0.182,
            "technical_performance": 0.087,
            "overall": 0.05,
        },
        "title_length": {"min": 15, "max": 35, "viral_avg": 19.4},
        "content_length": {"min": 50, "max": 200},
        "video_duration": {"min": 30, "max": 90, "optimal": 60},
        "tag_count": {"min": 5, "max": 9, "best": 7},
        "image_count": {"min": 1, "max": 8},
        "baseline": {
            "avg_engagement": 231659,
            "median": 36434,
            "viral_threshold": 542082,
            "sample_size": 81,
        },
        "bgm_heat_baseline": 42000,
        "best_hours": [12, 13, 21, 22, 23],
        "best_days": [0, 5, 6],
    },
    "other": {
        # 其他：视觉最重（0.232），增长策略（0.224），内容质量（0.172）
        "weights": {
            "content_quality": 0.172,
            "visual_performance": 0.232,
            "bgm_adaptation": 0.116,
            "growth_strategy": 0.224,
            "user_resonance": 0.141,
            "technical_performance": 0.116,
            "overall": 0.05,
        },
        "title_length": {"min": 15, "max": 35, "viral_avg": 20.0},
        "content_length": {"min": 50, "max": 200},
        "video_duration": {"min": 30, "max": 120, "optimal": 60},
        "tag_count": {"min": 5, "max": 9, "best": 7},
        "image_count": {"min": 1, "max": 10},
        "baseline": {
            "avg_engagement": 209362,
            "median": 31844,
            "viral_threshold": 412300,
            "sample_size": 683,
        },
        "bgm_heat_baseline": 40000,
        "best_hours": [12, 18, 19, 20, 21],
        "best_days": [1, 5, 6],
    },
}

# 品类中文名
CATEGORY_CN = {
    "food": "美食",
    "fashion": "穿搭",
    "tech": "科技",
    "travel": "旅行",
    "lifestyle": "生活",
    "other": "其他",
}


# ═══════════════════════════════════════════════════════════════
# 特征提取 + Model A 预评分
# ═══════════════════════════════════════════════════════════════

def _detect_emoji(text: str) -> bool:
    return bool(re.search(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        "\U0001F900-\U0001F9FF\U00002702-\U000027B0✨\U0001F525\U0001F49A‼⭐]",
        text or "",
    ))


def _count_hooks(title: str) -> int:
    hooks = 0
    if re.search(r'\d+', title):
        hooks += 1
    if re.search(r'[！!？?]', title):
        hooks += 1
    if re.search(r'[｜|]', title):
        hooks += 1
    if re.search(r'[✨\U0001F525‼⭐\U0001F4AF]', title):
        hooks += 1
    if re.search(r'(必|绝了|太|超|巨|神仙|宝藏|救命|麻了)', title):
        hooks += 1
    return hooks


def _range_score(value: float, opt_min: float, opt_max: float, base: float = 80) -> float:
    if opt_min <= value <= opt_max:
        mid = (opt_min + opt_max) / 2
        half = (opt_max - opt_min) / 2 + 1
        return base + (100 - base) * (1 - abs(value - mid) / half)
    elif value < opt_min:
        return max(20, base * value / max(opt_min, 1))
    else:
        return max(40, base - (value - opt_max) * 2)


def pre_score(
    title: str,
    content: str,
    category: str,
    tag_count: int = 0,
    image_count: int = 0,
    video_duration: int = 0,
    bgm_heat: int = 0,
) -> dict:
    """
    Model A 预评分。返回各维度分数和总分，用于注入到 Agent prompt 中。
    """
    p = MODEL_PARAMS.get(category, MODEL_PARAMS["lifestyle"])
    w = p["weights"]

    # 标题质量
    tl = p["title_length"]
    title_score = _range_score(len(title), tl["min"], tl["max"])
    title_score += (5 if re.search(r'\d+', title) else 0)
    title_score += min(_count_hooks(title), 3) * 3
    title_score += (2 if _detect_emoji(title + content) else 0)
    title_score = min(title_score, 100)

    # 内容质量
    cl = p["content_length"]
    content_score = min(_range_score(len(content), cl["min"], cl["max"], 85), 100)

    # 视觉质量
    ic = p["image_count"]
    visual_score = min(_range_score(image_count, ic["min"], ic["max"]), 100)

    # 标签策略
    tc = p["tag_count"]
    tag_score = max(0, 100 - abs(tag_count - tc["best"]) * 10)

    # 互动信号
    signals = 0
    if len(title) >= tl["min"]:
        signals += 25
    if re.search(r'\d+', title):
        signals += 15
    if _count_hooks(title) >= 2:
        signals += 20
    if tc["min"] <= tag_count <= tc["max"]:
        signals += 20
    if ic["min"] <= image_count <= ic["max"]:
        signals += 20
    engagement_score = min(signals, 100)

    # 视频时长（如果有）
    duration_score = 100
    if video_duration > 0:
        vd = p.get("video_duration", {})
        if vd:
            duration_score = _range_score(
                video_duration, vd.get("min", 30), vd.get("max", 180)
            )

    # BGM热度评分
    bgm_score = 100
    if bgm_heat > 0:
        heat_level = get_heat_level(bgm_heat)
        if heat_level == "S+":
            bgm_score = 100
        elif heat_level == "S":
            bgm_score = 90
        elif heat_level == "A":
            bgm_score = 75
        elif heat_level == "B":
            bgm_score = 55
        else:
            bgm_score = 30

    # 6维度标准化评分（匹配 MODEL_PARAMS weights 键名）
    dims = {
        "content_quality": round(title_score * 0.6 + content_score * 0.4, 1),  # 文案质量
        "visual_performance": round(visual_score, 1),  # 视觉表现
        "bgm_adaptation": round(bgm_score, 1),  # BGM适配度
        "growth_strategy": round(tag_score, 1),  # 增长策略
        "user_resonance": round(engagement_score, 1),  # 用户共鸣
        "technical_performance": round(duration_score, 1),  # 技术表现
    }

    total = min(round(sum(dims[k] * w[k] for k in dims), 1), 100)

    bl = p["baseline"]
    if total >= 85:
        level = "前10%（爆款潜力）"
    elif total >= 75:
        level = "前25%（优质内容）"
    elif total >= 65:
        level = "中位水平"
    else:
        level = "低于中位，建议优化"

    return {
        "total_score": total,
        "dimensions": dims,
        "weights": w,
        "level": level,
        "baseline": bl,
    }


def build_data_prompt_for_agent(agent_type: str, category: str) -> str:
    """
    为指定 Agent 和品类生成数据驱动的提示词片段，拼接到 system prompt 后。
    """
    p = MODEL_PARAMS.get(category, MODEL_PARAMS["lifestyle"])
    w = p["weights"]
    bl = p["baseline"]
    cn = CATEGORY_CN.get(category, category)

    viral = VIRAL_TITLES.get(category, VIRAL_TITLES.get("lifestyle", []))
    comments = REAL_COMMENTS.get(category, REAL_COMMENTS.get("lifestyle", []))

    if agent_type == "content":
        viral_str = " / ".join(f'"{t}"' for t in viral[:3])
        return (
            f"\n\n## 数据研究基准（{cn}品类，基于{bl['sample_size']}条真实数据）\n"
            f"- 标题最优长度：{p['title_length']['min']}-{p['title_length']['max']}字（爆款平均{p['title_length']['viral_avg']}字）\n"
            f"- 正文最优长度：{p['content_length']['min']}-{p['content_length']['max']}字\n"
            f"- 内容质量权重：{w['content_quality']:.1%}\n"
            f"- 基线互动量：平均{bl['avg_engagement']:,}，中位数{bl['median']:,}，爆款线{bl['viral_threshold']:,}\n"
            f"\n**该品类真实爆款标题参考**（请模仿这些标题的语气和句式改写用户标题）：\n{viral_str}\n"
            f"请严格依据以上参数给出量化诊断，优化标题时必须模仿真实爆款的语气。"
        )
    elif agent_type == "visual":
        return (
            f"\n\n## 数据研究基准（{cn}品类）\n"
            f"- 图片最优数量：{p['image_count']['min']}-{p['image_count']['max']}张\n"
            f"- 视觉质量权重：{w['visual_performance']:.1%}\n"
            f"- 视频时长建议：{p['video_duration']['min']}-{p['video_duration']['max']}秒（最优{p['video_duration']['optimal']}秒）\n"
            f"{'（穿搭品类视觉是核心驱动力，视觉权重高达30%）' if category == 'fashion' else ''}\n"
            f"请基于图片数量和视觉质量给出诊断。"
        )
    elif agent_type == "growth":
        best_hours = p.get("best_hours", [12, 18])
        return (
            f"\n\n## 数据研究基准（{cn}品类）\n"
            f"- 标签最优数量：{p['tag_count']['min']}-{p['tag_count']['max']}个（最佳{p['tag_count']['best']}个）\n"
            f"- 标签策略权重：{w['growth_strategy']:.1%}\n"
            f"- 基线：平均互动{bl['avg_engagement']:,}，爆款线{bl['viral_threshold']:,}\n"
            f"- 最佳发布时段：{', '.join(str(h) for h in best_hours[:4])}:00\n"
            f"请基于以上数据给出增长策略。"
        )
    elif agent_type == "bgm":
        heat_desc = ", ".join(
            f"{k}: {v['traffic_weight']}推流({v['description']})"
            for k, v in sorted(BGM_HEAT_LEVELS.items(), key=lambda x: -x[1]["threshold"])
        )
        return (
            f"\n\n## BGM热度研究基准\n"
            f"- BGM热度等级与推流影响：\n{heat_desc}\n"
            f"- {cn}品类BGM热度基线：{p.get('bgm_heat_baseline', 0):,}\n"
            f"- BGM适配度权重：{w.get('bgm_adaptation', 0.15):.1%}\n"
            f"分析维度：\n"
            f"1. BGM热度指数属于哪个等级\n"
            f"2. 内容适配度：音乐风格与内容调性是否匹配\n"
            f"3. 情绪同步：音乐节奏与画面节奏是否匹配\n"
            f"4. 推流预测：基于BGM热度的推流影响评估\n"
            f"5. 替代推荐：同风格但更高热度的BGM推荐\n"
        )
    elif agent_type == "user_sim":
        comments_str = "\n".join(f'  - "{c}"' for c in comments[:3])
        return (
            f"\n\n## 用户画像数据（{cn}品类，基于真实评论分析）\n"
            f"- 用户类型分布：种草型/经验型/调侃型/质疑型/求同款型/凑热闹型\n"
            f"- 互动特点：点赞/评论/收藏/分享行为模式\n"
            f"\n**该品类真实高赞评论参考**（请模仿这些评论的语气和风格）：\n{comments_str}\n"
            f"生成评论时必须像真实抖音用户——用口语、有的很短有的很长、有人抬杠有人种草。禁止AI味。"
        )
    elif agent_type == "judge":
        w_str = "、".join(
            f"{k}({v:.1%})"
            for k, v in sorted(w.items(), key=lambda x: -x[1])
        )
        viral_str = " / ".join(f'"{t}"' for t in viral[:3])
        return (
            f"\n\n## 数据驱动评分标准（{cn}品类，基于{bl['sample_size']}条数据训练）\n"
            f"- 评分权重优先级：{w_str}\n"
            f"- 基线对比：平均互动{bl['avg_engagement']:,}，中位数{bl['median']:,}，爆款线{bl['viral_threshold']:,}\n"
            f"\n**该品类真实爆款标题参考**（改写标题时请模仿这些语气）：\n{viral_str}\n"
            f"- optimized_title 必须像真实抖音爆款——口语化、有情绪、有悬念，禁止学术化或AI味\n"
            f"- optimized_content 必须像真实抖音正文——短段落、有节奏、结尾互动引导，禁止长段落和书面语\n"
            f"- 请严格按权重加权计算总分，并与基线对标。\n"
            f"- BGM优化建议是抖医的核心差异点，请重点关注。"
        )
    return ""
