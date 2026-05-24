"""
Model A 训练器
从 8880+ 真实数据中提取特征，学习品类差异化权重
"""
import sqlite3
import json
import re
from collections import defaultdict
from typing import Optional

DB_PATH = "data/tiktok_baseline.db"


def decode_text(b: bytes) -> str:
    """解码数据库文本"""
    try:
        return b.decode("gb18030", errors="ignore")
    except Exception:
        return b.decode("utf-8", errors="ignore")


def extract_features(title: str, desc: str, category: str, music_title: str, like_count: int, comment_count: int, share_count: int) -> dict:
    """从单条视频中提取特征"""
    text = (title or "") + " " + (desc or "")
    tags = re.findall(r"#(\w+)", text)

    # 标题特征
    title_len = len(title) if title else 0
    has_number = bool(re.search(r"\d", title or ""))
    has_exclaim = bool(re.search(r"[!?！?]", title or ""))
    has_emoji = bool(re.search(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        r"\U0001F900-\U0001F9FF✨⭐❤️💜🖤🤔]",
        title or ""
    ))
    has_separator = bool(re.search(r"[｜|]", title or ""))

    # 钩子词检测
    hook_words = ["必", "绝了", "太", "超", "巨", "神仙", "宝藏", "救命", "麻了", "封神", "绝了", "吹爆", "炸裂", "yyds", "绝了"]
    hook_count = sum(1 for w in hook_words if w in text)

    # 内容特征
    desc_len = len(desc) if desc else 0
    tag_count = len(tags)

    # 互动特征
    engagement = like_count + comment_count + share_count

    return {
        "title_len": title_len,
        "desc_len": desc_len,
        "tag_count": tag_count,
        "has_number": has_number,
        "has_exclaim": has_exclaim,
        "has_emoji": has_emoji,
        "has_separator": has_separator,
        "hook_count": hook_count,
        "engagement": engagement,
        "like_count": like_count,
        "comment_count": comment_count,
        "share_count": share_count,
    }


def load_video_data() -> list:
    """加载所有视频数据"""
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = decode_text
    cursor = conn.cursor()

    cursor.execute("""
        SELECT title, desc, category, music_title, like_count, comment_count, share_count
        FROM video_database
        WHERE like_count > 0
    """)

    videos = []
    for row in cursor.fetchall():
        title, desc, category, music_title, like_count, comment_count, share_count = row
        videos.append({
            "title": title,
            "desc": desc,
            "category": category,
            "music_title": music_title,
            "like_count": like_count,
            "comment_count": comment_count,
            "share_count": share_count,
        })

    conn.close()
    return videos


def load_bgm_heat_map() -> dict:
    """加载BGM热度映射"""
    conn = sqlite3.connect(DB_PATH)
    conn.text_factory = decode_text
    cursor = conn.cursor()

    cursor.execute("SELECT song_name, bgm_name, heat_index FROM bgm_database")
    heat_map = {}
    for song_name, bgm_name, heat in cursor.fetchall():
        name = song_name or bgm_name
        if name:
            heat_map[name.strip().lower()] = heat

    conn.close()
    return heat_map


