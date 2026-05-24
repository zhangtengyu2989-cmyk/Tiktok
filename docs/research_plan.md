# 抖医 TiktokRx 数据研究方案

## 一、研究目标

建立一套**可量化、可复现、可自进化**的抖音内容评价体系，最终产出：

1. **量化评分系统** — 基于传统统计方法，输出 6 维度评分标准与品类差异化权重
2. **LLM 评价标准** — 基于 MiMo 模型的内容/视觉/BGM/增长策略评价流程和提示词
3. **用户画像系统** — 基于 6782 条评论数据构建 6 种用户画像模板
4. **BGM 分析模块** — 独立于 NoteRx，分析 BGM 热度等级与流量加持关系
5. **最终研究报告** — 双轨分析结果 + 可视化 + 结论 + 可落地的评分参数

---

## 二、双轨分析架构

```
                    ┌──────────────────────────────────┐
                    │         原始数据入库               │
                    │  抖音/爬虫数据 → 统一 SQLite 格式  │
                    │  backend/data/tiktok_baseline.db  │
                    └───────────┬──────────────────────┘
                                │
                    ┌───────────▼──────────────────────┐
                    │       数据清洗 & 特征工程           │
                    │  文本特征 / 视觉特征 / 互动指标      │
                    │  BGM热度 / 视频时长 / 封面特征      │
                    └───────┬───────────┬──────────────┘
                            │           │
              ┌─────────────▼──┐  ┌─────▼──────────────┐
              │  Track A:       │  │  Track B:           │
              │  传统统计分析    │  │  LLM 深度分析        │
              │                │  │                     │
              │  ▸ 描述统计     │  │  ▸ mimo-v2-omni     │
              │  ▸ 相关性分析   │  │    视频封面理解      │
              │  ▸ 回归建模     │  │  ▸ mimo-v2-pro      │
              │  ▸ K-Means聚类 │  │    内容模式总结      │
              │  ▸ Spearman相关│  │  ▸ 标题钩子分析      │
              │  ▸ 品类间ANOVA │  │  ▸ BGM适配度评价    │
              │  ▸ 爆款阈值    │  │  ▸ 标签策略分析      │
              └───────┬────────┘  └────────┬────────────┘
                      │                    │
              ┌───────▼────────────────────▼────────────┐
              │          参数报告 & 评价标准               │
              │  量化参数 → 注入 6 个 Agent 系统提示词     │
              │  LLM 基于参数做统计解读和优化建议          │
              └───────────────────┬─────────────────────┘
                                  │
              ┌───────────────────▼─────────────────────┐
              │           最终研究报告                    │
              │  统计图表 + LLM 分析 + 结论 + 可视化      │
              └─────────────────────────────────────────┘

              ┌─────────────────────────────────────────┐
              │     独立模块 A: 用户画像系统               │
              │  6782条评论 → LLM分类 → 6种画像模板       │
              └─────────────────────────────────────────┘

              ┌─────────────────────────────────────────┐
              │     独立模块 B: BGM分析系统               │
              │  850条BGM → 热度等级 → 流量加持模型       │
              └─────────────────────────────────────────┘
```

---

## 三、数据源与处理

### 3.1 现有数据（已入库 tiktok_baseline.db）

| 数据类型 | 记录数 | 来源 | 状态 |
|----------|--------|------|------|
| 视频数据 | 8880+ | 抖音爬虫 + QQ音乐API | 已入库 |
| BGM 数据库 | 850 | QQ音乐多榜单（热/新/PC/亚洲/韩语/说唱/古典） | 已入库 |
| 标题数据库 | 534 | 抖音热搜 + 合成标题 | 已入库 |
| 评论数据库 | 2502 | 合成评论（每品类~500条） | 已入库 |
| 封面数据库 | 0 | 待实现 | 未采集 |

**五大品类**：美食 / 穿搭 / 科技 / 旅行 / 生活

### 3.2 统一字段映射

采集原始字段 → 系统内部字段：

| 原始列名 | 内部字段 | 类型 | 说明 |
|----------|---------|------|------|
| 视频ID | video_id | TEXT | 主键，去重 |
| 视频链接 | video_url | TEXT | 抖音分享链接 |
| 视频标题 | title | TEXT | |
| 视频描述 | description | TEXT | |
| 话题标签 | tags | TEXT→JSON | 井号分割后转 JSON 数组 |
| 点赞量 | likes | INT | |
| 评论量 | comments_count | INT | |
| 分享量 | shares | INT | |
| 收藏量 | collects | INT | |
| BGM名称 | bgm_name | TEXT | |
| 发布时间 | publish_time | DATETIME | |
| 博主昵称 | author_name | TEXT | |
| 博主粉丝数 | author_followers | INT | |
| 视频时长 | video_duration | INT | 秒 |
| 封面链接 | cover_url | TEXT | 用于视觉分析 |

