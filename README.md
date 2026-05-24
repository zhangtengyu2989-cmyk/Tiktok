<div align="center">

# 抖医 TiktokRx

### AI Multi-Agent 抖音内容诊断引擎

**8880+ 真实数据训练** | **6 AI 专家三轮辩论** | **六维量化评分** | **多模态支持**

<br>

[**立即在线体验**](https://eliotech.top/app/) &nbsp;&nbsp;|&nbsp;&nbsp; [着陆页](https://eliotech.top/) &nbsp;&nbsp;|&nbsp;&nbsp; [技术架构](#技术架构)

<br>

> 提交你的抖音内容（视频链接/截图/文字/BGM），6 位 AI 专家会像医生会诊一样，三轮辩论后给出量化诊断报告、六维评分、评论区预测，以及可执行的优化方案。

</div>

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

## 在线体验

**https://eliotech.top/app/**

1. 打开链接 → 上传抖音内容（视频链接/截图/文字/BGM名称）
2. AI 自动识别标题、内容、分类（< 30s）
3. 点击"开始诊断" → 观看 6 位 AI 专家实时辩论
4. 获取完整报告：评分 · 雷达图 · 优化方案 · 模拟评论区 · 分享卡片

手机电脑均可使用，无需注册。

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
Spearman / 回归 / 聚类   < 50ms 无 LLM          交叉质疑 · 补充论据         即时重新评分
6 品类差异化权重            品类差异化基线          裁判 Agent 综合裁定         最高分方案推荐
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

### 技术栈

| 层 | 技术 |
|---|---|
| **前端** | React 19 · TypeScript · MUI v9 · Framer Motion · ECharts · Vite |
| **后端** | FastAPI · asyncio · SSE 流式推送 · SQLite |
| **AI** | MiMo-v2-Pro（诊断）· MiMo-v2-Omni（多模态视觉）· MiMo-v2-Flash（快速任务） |
| **分析** | jieba 分词 · OpenCV 图像分析 · OCR 文字提取 · 视频首帧/听写 |
| **研究** | Spearman 相关 · 线性回归 · K-Means 聚类 · PCA 可视化 |

## 产品功能

- **多模态输入**：视频链接 / 截图拖入 / Ctrl+V 粘贴 / 纯文字输入 / BGM 名称，AI 自动识别内容类型
- **实时诊断动画**：12 步时间线 + 辩论实况气泡 + Agent 状态跟踪
- **六维雷达评分**：内容质量 · 视觉表现 · BGM适配 · 增长策略 · 用户共鸣 · 技术表现
- **AI 模拟评论区**：真实抖音风格（含种草/质疑/求助/经验分享），预估点赞数
- **迭代优化引擎**：自动生成优化方案，自动评分 + 最高分推荐
- **基线对比**：与同品类数千条视频对比（标题字数 / 标签数 / 爆款率）
- **分享卡片**：一键生成带品牌水印的诊断卡片
- **诊断历史**：本地 IndexedDB 存储，隐私安全
- **BGM 分析**：BGM 热度等级（S+/S/A/B/C）、适配度评估、推流加持预测
- **纯文字分析**：文案质量专项分析（信息密度、情感表达、互动引导）

## 内容诊断类型

| 类型 | 输入 | 维度 | Agent |
|------|------|------|-------|
| 短视频 | 视频链接/封面截图 | 6维 | 6个（含BGM Agent） |
| 图文 | 图片+文字 | 5维 | 5个（无BGM） |
| 纯文字 | 纯文本 | 5维 | 5个（无BGM） |
| BGM分析 | 音频/歌曲名 | 独立评分 | BGMAgent |

## 快速开始

```bash
# 克隆
git clone https://github.com/anthropics/claude-code.git && cd tiktok

# 配置
cp backend/.env.example backend/.env  # 编辑填入 API Key

# 一键安装 + 启动
python init_env.py
python start_project.py
```

访问 `http://localhost:5173/app/`

### 分别启动

```bash
# 后端 (http://127.0.0.1:8002)
bash start_backend.sh

# 前端 (http://localhost:5173/app/)
bash start_frontend.sh
```

### 环境要求

- Python 3.10+
- Node.js 18+
- FFmpeg（视频口播转写需要）

## 项目结构

```
D:/Tiktok/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口，生命周期钩子
│   │   ├── agents/              # 多Agent系统
│   │   │   ├── orchestrator.py  # 辩论编排（Round 1-3）
│   │   │   ├── base_agent.py    # 基类（MiMo/Anthropic 适配）
│   │   │   ├── content_agent.py # 内容分析师
│   │   │   ├── visual_agent.py  # 视觉诊断师
│   │   │   ├── bgm_agent.py     # BGM策略师
│   │   │   ├── growth_agent.py  # 增长策略师
│   │   │   ├── user_sim_agent.py# 用户模拟器
│   │   │   └── judge_agent.py   # 综合裁判
│   │   ├── analysis/            # 内容分析器
│   │   │   ├── text_analyzer.py
│   │   │   ├── image_analyzer.py
│   │   │   ├── video_analyzer.py
│   │   │   ├── ocr_processor.py
│   │   │   └── video_stt.py
│   │   ├── api/                 # API路由
│   │   │   ├── routes.py        # 路由注册
│   │   │   ├── diagnose.py      # 诊断接口
│   │   │   ├── bgm_api.py       # BGM分析
│   │   │   ├── auth_api.py      # 用户认证
│   │   │   └── ...
│   │   └── baseline/            # 基线对比
│   ├── data/                    # SQLite 数据库
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # 页面组件
│   │   │   ├── Home.tsx
│   │   │   ├── Diagnosing.tsx
│   │   │   ├── Report.tsx
│   │   │   ├── History.tsx
│   │   │   └── ScreenshotAnalysis.tsx
│   │   ├── components/          # 通用组件
│   │   └── utils/               # API客户端、本地存储
│   ├── vite.config.ts
│   └── package.json
├── docs/                        # 着陆页、法律文档
├── start_project.py             # 一键启动
├── start_backend.sh
└── start_frontend.sh
```

## 数据采集

```bash
cd backend && source venv/bin/activate
python -c "from app.crawler.data_crawler import crawl_all_data; crawl_all_data()"
```

| 数据类型 | 数量 | 说明 |
|---|---|---|
| 视频数据 | 876 | 完整视频信息 |
| 评论数据 | 6782 | 带类型标注 |
| BGM知识库 | 850+ | 带热度等级（QQ音乐多榜单） |
| 标题知识库 | 534 | 带钩子模式 |

## License

Apache License 2.0

---

<div align="center">

**[立即体验 →](https://eliotech.top/app/)**

</div>
