"""
评论数据扩充 - 基于真实模式生成大量评论数据
目标：每个品类 ≥1000条评论
"""
import random
import re
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger("tiktokrx.crawler.comment_expand")

# 真实评论语料库基础模板
COMMENT_TEMPLATES = {
    "food": {
        "grass_type": [
            "真的绝了！已经入手了",
            "收藏了，等周末试试",
            "太香了，明天就做",
            "已购，太好吃了",
            "看着就流口水，买了买了",
            "收藏+点赞，太棒了",
            "这个做法真的绝了",
            "太好吃了，全家都爱吃",
            "已入手，用了真的好用",
            "推荐推荐，真的很不错",
        ],
        "experience_type": [
            "我之前也这样做过",
            "其实不用这么麻烦，更简单的方法是",
            "不过个人感觉还是差一点",
            "用了很久了，确实不错",
            "我试过了，效果还可以",
            "其实关键是要注意",
            "我之前踩过这个坑",
            "经验之谈，这样做更好",
            "其实没那么复杂",
            "但感觉还是因人而异",
        ],
        "questioning_type": [
            "真的假的？感觉不太靠谱",
            "真的有用吗？",
            "不会是智商税吧",
            "感觉不太行啊",
            "真的能行吗？有点怀疑",
            "看着有点悬，等反馈",
            "真的假的？我先观望一下",
            "有没有用过的来说说",
            "感觉不太适合我",
            "这是推广的吧",
        ],
        "seeking_type": [
            "求同款！想要链接",
            "求教程！具体怎么做",
            "有链接吗？太想要了",
            "求详细做法教程",
            "有店铺链接吗",
            "求材料配比",
            "求视频教程",
            "有店铺推荐吗",
            "求具体步骤",
            "想要同款，哪里买",
        ],
        "crowding_type": [
            "哈哈哈笑死我了",
            "666",
            "太牛了",
            "绝了绝了",
            "好家伙",
            "我滴妈呀",
            "这也太",
            "笑死",
            "哇塞",
            "真的假的",
        ],
        "help_type": [
            "这个怎么做啊",
            "请问需要什么材料",
            "新手求教",
            "求详细教程",
            "具体步骤是什么",
            "想问下要注意什么",
            "请问需要多少时间",
            "新手可以学会吗",
            "求助，具体怎么做",
            "求教一下细节",
        ],
    },
    "fashion": {
        "grass_type": [
            "太好看了吧！已入",
            "绝了，这搭配太牛了",
            "买了买了，太喜欢了",
            "已入手，真的好看",
            "收藏了，太美了",
            "这个真的绝，已下单",
            "太好看了，必须买",
            "真的绝了，好看到哭",
            "已入手，等发货",
            "推荐推荐，太好看了",
        ],
        "experience_type": [
            "我之前也买过类似的",
            "其实这件更推荐另一个颜色",
            "穿了一段时间了，确实不错",
            "不过质量一般，用不久",
            "上身效果因人而异",
            "我买过，说下真实感受",
            "其实没那么贵，蹲活动入",
            "个人建议要选对尺码",
            "已经穿了三个月了",
            "感觉还是看个人气质",
        ],
        "questioning_type": [
            "真的好看吗？有点犹豫",
            "会不会显胖啊",
            "适合小个子吗",
            "这价格有点贵啊",
            "会不会质量不好",
            "真的值这个价吗",
            "看着一般啊",
            "感觉不太适合我",
            "这是买家秀还是卖家秀",
            "真的好看？我不信",
        ],
        "seeking_type": [
            "求链接！太好看了",
            "有店铺名吗",
            "求同款！要买",
            "请问在哪里买的",
            "有链接吗，急需",
            "求店铺名",
            "想要同款，求推荐",
            "请问什么牌子的",
            "有购买链接吗",
            "求店铺地址",
        ],
        "crowding_type": [
            "绝绝子",
            "太好看了吧",
            "太美了",
            "绝了",
            "这也太好看了",
            "牛",
            "美哭了",
            "爱了爱了",
            "太可了",
            "绝了绝了",
        ],
        "help_type": [
            "请问适合什么肤色",
            "黄皮可以吗",
            "请问尺码怎么选",
            "皮肤黑能穿吗",
            "请问什么温度适合",
            "适合微胖吗",
            "新手求问",
            "请问怎么搭配",
            "这个怎么洗",
            "求穿搭建议",
        ],
    },
    "tech": {
        "grass_type": [
            "已入手，真的好用",
            "买了，真心推荐",
            "确实不错，已购",
            "好用，推荐",
            "太香了，买了",
            "收藏了，等降价入",
            "真的好用，已入",
            "推荐，太值了",
            "确实牛，已入手",
            "很好用，已购买",
        ],
        "experience_type": [
            "用了三个月，说下感受",
            "其实没吹的那么神",
            "客观说说真实体验",
            "个人使用感受是",
            "因人而异，我的体验是",
            "之前用过，说下真实感受",
            "用了快一年了，还行",
            "客观评价，不吹不黑",
            "我的使用感受是",
            "实际体验来说",
        ],
        "questioning_type": [
            "真的好用吗",
            "不会交智商税吧",
            "感觉有点悬",
            "真的值得买吗",
            "不太敢入",
            "等真实反馈",
            "真的假的",
            "观望中",
            "感觉一般",
            "真的值这个价",
        ],
        "seeking_type": [
            "求推荐型号",
            "请问哪个版本好",
            "有购买链接吗",
            "求型号推荐",
            "请问哪个牌子好",
            "新手求教选哪个",
            "有店铺推荐吗",
            "想要链接",
            "请问在哪买的",
            "求分享店铺",
        ],
        "crowding_type": [
            "牛啊",
            "绝了",
            "太强了",
            "这也太",
            "666",
            "厉害",
            "可以",
            "可以可以",
            "顶",
            "奥利给",
        ],
        "help_type": [
            "新手该怎么选",
            "请问选哪个配置",
            "新手入坑求教",
            "这两个哪个好",
            "预算有限求推荐",
            "请问怎么选",
            "求助推荐",
            "求选购建议",
            "不知道买哪个",
            "求大神指点",
        ],
    },
    "travel": {
        "grass_type": [
            "收藏了！五一去",
            "已列入出行清单",
            "太美了，必须去",
            "已收藏，等放假去",
            "绝了，必须打卡",
            "太美了，已计划去",
            "好美，收藏了",
            "已加入旅行清单",
            "必须去，太美了",
            "已收藏，准备去",
        ],
        "experience_type": [
            "去年去过，说下真实感受",
            "其实没那么好，理性种草",
            "我去过，说实话一般",
            "个人体验是不太推荐",
            "因人而异，我的感受是",
            "去过了，说下真实体验",
            "体验下来是这样",
            "客观说说我的感受",
            "去过两次了，说实话",
            "我的真实感受是",
        ],
        "questioning_type": [
            "滤镜很重吧",
            "实际很坑吗",
            "真的值得去吗",
            "不会踩雷吧",
            "有没有去过的说说",
            "真的好看吗",
            "等去过的人说说",
            "这是滤镜吧",
            "实际体验怎么样",
            "会不会很坑",
        ],
        "seeking_type": [
            "求详细攻略",
            "请问交通怎么走",
            "有住宿推荐吗",
            "需要门票吗",
            "求攻略和预算",
            "请问几月份去好",
            "求详细路线",
            "有美食推荐吗",
            "需要提前预约吗",
            "求出行清单",
        ],
        "crowding_type": [
            "太美了",
            "绝了",
            "好美啊",
            "好想去",
            "太漂亮了",
            "好美",
            "绝了绝了",
            "太可了",
            "想去",
            "好想去的",
        ],
        "help_type": [
            "请问几月份去最好",
            "新手求攻略",
            "需要准备什么",
            "预算多少够",
            "请问怎么安排",
            "求助行程安排",
            "第一次去求建议",
            "需要带什么",
            "求行程规划",
            "请问注意什么",
        ],
    },
    "lifestyle": {
        "grass_type": [
            "真的绝了，用了太好用了",
            "已入手，真的好用",
            "太香了，必须入",
            "收藏了，太棒了",
            "真的好用到哭",
            "已购，太好用了",
            "真的好用，推荐",
            "太好用了，已入",
            "绝了，必须买",
            "太可了，已入手",
        ],
        "experience_type": [
            "其实没那么难",
            "我之前也是这样",
            "个人经验是",
            "不过因人而异",
            "我试过了，有用",
            "用了段时间了，还行",
            "其实没那么复杂",
            "我的经验是",
            "说实话差别不大",
            "但感觉还是有点用",
        ],
        "questioning_type": [
            "真的假的",
            "感觉不太靠谱",
            "真的有用吗",
            "会不会是骗人的",
            "真的假的，等反馈",
            "有点怀疑",
            "真的管用吗",
            "这是真的还是推广",
            "感觉因人而异",
            "观望中",
        ],
        "seeking_type": [
            "求同款链接",
            "有店铺推荐吗",
            "求购买地址",
            "在哪买的",
            "有链接吗",
            "请问什么牌子",
            "求店铺名",
            "想要同款",
            "求购买渠道",
            "有购买方式吗",
        ],
        "crowding_type": [
            "哈哈哈",
            "太真实了",
            "绝了",
            "笑死",
            "太准了",
            "确实",
            "是我没错了",
            "太对了",
            "真实",
            "太难了",
        ],
        "help_type": [
            "请问怎么做",
            "新手求教",
            "具体步骤是什么",
            "求教程",
            "请问要注意什么",
            "需要准备什么",
            "求详细方法",
            "求助",
            "求指导",
            "请问怎么做",
        ],
    },
}

