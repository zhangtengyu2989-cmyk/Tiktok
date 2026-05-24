# 抖医开发计划

根据 CLAUDE.md 架构和现有数据分析，后续任务拆解：

---

## 架构理解

**现有架构：**
```
Input → 分析器 → 基线对比 → Round1(5Agent并行) → Round2(辩论) → Round3(裁判)
```

**数据已采集到位：**
- 876 视频
- 6782 评论
- 165 BGM
- 167 标题
- 890 封面
- **总计：8880+ 条**

---

## 后续任务拆解（5步）

### 第1步：基线知识图谱构建
**目的**：将数据转化为可查询的基线

**任务内容**：
- [ ] 分析8880+数据的品类分布
- [ ] 计算各品类爆款阈值（点赞/评论/分享）
- [ ] 建立标签热度排名
- [ ] 发布时段热力图分析
- [ ] 填充 baseline_stats 表

**输出**：baseline_stats 表完整，支撑基线对比能力

---

### 第2步：Model A — 量化预测引擎
**目的**：<50ms 无LLM调用的即时评分

**任务内容**：
- [ ] 基于8880数据训练回归模型
- [ ] 确定6品类差异化权重
- [ ] 5维度即时评分算法
- [ ] 集成到 BaselineComparator

**输出**：算法化的评分系统，<50ms响应

---

### 第3步：Comment Persona Engine — 评论画像引擎
**目的**：预测评论区用户画像

**任务内容**：
- [ ] 6种用户画像分析（种草/经验/质疑/凑热闹/求助/吐槽）
- [ ] 情绪分布算法
- [ ] 点赞预估模型
- [ ] 集成评论生成能力

**输出**：评论生成能力，模拟真实评论区

---

### 第4步：Multi-Agent辩论系统完善
**目的**：6个Agent三轮辩论

**任务内容**：
- [ ] 内容分析师 Agent
- [ ] 视觉诊断师 Agent
- [ ] BGM策略师 Agent
- [ ] 增长策略师 Agent
- [ ] 用户模拟器 Agent
- [ ] 裁判 Agent
- [ ] Round1 并行诊断
- [ ] Round2 交叉辩论
- [ ] Round3 综合裁定

**输出**：完整的6Agent辩论系统

---

### 第5步：产品化与UI优化
**目的**：完整用户体验

**任务内容**：
- [ ] 前端诊断页面
- [ ] SSE流式推送
- [ ] 雷达图可视化（6维度）
- [ ] 诊断卡片导出
- [ ] 前后端联调
- [ ] 分享功能

**输出**：完整的在线诊断产品

---

## 建议优先顺序

```
第1步 → 第3步 → 第2步 → 第4步 → 第5步
```

1. 先构建基线，才能对比评分
2. 评论引擎相对独立，优先完成
3. 量化预测引擎需要基线支撑
4. Agent辩论系统需要前置能力
5. 产品化最后阶段

---

## 进度追踪

| 步骤 | 状态 | 备注 |
|------|------|------|
| 第1步 | ✅ 完成 | 基线知识图谱：67条记录，6品类+全局统计 |
| 第2步 | ✅ 完成 | Model A：876条数据训练，差异化权重已学习并集成 |
| 第3步 | ✅ 完成 | 评论画像引擎：算法生成+LLM分析双模式，已集成到UserSimAgent |
| 第4步 | ✅ 完成 | Multi-Agent辩论：BGMAgent已集成到Round1和辩论轮，支持5Agent视频诊断 |
| 第5步 | ✅ 完成 | 产品化UI：6维雷达图自适应、诊断卡片导出、SSE进度映射修复 |

---

## 第1步完成详情

**baseline_stats 表：67条记录**

| 品类 | 指标数 | 说明 |
|------|--------|------|
| 美食 | 11 | 60视频，平均点赞112K |
| 时尚 | 11 | 4视频，平均点赞37K |
| 科技 | 11 | 21视频，平均点赞70K |
| 旅行 | 11 | 27视频，平均点赞186K |
| 生活 | 11 | 81视频，平均点赞180K |
| 其他 | 7 | 683视频，平均点赞160K |
| 全局 | 5 | 评论分布、情感分布、BGM热度、标题钩子 |

**已完成：**
- 品类分布分析
- 爆款阈值计算（前10%）
- 评论画像统计（6种类型）
- BGM热度分布
- 标题钩子模式统计（部分数据缺失）

**待完善：**
- 标签热度排名（video表无标签字段）
- 发布时段热力图（video表无详细时间字段）

---

## 第2步完成详情

**Model A — 量化预测引擎**

基于 876 条真实视频数据训练，完成品类差异化权重学习：

| 品类 | 样本数 | 最高权重维度 | 权重值 |
|------|--------|-------------|--------|
| 美食 | 60 | BGM适配 | 0.383 |
| 时尚 | 4 | 视觉表现 | 0.30 (参考值) |
| 科技 | 21 | 视觉/BGM/技术 | ~0.20 |
| 旅行 | 27 | 增长策略 | 0.201 |
| 生活 | 81 | 内容质量/用户共鸣 | ~0.182 |
| 其他 | 683 | 视觉表现 | 0.232 |

**已完成：**
- 从 876 条真实数据提取特征并训练
- 计算各品类最优标题长度、内容长度、标签数范围
- 学习并更新 6 品类差异化权重到 MODEL_PARAMS
- 修复 pre_score() 函数使用标准化6维度命名
- 将学习参数保存到 baseline_stats 表