### 3.3 衍生特征（数据清洗阶段自动计算）

| 特征 | 计算方式 | 用途 |
|------|---------|------|
| title_length | len(title) | 标题长度分析 |
| tag_count | len(tags) | 标签数量分析 |
| has_emoji | regex 检测 | 表情使用率 |
| has_numbers | regex 检测 | 标题数字使用率 |
| has_exclaim | regex 检测 | 感叹号使用率 |
| has_question | regex 检测 | 问号钩子使用率 |
| engagement | likes + collects + comments + shares | 综合互动量 |
| engagement_rate | engagement / author_followers | 互动率（归一化） |
| is_viral | engagement > 品类 P90 | 是否爆款 |
| publish_hour | extract from publish_time | 发布时段 |
| publish_weekday | extract from publish_time | 发布星期 |
| title_hook_count | 检测数字/感叹号/问号/竖线/emoji | 标题钩子数 |
| video_duration_bucket | 0-15s / 15-30s / 30-60s / 60s+ | 时长分桶 |

### 3.4 评论数据结构

| 字段 | 类型 | 说明 |
|------|------|------|
| comment_id | TEXT | 主键 |
| video_id | TEXT | 关联视频 |
| content | TEXT | 评论文本 |
| comment_type | TEXT | 种草型/经验型/质疑型/凑热闹型/求助型/吐槽型 |
| sentiment | TEXT | positive/negative/neutral |
| likes | INT | 评论点赞数 |
| category | TEXT | 所属品类 |

---

## 四、Track A：传统统计分析

### 4.1 描述性统计（每品类）

对每个品类（美食/穿搭/科技/旅行/生活）输出基础统计报告：

- 各指标的均值、中位数、标准差、分位数（P25/P50/P75/P90）
- 爆款视频 vs 普通视频的各维度对比
- 视频时长分桶的互动差异

### 4.2 相关性分析

计算以下变量间的 Spearman 相关系数（Spearman 对非线性关系更鲁棒）：

| 变量 A | 变量 B | 假设 |
|--------|--------|------|
| title_length | engagement | 标题越长互动越好？ |
| tag_count | engagement | 标签越多曝光越多？ |
| video_duration | engagement | 时长影响互动？ |
| has_numbers | likes | 数字标题更吸引？ |
| has_exclaim | likes | 感叹号提升点击？ |
| publish_hour | engagement | 发布时间影响互动？ |
| author_followers | engagement | 大号效应有多强？ |
| bgm_heat_level | engagement | 热门BGM提升流量？ |

输出：相关性矩阵热力图 + 显著性标注

### 4.3 控变量回归分析

使用多元线性回归，控制粉丝量级后分析各因素对互动量的独立贡献：

```
engagement ~ title_length + tag_count + has_numbers + has_exclaim
             + video_duration + publish_hour + category
             + bgm_heat_level + author_tier (粉丝量分桶)
```

粉丝量分桶：nano(<1K), micro(1K-10K), mid(10K-100K), macro(100K-1M), mega(1M+)

### 4.4 品类间差异分析

- ANOVA / Kruskal-Wallis 检验品类间差异显著性
- 每品类的「最优参数区间」提取
- 输出：品类差异雷达图（6维度）

### 4.5 聚类分析

对视频做 K-Means / DBSCAN 聚类，发现自然分群：
- 爆款视频的共同特征模式
- 不同创作风格的视频群
- 异常值分析（超级爆款 vs 数据异常）

### 4.6 BGM 热度等级基准分析

| 等级 | 阈值 | 预期流量加持 | 样本量 |
|------|------|-------------|--------|
| S+ | 100万+ | +30% | |
| S | 50-100万 | +20% | |
| A | 10-50万 | +15% | |
| B | 1-10万 | +5% | |
| C | <1万 | 0% | |

验证各等级 BGM 的实际互动提升是否符合预期。

---

## 五、Track B：LLM 深度分析

### 5.1 视频封面视觉分析（mimo-v2-omni）

对每条视频的封面图：
1. 下载封面图片
2. 调用 mimo-v2-omni 多模态分析

**提示词**：