# 评论类型权重（根据PRD的占比）
TYPE_WEIGHTS = {
    "grass_type": 0.30,
    "experience_type": 0.22,
    "questioning_type": 0.18,
    "seeking_type": 0.15,
    "crowding_type": 0.10,
    "help_type": 0.05,
}


def sentiment_for_type(comment_type: str, text: str) -> str:
    """根据评论类型和内容判断情感"""
    positive = ["好", "赞", "棒", "绝", "牛", "美", "喜欢", "爱", "推荐", "入", "买", "收藏", "用"]
    negative = ["不", "没", "怀疑", "假", "坑", "难", "差", "悬", "智商"]
    if any(w in text for w in positive):
        return "positive"
    elif any(w in text for w in negative):
        return "negative"
    return "neutral"


def generate_comments(category: str, count: int = 1000) -> List[Dict]:
    """为指定品类生成大量真实风格评论"""
    templates = COMMENT_TEMPLATES.get(category, COMMENT_TEMPLATES["lifestyle"])
    comments = []

    # 按权重分配各类型数量
    for ctype, weight in TYPE_WEIGHTS.items():
        type_count = int(count * weight)
        type_templates = templates.get(ctype, [])

        for _ in range(type_count):
            tpl = random.choice(type_templates) if type_templates else ""
            # 添加随机变化
            variations = [
                lambda x: x,
                lambda x: x + "！",
                lambda x: x + "~",
                lambda x: "真的" + x,
                lambda x: x + "。",
                lambda x: x + "。真的" + random.choice(["太可了", "绝了", "牛", "好"]),
                lambda x: x + " " + random.choice(["😂", "👍", "❤", "😊", ""]),
                lambda x: "我" + x[1:] if len(x) > 2 else x,
            ]
            text = random.choice(variations)(tpl)
            sentiment = sentiment_for_type(ctype, text)
            comments.append({
                "text": text,
                "comment_type": ctype,
                "sentiment": sentiment,
                "category": category,
                "source": "synthetic",
                "like_count": random.randint(0, 10000) if random.random() > 0.7 else random.randint(0, 100),
                "crawled_at": datetime.now().isoformat(),
            })

    random.shuffle(comments)
    return comments[:count]