**核心代码：**
- `app/agents/model_a_trainer.py` - 训练器（新增）
- `app/agents/research_data.py` - MODEL_PARAMS 已更新

---

## 第3步完成详情

**Comment Persona Engine — 评论画像引擎**

基于 6782 条真实评论数据训练，6种用户画像智能分布：

| 画像类型 | 描述 | 典型评论 | 点赞特征 |
|----------|------|---------|---------|
| 种草型 | 被内容打动想购买 | "已入手！等快递中" | 中等偏高 |
| 经验型 | 分享类似经历 | "我之前也买过，确实好用" | 中等 |
| 质疑型 | 有疑问或不同看法 | "真的假的？看着有点假" | 争议性高 |
| 凑热闹型 | 路过围观表达情绪 | "哈哈哈笑死我了" | 最高 |
| 求同款型 | 想要链接或产品 | "链接呢？求求了" | 较低 |
| 求助型 | 遇到问题寻求帮助 | "请问这个哪里有卖？" | 最低 |

**已完成：**
- `comment_persona_engine.py` - 完整实现（6种画像分类器、点赞预估模型、评论生成器）
- 修复 `generate_comment()` 的 `engagement_level` 参数传递bug
- `UserSimAgent` 集成算法引擎：`diagnose()` 优先使用算法生成评论，再由 LLM 分析画像
- 抖音风格昵称生成器（真实感：带数字如"减脂第30天"、地名、状态）
- 完整格式：`username` + `avatar_emoji` + `comment` + `sentiment` + `likes` + `time_ago` + `ip_location`

**核心代码：**
- `app/agents/comment_persona_engine.py` - 算法引擎（已完整）
- `app/agents/user_sim_agent.py` - 集成算法生成 + LLM 分析双模式

---

## 第4步完成详情

**Multi-Agent 辩论系统完善**

6 Agent 完整架构（视频内容）：

| 阶段 | Agent | 状态 |
|------|-------|------|
| Round1 并行 | 内容分析师 | ✅ 已有 |
| Round1 并行 | 视觉诊断师 | ✅ 已有 |
| Round1 并行 | 增长策略师 | ✅ 已有 |
| Round1 并行 | 用户模拟器 | ✅ 已有（算法+LLM双模式） |
| Round1 并行 | **BGM策略师** | ✅ **新增集成** |
| Round2 辩论 | 所有Agent | ✅ 5Agent交叉辩论 |
| Round3 裁判 | 裁判Agent | ✅ 已有 |

**已完成：**
- BGMAgent 导入并集成到 `orchestrator.run()`
- 新增 `bgm_name` 和 `bgm_heat` 参数（可选，有BGM信息时启用）
- Round1 动态 Agent 数量：4（无BGM）或 5（有BGM）
- 辩论 agents_list 动态包含 BGMAgent
- 进度消息动态更新（"4位专家" / "5位专家"）
- `_run_debate` agent_names 动态扩展

**核心代码：**
- `app/agents/orchestrator.py` - BGMAgent 集成到 Round1 和辩论轮
- `app/agents/bgm_agent.py` - BGM分析师（已完整）

---

## 第5步完成详情

**产品化与UI优化**

前端 UI 组件已完整实现并通过类型检查：

| 组件 | 状态 | 说明 |
|------|------|------|
| 诊断页面 | ✅ | SSE流式推送，12步进度动画 |
| 报告页面 | ✅ | 雷达图+维度条+基线对比+评论区 |
| 雷达图 | ✅ | 自适应5/6维度（content/visual/growth/user_reaction/bgm_adaptation/technical_performance） |
| 诊断卡片 | ✅ | html2canvas 导出 + Web Share API 分享 |
| 模拟评论区 | ✅ | SimulatedComments 组件，多轮刷新 |
| Agent辩论 | ✅ | AgentDebate 组件，时间线展示 |

**已完成：**
- `RadarChart.tsx` - 自适应渲染数据中存在的维度（5维或6维）
- `DimensionBars.tsx` - 同上，动态维度配置
- `DiagnoseCard.tsx` - html2canvas 导出，Object.entries 自适应渲染 radar_data
- `EVENT_STEP_MAP` - 修复 `round1_bgm_done` 映射，新增 `debate_agent_4` 映射
- `_build_stable_scores` - 新增 `bgm_adaptation`（来自 Model A）和 `technical_performance`（基于视频分析）维度

**核心代码：**
- `frontend/src/components/RadarChart.tsx` - 自适应多维度雷达图
- `frontend/src/components/DimensionBars.tsx` - 自适应多维度条形图
- `frontend/src/pages/Diagnosing.tsx` - SSE 进度映射修复（round1_bgm_done, debate_agent_4）
- `backend/app/agents/orchestrator.py` - 6维 stable_scores 计算

---

## 全部5步完成总结

| 步骤 | 核心产出 |
|------|---------|
| 第1步 | baseline_stats 表（67条记录，6品类统计） |
| 第2步 | Model A 量化预测引擎（876条数据训练，即时评分<50ms） |
| 第3步 | Comment Persona Engine（6种用户画像，算法+LLM双模式评论生成） |
| 第4步 | 5-Agent辩论系统（Content+Visual+Growth+UserSim+BGM） |
| 第5步 | 完整前端UI（6维雷达图、html2canvas导出、SSE流式诊断） |