```
你是一个抖音视频封面视觉分析专家。请分析这张抖音视频封面图片，输出 JSON 格式：

{
  "cover_style": "人物出镜/产品特写/场景图/拼图/纯文字/对比图/字幕封面",
  "color_tone": "暖色调/冷色调/中性/高饱和/低饱和",
  "text_overlay": "有/无",
  "text_content": "封面上的文字内容（如有）",
  "text_area_ratio": 0.0-1.0,
  "has_face": true/false,
  "face_expression": "微笑/严肃/夸张/无",
  "composition": "居中/三分法/对角线/留白/满铺",
  "visual_quality": 1-10,
  "click_appeal": 1-10,
  "style_tags": ["ins风", "国潮", "极简", "复古", "科技感", ...],
  "first_frame_recommendation": "是否适合做第一帧(1-10)"
}

只输出 JSON，不要其他内容。
```

**并行策略**：asyncio.gather 批量调用，每批 5 张，控制并发避免限流

### 5.2 标题钩子模式分析（mimo-v2-pro）

对每品类的爆款视频标题，调用 LLM 总结钩子模式：

```
你是抖音内容研究专家。以下是 {category} 品类中 {count} 条爆款视频的标题。

请分析并总结：

1. **钩子模式**（5-8 种常见模式，每种给出模板和示例）
   - 如：数字型「3步搞定XXX」、悬念型「千万别XXX」、疑问型「为什么XXX」
2. **情绪基调**（热情/专业/亲切/犀利/幽默/震惊）
3. **信息密度**（高密度干货 vs 轻松随意）
4. **品类专属高频词**

输出 JSON 格式：
{
  "hook_patterns": [...],
  "emotion_tone": "...",
  "info_density": "...",
  "high_freq_words": [...],
  "key_findings": ["..."]
}

标题数据如下：
{titles_json}
```

### 5.3 标签策略分析（mimo-v2-pro）

```
分析以下 {category} 品类视频的标签使用策略。数据包含每条视频的标签列表和互动数据。

请输出：
1. 热门标签 TOP 20 及其平均互动量
2. 长尾标签中互动率最高的 10 个（小众但有效）
3. 最佳标签组合模式（哪些标签经常同时出现在爆款中）
4. 标签数量与互动量的关系曲线描述
5. 品类专属的标签策略建议

{videos_with_tags_json}
```

### 5.4 LLM 综合评价（基于 Track A 输出）

Track A 的量化分析完成后，将统计报告传给 mimo-v2-pro 做深度解读：

```
你是一个数据科学家，专门研究抖音短视频内容。以下是我们对 {category} 品类
{total_videos} 条抖音视频的统计分析结果。

请基于这些数据：
1. 解读每个统计发现的实际意义（不要复述数字，要解释 why）
2. 发现数据中的反直觉结论（如果有）
3. 给出该品类的「黄金参数」推荐值（标题长度、标签数、视频时长、发布时间等）
4. 指出数据局限性和可能的偏差
5. 与其他品类的对比发现

统计报告：
{track_a_report_json}
```

---

## 六、用户画像系统（独立模块）

### 6.1 数据源

评论数据：当前 2502 条（合成评论），目标扩展至 6782+ 条。

### 6.2 6 种评论画像类型

| 类型 | 占比 | 特征 |
|------|------|------|
| 种草型 | 30% | 语气热情，求链接，「看起来好好吃」「求同款」 |
| 经验型 | 22% | 分享使用体验，专业评价，「我试过这个XXX」 |
| 质疑型 | 18% | 质疑真实性或效果，「真的假的」「又在带货」 |
| 凑热闹型 | 15% | 路人围观，无意义但增加评论量，「哈哈哈」「前排」 |
| 求助型 | 10% | 具体问题咨询，「怎么做到的」「新手求助」 |
| 吐槽型 | 5% | 负面评价，吐槽槽点，「太贵了」「不实用」 |

### 6.3 画像构建流程

```
评论原始数据
     ↓
  LLM 分类（mimo-v2-flash，快速批量处理）
  → 每条评论标注：情感倾向 / 用户类型 / 评论意图
     ↓
  传统聚类验证
  → TF-IDF + K-Means 对评论文本聚类
  → 与 LLM 分类结果交叉验证
     ↓
  LLM 画像总结（mimo-v2-pro）
  → 输出 6 种用户画像模板
     ↓
  画像参数化
  → 每种画像：名称、占比、语言风格、触发条件、示例评论
     ↓
  写入系统配置
  → 注入 UserSimAgent 生成更真实的模拟评论
```

### 6.4 画像分类提示词（mimo-v2-flash）

```
对以下抖音评论进行分类，输出 JSON：
{
  "sentiment": "positive/negative/neutral",
  "user_type": "种草型/经验型/质疑型/凑热闹型/求助型/吐槽型",
  "intent": "赞美/追问/分享经验/质疑/求链接/吐槽/互动",
  "emotion_level": 1-5
}

评论："{comment_text}"
```