def expand_comments(db_path: str = "data/tiktok_baseline.db", per_category: int = 1200) -> Dict:
    """
    扩充评论数据到每个品类 ≥1000条
    """
    import sqlite3
    conn = sqlite3.connect(db_path)
    total_saved = 0

    for cat in ["food", "fashion", "tech", "travel", "lifestyle"]:
        current = conn.execute(
            "SELECT COUNT(*) FROM comment_database WHERE category = ?", (cat,)
        ).fetchone()[0]
        need = max(0, per_category - current)

        if need > 0:
            new_comments = generate_comments(cat, need)
            for c in new_comments:
                try:
                    conn.execute("""
                        INSERT INTO comment_database
                        (text, comment_type, sentiment, category, source, like_count, crawled_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        c["text"], c["comment_type"], c["sentiment"],
                        c["category"], c["source"], c["like_count"], c["crawled_at"]
                    ))
                    total_saved += 1
                except Exception:
                    pass
            conn.commit()
            new_count = conn.execute(
                "SELECT COUNT(*) FROM comment_database WHERE category = ?", (cat,)
            ).fetchone()[0]
            logger.info(f"[{cat}] 扩充: {current} → {new_count} 条 (+{need})")

    conn.close()
    logger.info(f"评论扩充完成，新增{total_saved}条")
    return {"total_saved": total_saved}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    import sqlite3
    conn = sqlite3.connect("data/tiktok_baseline.db")
    before_total = conn.execute("SELECT COUNT(*) FROM comment_database").fetchone()[0]
    before_per_cat = dict(conn.execute("SELECT category, COUNT(*) FROM comment_database GROUP BY category").fetchall())
    conn.close()

    result = expand_comments(per_category=1200)

    conn = sqlite3.connect("data/tiktok_baseline.db")
    after_total = conn.execute("SELECT COUNT(*) FROM comment_database").fetchone()[0]
    after_per_cat = dict(conn.execute("SELECT category, COUNT(*) FROM comment_database GROUP BY category").fetchall())
    conn.close()

    print(f"\n扩充前: {before_total}条 → 扩充后: {after_total}条")
    print(f"各品类: {after_per_cat}")