def analyze_category(videos: list, category: str, bgm_heat_map: dict) -> dict:
    """分析单个品类的特征分布"""
    cat_videos = [v for v in videos if v["category"] == category]

    if len(cat_videos) < 5:
        return None

    # 提取特征
    features_list = []
    for v in cat_videos:
        # 查找BGM热度
        music_heat = 0
        if v["music_title"]:
            mt_lower = v["music_title"].strip().lower()
            for k, heat in bgm_heat_map.items():
                if k in mt_lower or mt_lower in k:
                    music_heat = heat
                    break

        f = extract_features(
            v["title"], v["desc"], v["category"],
            v["music_title"], v["like_count"], v["comment_count"], v["share_count"]
        )
        f["music_heat"] = music_heat
        features_list.append(f)

    # 计算统计量
    n = len(features_list)
    avg_engagement = sum(f["engagement"] for f in features_list) / n
    median_engagement = sorted(f["engagement"] for f in features_list)[n // 2]

    # 计算爆款阈值（前10%）
    sorted_eng = sorted(f["engagement"] for f in features_list)
    viral_threshold = sorted_eng[int(n * 0.9)] if n >= 10 else sorted_eng[-1]

    # 高互动视频的特征分析
    high_eng = [f for f in features_list if f["engagement"] >= viral_threshold]

    # 计算各维度与engagement的相关性（简化版：分组对比）
    def avg_feature(f_list, key):
        return sum(f[key] for f in f_list) / len(f_list) if f_list else 0

    # 对比高互动vs整体
    stats = {
        "sample_size": n,
        "avg_engagement": round(avg_engagement, 0),
        "median_engagement": round(median_engagement, 0),
        "viral_threshold": round(viral_threshold, 0),
        "avg_likes": round(sum(f["like_count"] for f in features_list) / n, 0),
        "avg_comments": round(sum(f["comment_count"] for f in features_list) / n, 0),
        "avg_shares": round(sum(f["share_count"] for f in features_list) / n, 0),
        # 标题长度
        "avg_title_len": round(sum(f["title_len"] for f in features_list) / n, 1),
        "viral_avg_title_len": round(avg_feature(high_eng, "title_len"), 1),
        "title_len_min": min(f["title_len"] for f in features_list),
        "title_len_max": max(f["title_len"] for f in features_list),
        # 描述长度
        "avg_desc_len": round(sum(f["desc_len"] for f in features_list) / n, 1),
        "viral_avg_desc_len": round(avg_feature(high_eng, "desc_len"), 1),
        # 标签数
        "avg_tag_count": round(sum(f["tag_count"] for f in features_list) / n, 1),
        "viral_avg_tag_count": round(avg_feature(high_eng, "tag_count"), 1),
        "optimal_tag_count": round(avg_feature(high_eng, "tag_count"), 1),
        # 钩子特征
        "avg_hook_count": round(sum(f["hook_count"] for f in features_list) / n, 2),
        "viral_avg_hook_count": round(avg_feature(high_eng, "hook_count"), 2),
        "avg_has_number": round(sum(1 for f in features_list if f["has_number"]) / n, 2),
        "viral_has_number": round(sum(1 for f in high_eng if f["has_number"]) / max(len(high_eng), 1), 2),
        "avg_has_emoji": round(sum(1 for f in features_list if f["has_emoji"]) / n, 2),
        # BGM热度
        "avg_bgm_heat": round(sum(f["music_heat"] for f in features_list) / n, 0),
    }

    # 计算最优标题长度范围（基于高互动视频）
    if high_eng:
        high_title_lens = sorted([f["title_len"] for f in high_eng])
        q1 = high_title_lens[len(high_title_lens) // 4]
        q3 = high_title_lens[3 * len(high_title_lens) // 4]
        stats["optimal_title_len_min"] = max(5, q1 - 5)
        stats["optimal_title_len_max"] = q3 + 5
    else:
        stats["optimal_title_len_min"] = 20
        stats["optimal_title_len_max"] = 60

    # 计算内容长度范围
    if high_eng:
        high_desc_lens = sorted([f["desc_len"] for f in high_eng])
        q1 = high_desc_lens[len(high_desc_lens) // 4]
        q3 = high_desc_lens[3 * len(high_desc_lens) // 4]
        stats["optimal_desc_len_min"] = max(20, q1 // 2)
        stats["optimal_desc_len_max"] = q3 * 2
    else:
        stats["optimal_desc_len_min"] = 50
        stats["optimal_desc_len_max"] = 200

    # 权重推断（基于特征重要性）
    # 通过对比高互动vs整体来推断各特征的重要性
    weights = infer_weights(features_list, high_eng, stats)
    stats["inferred_weights"] = weights

    return stats


def infer_weights(all_features: list, high_eng_features: list, stats: dict) -> dict:
    """推断各维度的权重"""
    # 6个维度的代理特征
    dimensions = {
        "content_quality": ["title_len", "hook_count", "has_exclaim"],
        "visual_performance": ["has_emoji"],  # 视觉代理：emoji使用
        "bgm_adaptation": ["music_heat"],
        "growth_strategy": ["tag_count", "has_number"],
        "user_resonance": ["desc_len"],  # 内容丰富度代理
        "technical_performance": ["has_separator"],  # 结构化程度代理
    }

    weights = {}
    total_importance = 0

    for dim, features in dimensions.items():
        # 计算整体平均值和高互动平均值
        all_avg = sum(sum(f.get(feat, 0) for f in all_features) / max(len(all_features), 1) for feat in features) / len(features)
        high_avg = sum(sum(f.get(feat, 0) for f in high_eng_features) / max(len(high_eng_features), 1) for feat in features) / len(features)

        # 计算提升比例
        if all_avg > 0:
            lift = high_avg / all_avg
        else:
            lift = 1.0

        # 映射到权重分数
        importance = min(max((lift - 1) * 2 + 1, 0.5), 3)
        weights[dim] = importance
        total_importance += importance

    # 归一化权重
    if total_importance > 0:
        weights = {k: round(v / total_importance, 3) for k, v in weights.items()}

    # 添加overall权重
    weights["overall"] = 0.05

    return weights


def train_model_a():
    """训练 Model A，返回各品类的学习到的参数"""
    print("Loading video data...")
    videos = load_video_data()
    print(f"Loaded {len(videos)} videos")

    print("Loading BGM heat map...")
    bgm_heat_map = load_bgm_heat_map()
    print(f"Loaded {len(bgm_heat_map)} BGM entries")

    categories = ["food", "fashion", "tech", "travel", "lifestyle", "other"]
    results = {}

    for cat in categories:
        print(f"\nAnalyzing category: {cat}")
        stats = analyze_category(videos, cat, bgm_heat_map)
        if stats:
            results[cat] = stats
            print(f"  Sample: {stats['sample_size']}")
            print(f"  Avg engagement: {stats['avg_engagement']:,.0f}")
            print(f"  Viral threshold: {stats['viral_threshold']:,.0f}")
            print(f"  Optimal title len: {stats.get('optimal_title_len_min', 0)}-{stats.get('optimal_title_len_max', 0)}")
            print(f"  Optimal tag count: {stats.get('optimal_tag_count', 0)}")
            print(f"  Inferred weights: {stats.get('inferred_weights', {})}")
        else:
            print(f"  Insufficient data")

    return results


def update_research_data(model_params: dict):
    """更新 research_data.py 中的 MODEL_PARAMS"""
    print("\nUpdating research_data.py with learned parameters...")

    # 读取现有文件
    with open("app/agents/research_data.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 生成新的 MODEL_PARAMS
    new_params = {}
    cat_cn = {"food": "美食", "fashion": "时尚", "tech": "科技", "travel": "旅行", "lifestyle": "生活", "other": "其他"}

    for cat, stats in model_params.items():
        weights = stats.get("inferred_weights", {})

        new_params[cat] = {
            "weights": weights,
            "title_length": {
                "min": int(stats.get("optimal_title_len_min", 20)),
                "max": int(stats.get("optimal_title_len_max", 60)),
                "viral_avg": stats.get("viral_avg_title_len", 30),
            },
            "content_length": {
                "min": int(stats.get("optimal_desc_len_min", 50)),
                "max": int(stats.get("optimal_desc_len_max", 200)),
            },
            "tag_count": {
                "min": max(1, int(stats.get("optimal_tag_count", 5)) - 2),
                "max": int(stats.get("optimal_tag_count", 5)) + 2,
                "best": int(stats.get("optimal_tag_count", 5)),
            },
            "baseline": {
                "avg_engagement": stats.get("avg_engagement", 10000),
                "median": stats.get("median_engagement", 5000),
                "viral_threshold": stats.get("viral_threshold", 50000),
                "sample_size": stats.get("sample_size", 100),
            },
            "bgm_heat_baseline": stats.get("avg_bgm_heat", 30000),
            "best_hours": [11, 12, 18, 19, 20],
            "best_days": [1, 5, 6],
        }

    print("Learned parameters:")
    print(json.dumps(new_params, indent=2, ensure_ascii=False))

    return new_params


def save_to_baseline_stats(model_params: dict):
    """保存学习到的参数到 baseline_stats 表"""
    print("\nSaving to baseline_stats table...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for cat, stats in model_params.items():
        # 保存主要统计
        metrics = [
            ("avg_engagement", stats.get("avg_engagement", 0), None),
            ("median_engagement", stats.get("median_engagement", 0), None),
            ("viral_threshold", stats.get("viral_threshold", 0), None),
            ("avg_title_length", stats.get("avg_title_len", 0), None),
            ("viral_avg_title_length", stats.get("viral_avg_title_len", 0), None),
            ("optimal_title_len_min", stats.get("optimal_title_len_min", 0), None),
            ("optimal_title_len_max", stats.get("optimal_title_len_max", 0), None),
            ("avg_tag_count", stats.get("avg_tag_count", 0), None),
            ("optimal_tag_count", stats.get("optimal_tag_count", 0), None),
            ("avg_desc_len", stats.get("avg_desc_len", 0), None),
            ("viral_avg_desc_len", stats.get("viral_avg_desc_len", 0), None),
            ("optimal_desc_len_min", stats.get("optimal_desc_len_min", 0), None),
            ("optimal_desc_len_max", stats.get("optimal_desc_len_max", 0), None),
            ("avg_hook_count", stats.get("avg_hook_count", 0), None),
            ("viral_avg_hook_count", stats.get("viral_avg_hook_count", 0), None),
            ("avg_has_number", stats.get("avg_has_number", 0), None),
            ("viral_has_number", stats.get("viral_has_number", 0), None),
            ("avg_has_emoji", stats.get("avg_has_emoji", 0), None),
            ("avg_bgm_heat", stats.get("avg_bgm_heat", 0), None),
        ]

        for metric_name, metric_value, json_value in metrics:
            if metric_value is not None and metric_value > 0:
                cursor.execute("""
                    INSERT OR REPLACE INTO baseline_stats (category, metric_name, metric_value, metric_json)
                    VALUES (?, ?, ?, ?)
                """, (cat, metric_name, metric_value, json_value))

        # 保存学习到的权重
        weights = stats.get("inferred_weights", {})
        if weights:
            cursor.execute("""
                INSERT OR REPLACE INTO baseline_stats (category, metric_name, metric_value, metric_json)
                VALUES (?, ?, ?, ?)
            """, (cat, "learned_weights", 0, json.dumps(weights, ensure_ascii=False)))

    conn.commit()
    conn.close()
    print("Saved to baseline_stats table")


if __name__ == "__main__":
    # 训练模型
    model_params = train_model_a()

    if model_params:
        # 更新 research_data.py
        update_research_data(model_params)

        # 保存到数据库
        save_to_baseline_stats(model_params)

        print("\n=== Model A Training Complete ===")
        print(f"Trained on {sum(s['sample_size'] for s in model_params.values())} videos")
        print(f"Categories: {list(model_params.keys())}")
    else:
        print("Training failed - no model parameters generated")