---

## 七、BGM 分析（独立模块，TiktokRx 独有）

### 7.1 数据源

BGM 数据库：850 条 BGM，来自 QQ音乐多榜单（热榜/新歌/PC榜/亚洲/韩语/说唱/古典）。

### 7.2 分析维度

| 维度 | 说明 | 输出 |
|------|------|------|
| 热度等级 | 播放量 → S+/S/A/B/C 五级 | 等级判定规则 |
| 品类适配 | BGM风格 vs 品类内容匹配度 | 品类-BGM推荐矩阵 |
| 节奏匹配 | BPM vs 视频节奏（快剪/慢镜头） | 时长-BPM最优区间 |
| 流量加持 | 各等级 BGM 实际互动提升 | 验证 +/-30% 假设 |
| 趋势预测 | 新上榜 BGM 的上升趋势 | 热度预测模型 |

### 7.3 BGM Agent 评价提示词（mimo-v2-pro）

```
你是抖音 BGM 策略专家。以下是一段视频的信息和使用的 BGM 数据。

视频信息：
- 品类：{category}
- 视频时长：{duration}秒
- 当前BGM：{bgm_name}
- BGM热度等级：{heat_level}
- BGM流派：{genre}

请从以下维度评价 BGM 适配度（1-10分）：
1. 热度匹配：BGM是否在当前热度高峰期
2. 节奏匹配：BGM节奏是否适合视频剪辑节奏
3. 情绪匹配：BGM情绪是否与内容主题一致
4. 品类适配：该BGM在{category}品类中是否常见

输出 JSON：
{
  "heat_score": 1-10,
  "rhythm_score": 1-10,
  "emotion_score": 1-10,
  "category_fit": 1-10,
  "overall_score": 1-10,
  "recommendation": "保持/更换为XXX",
  "traffic_boost_estimate": "预计流量加持 +/-X%"
}
```

### 7.4 分析脚本

位于 `backend/app/crawler/` 目录下，通过 QQ音乐 API 采集实时数据并更新热度等级。

---

## 八、执行步骤

### Step 1: 数据导入与验证
```bash
cd backend && source venv/bin/activate
python -c "from app.main import init_db; init_db()"
```
- 验证 `tiktok_baseline.db` 中各表数据完整性
- 统计各品类视频数、评论数、BGM 数
- 输出数据质量报告

### Step 2: 视频封面下载
```bash
python backend/app/crawler/download_covers.py
```
- 从 cover_url 批量下载封面图片到 `backend/data/covers/{category}/`
- 并行下载，失败重试
- 目前 cover_database 为 0，此步骤优先补充

### Step 3: 传统统计分析（Track A）
```bash
python backend/app/research/01_traditional_analysis.py
```
- 描述统计 → Spearman 相关性 → 回归 → K-Means 聚类 → ANOVA
- 输出图表到 `backend/data/research_output/charts/`
- 输出统计 JSON 到 `backend/data/research_output/stats/`

### Step 4: LLM 分析（Track B）
```bash
python backend/app/research/02_llm_analysis.py
```
- 封面视觉分析（mimo-v2-omni，并发 5）
- 标题钩子模式总结（mimo-v2-pro）
- 标签策略分析（mimo-v2-pro）
- BGM 适配度评价（mimo-v2-pro）
- 输出到 `backend/data/research_output/llm/`

### Step 5: 综合报告生成
```bash
python backend/app/research/03_generate_report.py
```
- 合并 Track A + Track B 结果
- 传给 mimo-v2-pro 做最终解读
- 生成可视化图表
- 输出最终报告 `backend/data/research_output/final_report.md`

### Step 6: 用户画像构建（独立）
```bash
python backend/app/research/04_user_persona.py
```
- 评论分类（mimo-v2-flash，批量处理）
- TF-IDF + K-Means 聚类交叉验证
- 输出 6 种画像配置 JSON → 注入 UserSimAgent

### Step 7: 评分参数输出
```bash
python backend/app/research/05_output_params.py
```
- 汇总所有分析结果
- 输出每品类量化评分参数 JSON
- 输出 Agent 评价提示词模板

---

## 九、模型使用策略

