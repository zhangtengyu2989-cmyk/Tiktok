"""
歌曲名 → 抖音BGM 映射表
基于已知热门抖音BGM建立映射
"""
import re
from typing import Optional

# 已知抖音热门BGM映射表（歌曲名/艺术家 → 抖音BGM信息）
KNOWN_DOUBIN_BGMS = {
    # 抖音神曲类
    ("适配", "小潘潘"): {"bgm_name": "适配", "style": "欢快", "categories": ["生活", "剧情"]},
    ("穷叉叉", "关涛"): {"bgm_name": "穷叉叉", "style": "动感", "categories": ["搞笑", "剧情"]},
    ("恐龙化石", "小潘潘"): {"bgm_name": "恐龙化石", "style": "欢快", "categories": ["萌宠", "生活"]},
    ("是想你的声音啊", "三无MarBlue"): {"bgm_name": "是想你的声音啊", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("木偶戏", "G.E.M.邓紫棋"): {"bgm_name": "木偶戏", "style": "专业", "categories": ["音乐", "翻唱"]},
    ("腰痛", "小潘潘"): {"bgm_name": "腰痛", "style": "欢快", "categories": ["搞笑", "生活"]},
    ("白月光与朱砂痣", "大籽"): {"bgm_name": "白月光与朱砂痣", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("执迷不悟", "小乐哥"): {"bgm_name": "执迷不悟", "style": "动感", "categories": ["音乐", "翻唱"]},
    ("时光洪流", "程响"): {"bgm_name": "时光洪流", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("探窗", "解忧邵栈"): {"bgm_name": "探窗", "style": "动感", "categories": ["音乐", "古风"]},
    ("海市蜃楼", "J Magic"): {"bgm_name": "海市蜃楼", "style": "动感", "categories": ["音乐", "舞蹈"]},
    ("踏山河", "是七叔呢"): {"bgm_name": "踏山河", "style": "大气", "categories": ["音乐", "古风"]},
    ("醒不来的梦", "回音哥"): {"bgm_name": "醒不来的梦", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("千千万万", "深海鱼子酱"): {"bgm_name": "千千万万", "style": "欢快", "categories": ["生活", "剧情"]},
    ("星河不可及", "等什么君"): {"bgm_name": "星河不可及", "style": "大气", "categories": ["音乐", "古风"]},
    ("沦陷", "王靖雯"): {"bgm_name": "沦陷", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("可可托海的牧羊人", "王琪"): {"bgm_name": "可可托海的牧羊人", "style": "大气", "categories": ["音乐", "民谣"]},
    ("跟我回家", "G.E.M.邓紫棋"): {"bgm_name": "跟我回家", "style": "动感", "categories": ["音乐", "剧情"]},
    ("简单爱", "周杰伦"): {"bgm_name": "简单爱", "style": "欢快", "categories": ["音乐", "翻唱", "生活"]},
    ("稻香", "周杰伦"): {"bgm_name": "稻香", "style": "欢快", "categories": ["音乐", "治愈", "生活"]},
    ("Mojito", "周杰伦"): {"bgm_name": "Mojito", "style": "动感", "categories": ["音乐", "舞蹈", "生活"]},
    ("错位时空", "艾辰"): {"bgm_name": "错位时空", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("厚米", "南拳妈妈"): {"bgm_name": "厚米", "style": "欢快", "categories": ["搞笑", "生活"]},
    ("热爱105度的你", "G.E.M.邓紫棋"): {"bgm_name": "热爱105度的你", "style": "欢快", "categories": ["音乐", "舞蹈"]},
    ("在年少的光里走散", "赵露思"): {"bgm_name": "在年少的光里走散", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("蜜雪冰城", ""): {"bgm_name": "蜜雪冰城主题曲", "style": "欢快", "categories": ["搞笑", "生活", "美食"]},
    ("达拉崩吧", "周深"): {"bgm_name": "达拉崩吧", "style": "动感", "categories": ["音乐", "翻唱"]},
    ("芒种", "音阙诗听/赵方婧"): {"bgm_name": "芒种", "style": "大气", "categories": ["音乐", "古风"]},
    ("下山", "要不要买菜"): {"bgm_name": "下山", "style": "动感", "categories": ["音乐", "古风", "舞蹈"]},
    ("膨胀", "R1SE"): {"bgm_name": "膨胀", "style": "动感", "categories": ["音乐", "舞蹈"]},
    ("野狼disco", "宝石Gem"): {"bgm_name": "野狼disco", "style": "动感", "categories": ["音乐", "舞蹈", "搞笑"]},
    ("处处吻", "杨千婯"): {"bgm_name": "处处吻", "style": "动感", "categories": ["音乐", "舞蹈"]},
    ("Last Dance", "伍佰"): {"bgm_name": "Last Dance", "style": "舒缓", "categories": ["情感", "剧情", "怀旧"]},
    ("口水歌", "小潘潘"): {"bgm_name": "小潘潘-口水歌", "style": "欢快", "categories": ["搞笑", "生活"]},
    ("卡点音乐", ""): {"bgm_name": "热门卡点音乐", "style": "动感", "categories": ["舞蹈", "剪辑"]},
    ("变脸", ""): {"bgm_name": "川剧变脸BGM", "style": "大气", "categories": ["文化", "剧情"]},
    ("cinema", ""): {"bgm_name": "Cinema", "style": "动感", "categories": ["舞蹈", "剪辑"]},
    ("反方向的钟", "周杰伦"): {"bgm_name": "反方向的钟", "style": "舒缓", "categories": ["音乐", "怀旧"]},
    ("Commune", ""): {"bgm_name": "Commune", "style": "电子", "categories": ["舞蹈", "科技"]},
    ("Freak Out", ""): {"bgm_name": "Freak Out", "style": "动感", "categories": ["舞蹈", "运动"]},
    ("星球", "盛宇/艾热"): {"bgm_name": "星球", "style": "舒缓", "categories": ["情感", "说唱"]},
    ("commune", ""): {"bgm_name": "Commune", "style": "电子", "categories": ["舞蹈", "夜店"]},

    # 2024-2025抖音新晋热门BGM
    ("爱如火", "要不要买菜"): {"bgm_name": "爱如火", "style": "动感", "categories": ["音乐", "舞蹈", "搞笑"]},
    ("精武门", "陈小春"): {"bgm_name": "精武门", "style": "动感", "categories": ["动作", "剧情", "怀旧"]},
    ("钵钵鸡", "一纸荒年"): {"bgm_name": "钵钵鸡", "style": "欢快", "categories": ["美食", "搞笑", "生活"]},
    ("我怕等不到你", "蒋小欠"): {"bgm_name": "我怕等不到你", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("就让这大雨全都落下", "容祖儿"): {"bgm_name": "就让这大雨全都落下", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("雪", "jj哥哥"): {"bgm_name": "雪", "style": "舒缓", "categories": ["情感", "风景"]},
    (" Comptine d'un autre été", "Yann Tiersen"): {"bgm_name": "雪の降る街", "style": "舒缓", "categories": ["治愈", "风景", "纯音乐"]},
    ("communion", ""): {"bgm_name": "Communion", "style": "电子", "categories": ["舞蹈", "剪辑"]},
    ("经济舱", "Keyso"): {"bgm_name": "经济舱", "style": "说唱", "categories": ["音乐", "说唱"]},
    ("泪桥", "ice Paper"): {"bgm_name": "泪桥", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("若把你", "Kirsty"): {"bgm_name": "若把你", "style": "舒缓", "categories": ["情感", "剧情", "古风"]},
    ("彩虹的微笑", "王心凌"): {"bgm_name": "彩虹的微笑", "style": "欢快", "categories": ["音乐", "翻唱", "治愈"]},
    ("qs", ""): {"bgm_name": "Qs", "style": "动感", "categories": ["舞蹈", "剪辑"]},
    ("国产整车", "小西米"): {"bgm_name": "国产整车", "style": "欢快", "categories": ["搞笑", "生活"]},
    ("我想要", "Eggplant"): {"bgm_name": "我想要", "style": "欢快", "categories": ["生活", "情感"]},
    ("cutoff", ""): {"bgm_name": "Cut Off", "style": "动感", "categories": ["舞蹈", "剪辑"]},
    ("厂商", "小西米"): {"bgm_name": "厂商", "style": "欢快", "categories": ["搞笑", "生活"]},
    ("鉴宝", ""): {"bgm_name": "鉴宝BGM", "style": "紧张", "categories": ["剧情", "悬疑"]},
    ("麻辣蘑菇", "小西米"): {"bgm_name": "麻辣蘑菇", "style": "欢快", "categories": ["美食", "搞笑"]},
    ("养乐多", "Blow Fever"): {"bgm_name": "养乐多", "style": "欢快", "categories": ["生活", "舞蹈"]},

    # 经典老歌BGM
    ("童话", "光良"): {"bgm_name": "童话", "style": "舒缓", "categories": ["情感", "怀旧", "剧情"]},
    ("江南", "林俊杰"): {"bgm_name": "江南", "style": "舒缓", "categories": ["情感", "怀旧", "剧情"]},
    ("晴天", "周杰伦"): {"bgm_name": "晴天", "style": "舒缓", "categories": ["情感", "怀旧", "剧情"]},
    ("七里香", "周杰伦"): {"bgm_name": "七里香", "style": "舒缓", "categories": ["情感", "怀旧", "剧情"]},
    ("夜曲", "周杰伦"): {"bgm_name": "夜曲", "style": "舒缓", "categories": ["情感", "怀旧", "剧情"]},
    ("稻香", "周杰伦"): {"bgm_name": "稻香", "style": "欢快", "categories": ["治愈", "生活", "怀旧"]},
    ("将军", "周杰伦"): {"bgm_name": "将军", "style": "动感", "categories": ["游戏", "动作"]},
    ("龙拳", "周杰伦"): {"bgm_name": "龙拳", "style": "动感", "categories": ["动作", "武术"]},
    ("双截棍", "周杰伦"): {"bgm_name": "双截棍", "style": "动感", "categories": ["动作", "武术"]},
    ("以父之名", "周杰伦"): {"bgm_name": "以父之名", "style": "大气", "categories": ["剧情", "电影"]},
    ("夜的第七章", "周杰伦"): {"bgm_name": "夜的第七章", "style": "悬疑", "categories": ["悬疑", "剧情"]},
    ("夜城", ""): {"bgm_name": "夜城", "style": "动感", "categories": ["舞蹈", "夜店"]},
    ("伤心的人别听慢歌", "五月天"): {"bgm_name": "伤心的人别听慢歌", "style": "动感", "categories": ["音乐", "情感"]},
    ("离开地球表面", "五月天"): {"bgm_name": "离开地球表面", "style": "动感", "categories": ["音乐", "舞蹈"]},
    ("派对动物", "五月天"): {"bgm_name": "派对动物", "style": "动感", "categories": ["音乐", "舞蹈"]},
    ("倔强", "五月天"): {"bgm_name": "倔强", "style": "热血", "categories": ["音乐", "励志"]},
    ("温柔", "五月天"): {"bgm_name": "温柔", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("突然好想你", "五月天"): {"bgm_name": "突然好想你", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("恋爱ing", "五月天"): {"bgm_name": "恋爱ing", "style": "欢快", "categories": ["音乐", "舞蹈"]},
    ("洋葱", "杨宗纬"): {"bgm_name": "洋葱", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("一次就好", "杨宗纬"): {"bgm_name": "一次就好", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("矜持", "王菲"): {"bgm_name": "矜持", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("红豆", "王菲"): {"bgm_name": "红豆", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("匆匆那年", "王菲"): {"bgm_name": "匆匆那年", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("传奇", "王菲"): {"bgm_name": "传奇", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("约定", "王菲"): {"bgm_name": "约定", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("岁月神偷", "金玟岐"): {"bgm_name": "岁月神偷", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("踮起脚尖爱", "洪辰"): {"bgm_name": "踮起脚尖爱", "style": "欢快", "categories": ["音乐", "舞蹈"]},
    ("小幸运", "田馥甄"): {"bgm_name": "小幸运", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("体面", "于文文"): {"bgm_name": "体面", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("说散就散", "袁娅维"): {"bgm_name": "说散就散", "style": "动感", "categories": ["情感", "剧情"]},
    ("起风了", "买辣椒也用券"): {"bgm_name": "起风了", "style": "舒缓", "categories": ["情感", "治愈", "剧情"]},
    ("年少有为", "李荣浩"): {"bgm_name": "年少有为", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("模特", "李荣浩"): {"bgm_name": "模特", "style": "动感", "categories": ["音乐", "舞蹈"]},
    ("李白", "李荣浩"): {"bgm_name": "李白", "style": "欢快", "categories": ["音乐", "生活"]},
    ("耳朵", "李荣浩"): {"bgm_name": "耳朵", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("戒烟", "李荣浩"): {"bgm_name": "戒烟", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("年少有为", "李荣浩"): {"bgm_name": "年少有为", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("乌梅子酱", "李荣浩"): {"bgm_name": "乌梅子酱", "style": "欢快", "categories": ["音乐", "舞蹈", "生活"]},
    ("月亮惹的祸", "张宇"): {"bgm_name": "月亮惹的祸", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("雨一直下", "张宇"): {"bgm_name": "雨一直下", "style": "动感", "categories": ["情感", "剧情"]},
    ("心太软", "任家萱"): {"bgm_name": "心太软", "style": "舒缓", "categories": ["情感", "剧情"]},

    # 国际热门BGM
    ("Shape of You", "Ed Sheeran"): {"bgm_name": "Shape of You", "style": "动感", "categories": ["音乐", "舞蹈", "健身"]},
    ("Despacito", "Luis Fonsi"): {"bgm_name": "Despacito", "style": "动感", "categories": ["音乐", "舞蹈", "拉丁"]},
    ("Faded", "Alan Walker"): {"bgm_name": "Faded", "style": "电子", "categories": ["音乐", "电音", "励志"]},
    ("Alone", "Marshmello"): {"bgm_name": "Alone", "style": "电子", "categories": ["音乐", "电音"]},
    ("The Spectre", "Alan Walker"): {"bgm_name": "The Spectre", "style": "电子", "categories": ["音乐", "电音"]},
    ("Something Just Like This", "Chainsmokers"): {"bgm_name": "Something Just Like This", "style": "电子", "categories": ["音乐", "电音"]},
    (" Closer", "Chainsmokers"): {"bgm_name": "Closer", "style": "电子", "categories": ["音乐", "电音"]},
    ("Dancing With Your Ghost", "Ariana Grande"): {"bgm_name": "Dancing With Your Ghost", "style": "舒缓", "categories": ["情感", "治愈"]},
    ("Let Me Down Slowly", "Alec Benjamin"): {"bgm_name": "Let Me Down Slowly", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("Falling", "Trevor Daniel"): {"bgm_name": "Falling", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("Heat Waves", "Glass Animals"): {"bgm_name": "Heat Waves", "style": "舒缓", "categories": ["情感", "治愈"]},
    ("Stay", "The Kid LAROI"): {"bgm_name": "Stay", "style": "动感", "categories": ["音乐", "电音"]},
    ("Bad Guy", "Billie Eilish"): {"bgm_name": "Bad Guy", "style": "动感", "categories": ["音乐", "舞蹈"]},
    ("Havana", "Camila Cabello"): {"bgm_name": "Havana", "style": "欢快", "categories": ["音乐", "拉丁"]},
    ("Perfect", "Ed Sheeran"): {"bgm_name": "Perfect", "style": "舒缓", "categories": ["情感", "婚礼", "剧情"]},
    ("Thinking Out Loud", "Ed Sheeran"): {"bgm_name": "Thinking Out Loud", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("Photograph", "Ed Sheeran"): {"bgm_name": "Photograph", "style": "舒缓", "categories": ["情感", "剧情", "治愈"]},
    ("Say Something", "A Great Big World"): {"bgm_name": "Say Something", "style": "舒缓", "categories": ["情感", "剧情"]},
    ("Love Story", "Taylor Swift"): {"bgm_name": "Love Story", "style": "欢快", "categories": ["音乐", "剧情", "怀旧"]},
    ("Shake It Off", "Taylor Swift"): {"bgm_name": "Shake It Off", "style": "欢快", "categories": ["音乐", "舞蹈"]},
    ("Blank Space", "Taylor Swift"): {"bgm_name": "Blank Space", "style": "欢快", "categories": ["音乐", "舞蹈"]},
    ("Dynamite", "BTS"): {"bgm_name": "Dynamite", "style": "欢快", "categories": ["音乐", "舞蹈", "韩流"]},
    ("Butter", "BTS"): {"bgm_name": "Butter", "style": "欢快", "categories": ["音乐", "舞蹈", "韩流"]},
    ("Permission to Dance", "BTS"): {"bgm_name": "Permission to Dance", "style": "欢快", "categories": ["音乐", "舞蹈", "韩流"]},
    ("Kill This Love", "BLACKPINK"): {"bgm_name": "Kill This Love", "style": "动感", "categories": ["音乐", "舞蹈", "韩流"]},
    ("DDU-DU DDU-DU", "BLACKPINK"): {"bgm_name": "DDU-DU DDU-DU", "style": "动感", "categories": ["音乐", "舞蹈", "韩流"]},
    ("How You Like That", "BLACKPINK"): {"bgm_name": "How You Like That", "style": "动感", "categories": ["音乐", "舞蹈", "韩流"]},

    # 纯音乐BGM
    ("Sky", ""): {"bgm_name": "Sky", "style": "舒缓", "categories": ["治愈", "风景", "纯音乐"]},
    ("Flower", ""): {"bgm_name": "Flower", "style": "舒缓", "categories": ["治愈", "风景", "纯音乐"]},
    ("Rain", ""): {"bgm_name": "Rain", "style": "舒缓", "categories": ["治愈", "风景", "纯音乐"]},
    ("Sunset", ""): {"bgm_name": "Sunset", "style": "舒缓", "categories": ["治愈", "风景", "纯音乐"]},
    ("Morning", ""): {"bgm_name": "Morning", "style": "欢快", "categories": ["治愈", "生活", "纯音乐"]},
    ("Night", ""): {"bgm_name": "Night", "style": "舒缓", "categories": ["治愈", "夜景", "纯音乐"]},
    ("Cafe", ""): {"bgm_name": "Cafe", "style": "欢快", "categories": ["生活", "美食", "纯音乐"]},
    ("Travel", ""): {"bgm_name": "Travel", "style": "欢快", "categories": ["旅行", "风景", "纯音乐"]},
    (" Workout", ""): {"bgm_name": "Workout", "style": "动感", "categories": ["健身", "运动", "纯音乐"]},
    ("Epic", ""): {"bgm_name": "Epic", "style": "大气", "categories": ["剧情", "电影", "纯音乐"]},
    ("Cinematic", ""): {"bgm_name": "Cinematic", "style": "大气", "categories": ["剧情", "电影", "纯音乐"]},
    ("Adventure", ""): {"bgm_name": "Adventure", "style": "大气", "categories": ["剧情", "冒险", "纯音乐"]},
    ("Comedy", ""): {"bgm_name": "Comedy", "style": "欢快", "categories": ["搞笑", "生活", "纯音乐"]},
    ("Romance", ""): {"bgm_name": "Romance", "style": "舒缓", "categories": ["情感", "剧情", "纯音乐"]},
    ("Tension", ""): {"bgm_name": "Tension", "style": "紧张", "categories": ["悬疑", "剧情", "纯音乐"]},
    ("Horror", ""): {"bgm_name": "Horror", "style": "紧张", "categories": ["恐怖", "悬疑", "纯音乐"]},

    # 抖音平台特效BGM
    ("扫描", ""): {"bgm_name": "扫描特效音", "style": "科技", "categories": ["特效", "剪辑", "科技"]},
    ("打字机", ""): {"bgm_name": "打字机音效", "style": "科技", "categories": ["特效", "剪辑"]},
    ("转场", ""): {"bgm_name": "转场音效", "style": "动感", "categories": ["剪辑", "转场"]},
    ("揭晓", ""): {"bgm_name": "揭晓音效", "style": "紧张", "categories": ["特效", "剧情"]},
    ("失败", ""): {"bgm_name": "失败音效", "style": "搞笑", "categories": ["特效", "搞笑"]},
    ("成功", ""): {"bgm_name": "成功音效", "style": "欢快", "categories": ["特效", "剧情"]},
    ("心跳", ""): {"bgm_name": "心跳音效", "style": "紧张", "categories": ["特效", "情感"]},
    ("倒计时", ""): {"bgm_name": "倒计时音效", "style": "紧张", "categories": ["特效", "剧情"]},
}


def fuzzy_match(song_name: str, artist: str = "") -> Optional[dict]:
    """模糊匹配歌曲名→抖音BGM"""
    if not song_name:
        return None

    song_clean = re.sub(r"[^一-龥a-zA-Z0-9]", "", song_name.lower())
    artist_clean = re.sub(r"[^一-龥a-zA-Z0-9]", "", (artist or "").lower())

    # 精确匹配
    for (s, a), info in KNOWN_DOUBIN_BGMS.items():
        s_clean = re.sub(r"[^一-龥a-zA-Z0-9]", "", s.lower())
        a_clean = re.sub(r"[^一-龥a-zA-Z0-9]", "", (a or "").lower())
        if song_clean == s_clean:
            if not a_clean or a_clean == artist_clean or a_clean in artist_clean or artist_clean in a_clean:
                return dict(info, matched_song=s, matched_artist=a)

    # 模糊匹配：歌名包含
    for (s, a), info in KNOWN_DOUBIN_BGMS.items():
        s_clean = re.sub(r"[^一-龥a-zA-Z0-9]", "", s.lower())
        if s_clean and s_clean in song_clean:
            return dict(info, matched_song=s, matched_artist=a)

    return None


def estimate_heat_by_name(song_name: str) -> int:
    """根据歌曲名估算热度（万）"""
    hot_keywords = ["周杰伦", "邓紫棋", "陈奕迅", "林俊杰", "Taylor", "BTS", "抖音", "网红"]
    viral_keywords = ["爆火", "神曲", "洗脑", "刷屏"]
    name = song_name.lower()
    score = 5  # 默认5万
    for kw in hot_keywords:
        if kw.lower() in name:
            score = max(score, 50)
    for kw in viral_keywords:
        if kw.lower() in name:
            score = max(score, 100)
    return score
