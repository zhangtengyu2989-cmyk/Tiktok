# 抖医 TiktokRx

### 抖音 Multi-Agent 内容诊断引擎

**抖音内容诊断** | 8880+ 条真实数据训练 | 6 AI 专家三轮辩论 | 多模态支持

<br>

> 提交你的抖音内容（视频链接/截图/文字），6 位 AI 专家会像医生会诊一样，三轮辩论后给出量化诊断报告、6维度评分、评论区预测，以及可执行的优化方案。

---

## 为什么是抖医

| | 传统工具 | 抖医 TiktokRx |
|---|---|---|
| **评分依据** | 主观经验 / 单模型打分 | 8880+ 条真实数据回归分析 → 6 品类差异化权重 |
| **诊断方式** | 单次 GPT 调用 | 6 Agent 并行诊断 → 交叉质疑辩论 → 裁判综合 |
| **建议质量** | "提升内容吸引力" | "BGM选择→改为「反差感强BGM」→配合快节奏剪辑→预计互动率+15%" |
| **评论预测** | 无 | AI 模拟真实评论区（含种草/质疑/求助/经验分享） |
| **优化闭环** | 给建议，用户自己改 | 自动生成优化方案 + 即时重新评分 |
| **数据支撑** | 无 | Spearman 相关 · 线性回归 · K-Means 聚类 · LLM 深度分析 |

## 核心技术

### 三大自训练模型

| 模型 | 训练数据 | 能力 |
|---|---|---|
| **Model A — 量化预测引擎** | 8880+ 条真实数据 · 回归分析 | 6 品类差异化权重 · 6 维度即时评分 · < 50ms 无 LLM 调用 |
| **Baseline Knowledge Graph — 基线知识图谱** | 876 视频 + 6782 评论 · K-Means 聚类 | 品类爆款线 · 互动中位数 · 标签分布 · 发布时段热力图 |
| **Comment Persona Engine — 评论画像引擎** | 6782 条真实评论 · LLM 分类 | 6 种用户画像（种草型/经验型/质疑型/凑热闹型/求助型/吐槽型）· 情绪分布 · 点赞预估 |

### 四阶段诊断引擎

```
Stage 1                    Stage 2                Stage 3                    Stage 4
数据驱动基线训练      →     Model A 智能初评    →   多智能体深度辩论        →    AI 优化闭环

8880+ 数据               6 维度即时打分          6 Agent 并行诊断            自动生成优化方案
Spearman / 回归 / 聚类   < 50ms 无 LLM          交叉质疑 · 补充论据          即时重新评分
6 品类差异化权重            品类差异化基线          裁判 Agent 综合裁定           最高分方案推荐
```

### Multi-Agent 辩论架构

```
Round 1: 并行诊断                    Round 2: 交叉辩论                Round 3: 综合裁判

[内容分析师] ─┐                      内容 ←→ 视觉                     ┌─→ 最终评分
[视觉诊断师] ─┤→ 独立诊断 + 评分     视觉 ←→ 增长      质疑/反驳      ├─→ 优化标题 + 文案
[BGM策略师] ──┤                      增长 ←→ 用户                     ├─→ 封面方向建议
[增长策略师] ─┤                      用户 ←→ 内容                     ├─→ BGM选择建议
[用户模拟器] ─┘                      BGM ←→ 内容      赞同/补充      └─→ 模拟评论区
```

### 6维度评分体系（视频）

| 维度 | 说明 |
|---|---|
| **content_quality** | 文案质量（标题、钩子，信息密度） |
| **visual_performance** | 视觉表现（封面、第一帧） |
| **bgm_adaptation** | BGM适配度（热度、节奏匹配） |
| **growth_strategy** | 增长策略（标签、发布时间） |
| **user_resonance** | 用户共鸣（评论区预测） |
| **technical_performance** | 技术表现（画质、剪辑节奏） |

### 5维度评分体系（图文/纯文字）

无 `bgm_adaptation` 维度，其余相同。

### BGM热度等级

| 等级 | 阈值 | 流量加持 |
|---|---|---|
| S+ | 100万+ | +30% |
| S | 50-100万 | +20% |
| A | 10-50万 | +15% |
| B | 1-10万 | +5% |
| C | <1万 | 0% |

### 技术栈

| 层 | 技术 |
|---|---|
| **前端** | React 19 · TypeScript · MUI v9 · Framer Motion · ECharts · Vite |
| **后端** | FastAPI · asyncio · SSE 流式推送 · SQLite |
| **AI** | MiMo-v2-Pro（诊断）· MiMo-v2-Omni（多模态视觉）· MiMo-v2-Flash（快速任务） |
| **爬虫** | Playwright · requests · TikTok API |
| **分析** | jieba 分词 · OpenCV 图像分析 · OCR 文字提取 · 视频首帧/听写 |

## 产品功能

- **多模态输入**：视频链接 / 图片上传 / 纯文字输入，AI 自动识别内容类型
- **实时诊断动画**：12 步时间线 + 辩论实况气泡 + Agent 状态跟踪
- **六维雷达评分**：内容质量 · 视觉表现 · BGM适配 · 增长策略 · 用户共鸣 · 技术表现
- **AI 模拟评论区**：真实抖音风格（含种草/质疑/求助/经验分享），预估点赞数
- **迭代优化引擎**：自动生成优化方案，自动评分 + 最高分推荐
- **基线对比**：与同品类数千条视频对比（标题字数 / 标签数 / 爆款率）
- **分享卡片**：一键生成带品牌水印的诊断卡片
- **诊断历史**：本地 IndexedDB 存储，隐私安全

## 快速开始

```bash
# 安装依赖
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd frontend && npm install

# 初始化数据库
cd backend && python -c "from app.main import init_db; init_db()"

# 启动后端 (port 8002)
cd backend && source venv/bin/activate && uvicorn app.main:app --port 8002 --reload

# 启动前端 (port 5173)
cd frontend && npm run dev
```

访问 `http://localhost:5173`

## 数据采集

```bash
# 一键采集所有数据（BGM + 标题 + 评论 + 封面）
cd backend && source venv/bin/activate
python -c "from app.crawler.data_crawler import crawl_all_data; crawl_all_data()"
```

**当前数据规模：**

| 数据类型 | 数量 | 说明 |
|---|---|---|
| 视频数据 | 876 | 完整视频信息 |
| 评论数据 | 6782 | 带类型标注 |
| BGM知识库 | 165 | 带热度等级 |
| 标题知识库 | 167 | 带钩子模式 |
| 封面数据 | 890 | 带色彩分析 |

---

**抖医 TiktokRx** — 抖音内容诊断平台