| 任务 | 模型 | 并发数 | 单条耗时 | 说明 |
|------|------|--------|---------|------|
| 封面视觉分析 | mimo-v2-omni | 5 | ~3s | 每张图片独立调用 |
| 评论快速分类 | mimo-v2-flash | 10 | ~0.5s | 批量处理，每次10条 |
| 标题钩子分析 | mimo-v2-pro | 1 | ~10s | 每品类一次，传入50-100条标题 |
| 标签策略分析 | mimo-v2-pro | 1 | ~8s | 每品类一次 |
| BGM适配度评价 | mimo-v2-pro | 1 | ~10s | 每品类BGM样本分析 |
| 统计报告解读 | mimo-v2-pro | 1 | ~15s | 每品类一次，传入完整统计JSON |
| 最终报告生成 | mimo-v2-pro | 1 | ~20s | 全局一次 |
| 画像总结 | mimo-v2-pro | 1 | ~10s | 每品类一次 |

**预估总调用量**（按 5 品类 × ~1776 条视频/品类）：
- omni 调用：~8880 次（封面分析，需补充封面数据）
- flash 调用：~2500 次（评论分类，按 2502 条评论）
- pro 调用：~50 次（标题/标签/BGM/统计/报告/画像）

---

## 十、输出物

### 10.1 量化评分参数（每品类）

```json
{
  "category": "美食",
  "dimensions": {
    "content_quality": { "title_length_optimal": [12, 20], "hook_types": ["数字型", "悬念型"], "weight": 0.20 },
    "visual_performance": { "cover_style_preference": ["产品特写", "场景图"], "weight": 0.15 },
    "bgm_adaptation": { "preferred_heat_level": "A+", "optimal_bpm_range": [100, 130], "weight": 0.15 },
    "growth_strategy": { "optimal_tags": [3, 6], "best_hours": [11, 12, 18, 19, 20], "weight": 0.15 },
    "user_resonance": { "comment_rate_threshold": 0.02, "weight": 0.20 },
    "technical_performance": { "optimal_duration": [15, 45], "weight": 0.15 }
  },
  "baseline": {
    "avg_engagement": 1234,
    "viral_threshold": 5000,
    "viral_rate": 0.12,
    "avg_likes": 800,
    "avg_comments": 45
  }
}
```

### 10.2 LLM 评价标准

每品类输出一套 6 个 Agent 用的评价提示词模板，包含从数据中提取的具体标准（而非主观判断）。

### 10.3 用户画像模板

```json
{
  "category": "美食",
  "personas": [
    {
      "name": "种草小白",
      "ratio": 0.30,
      "style": "语气热情，大量使用感叹号和表情",
      "patterns": ["看起来好好吃！", "收藏了回家试", "姐妹这个在哪买的"],
      "triggers": "产品推荐、教程类内容"
    }
  ]
}
```

### 10.4 BGM 推荐矩阵

```json
{
  "category": "美食",
  "recommended_bgms": [
    { "name": "XXX", "heat_level": "S", "genre": "轻快", "avg_engagement_boost": 0.18 }
  ],
  "avoid_bgms": [...]
}
```

### 10.5 最终研究报告

包含章节：
1. 研究背景与方法论
2. 数据概览（8880+视频 / 2502评论 / 850 BGM）
3. 各品类描述性统计
4. 相关性与回归分析结果（Spearman + 线性回归）
5. 封面视觉分析发现（LLM）
6. 标题钩子与标签策略分析（LLM）
7. BGM 热度与流量加持分析
8. 品类间差异对比
9. 用户画像研究
10. 6 维度量化评分标准制定依据
11. 局限性与后续研究方向

---

## 十一、可视化清单

| 图表 | 类型 | 内容 |
|------|------|------|
| 互动量分布 | 箱线图 | 各品类 likes/comments/shares 分布 |
| 相关性矩阵 | 热力图 | 各变量间 Spearman 相关性 |
| 标题长度 vs 互动 | 散点图+回归线 | 控制粉丝量后的关系 |
| 标签数 vs 互动 | 折线图 | 最优标签数量 |
| 发布时段热力图 | 热力图 | 时段 × 星期 × 平均互动 |
| 品类雷达图 | 雷达图 | 5 品类 6 维度最优参数对比 |
| 封面风格分布 | 饼图/条形图 | LLM 分析的封面类型占比 |
| 爆款特征对比 | 分组条形图 | 爆款 vs 普通各维度对比 |
| 聚类可视化 | 散点图(PCA降维) | 视频聚类分群 |
| 用户画像分布 | 环形图 | 6 种评论类型占比 |
| BGM热度等级分布 | 条形图 | S+/S/A/B/C 各等级 BGM 数量 |
| BGM品类适配矩阵 | 热力图 | BGM流派 × 品类适配度 |
| 视频时长分布 | 直方图 | 各品类视频时长分桶占比 |
| 爆款标签云 | 词云图 | 爆款视频高频标签 |
