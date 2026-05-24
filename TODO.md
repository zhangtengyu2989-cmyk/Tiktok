# 抖医 TiktokRx — TODO

> 对照薯医 NoteRx 项目查缺补漏，按优先级排列。

---

## 已完成

- [x] **BGM 数据库扩充** — 聚合调度器 + 多平台爬虫（QQ音乐/抖音/酷狗/酷我/咪咕/Apple Music/Spotify/YouTube Music）→ 预估2000+条
- [x] **数据源扩展** — 新增 social_spiders.py（今日头条/微信搜一搜/百度贴吧），降级策略优化
- [x] **用户体系** — 完成 auth_api + sync_api + 前端 AuthContext + LoginDialog
- [x] **导出稳定性** — export_api.py 后端 Playwright 渲染，前端 DiagnoseCard 降级适配
- [x] **cover_database 补充** — 各 collector 的 save_cover 现在会调用 full_cover_analysis 进行完整封面分析（颜色+构图），不再只存 URL
- [x] **Agent 超时容错增强** — 辩论超时 Agent 标记 `_timed_out` 并在 timeline 中过滤；返回 `debate_partial` 标记；`_usage` 中记录 `debate_timeouts` 数量
- [x] **视频分析能力加强** — 主诊断流程（diagnose.py）中当 MiMo 视频理解不可用时，尝试调用 Whisper STT 提取口播内容补充到正文中
- [x] **BGM 数据库扩充** — 创建 bgm_aggregator.py 聚合调度器，扩展 bgm_database 表结构，新增 bgm_admin_api.py 管理接口
- [x] **数据源扩展** — 创建 social_spiders.py 实现今日头条/微信搜一搜/百度贴吧爬虫，优化 title_crawler.py 降级策略
- [x] **用户体系** — 数据库 users/user_devices/sync_log 表，auth_api.py 注册登录，sync_api.py 跨设备同步，前端 AuthContext + LoginDialog
- [x] **导出稳定性** — export_api.py 后端 Playwright 渲染，DiagnoseCard.tsx 优先后端降级html2canvas
- [x] **着陆页** — docs/landing.html + Vite 插件 + 后端路由

---

## P0 — 必须补齐（合规/基础）

### 1. 隐私政策页面 `docs/privacy.html`
- [x] 创建隐私政策 HTML（参考 NoteRx `docs/privacy.html`）
- [x] 内容：信息收集说明、本地存储说明、匿名数据、第三方服务（MiMo API）、Cookie 政策、联系方式
- [x] 内嵌 `/api/visit` 追踪 beacon 脚本
- [x] 后端 `main.py` 添加 `/privacy` 路由
- [x] 着陆页 Footer 添加 `/privacy` 链接

### 2. 服务条款页面 `docs/terms.html`
- [x] 创建服务条款 HTML（参考 NoteRx `docs/terms.html`）
- [x] 内容：服务说明、用户责任、免责声明、数据说明、知识产权、适用法律
- [x] 内嵌 `/api/visit` 追踪 beacon 脚本
- [x] 后端 `main.py` 添加 `/terms` 路由
- [x] 着陆页 Footer 添加 `/terms` 链接

### 3. README.md
- [x] 项目名称 + 标语 + 在线地址
- [x] 核心价值主张（与传统工具对比表）
- [x] 三大自训练模型说明（Model A / 基线知识图谱 / 评论画像引擎）
- [x] 四阶段诊断引擎流程图
- [x] 快速开始（安装、启动、部署）
- [x] 技术栈
- [x] 数据采集说明
- [x] 项目结构树

---

## P1 — 应该补齐（开发体验/部署）

### 4. `.env.example`
- [x] 完整环境变量模板已存在（`backend/.env.example`）
- [x] 包含：LLM Provider、API Key、Base URL、模型名称（PRO/OMNI/FAST）
- [x] MiMo 视频理解参数（FPS、media_resolution）
- [x] Whisper/STT 配置
- [x] 服务端口、上传大小限制
- [x] 前端 `VITE_DIAGNOSE_MAX_WAIT_MS` 等

### 5. `start.sh` 一键启动脚本
- [x] 后端 venv 激活 + uvicorn 启动
- [x] 前端 npm dev 启动
- [x] 信号处理（Ctrl+C 优雅退出）

### 6. `Makefile`
- [x] `make install` — 安装依赖
- [x] `make dev` — 启动开发环境
- [x] `make build` — 构建前端
- [x] `make data` — 初始化数据库
- [x] `make clean` — 清理构建产物

### 7. `deploy_backend.py` 部署脚本
- [x] 生产环境部署（uvicorn + 前端静态文件）

---

## P2 — 建议补齐（着陆页增强）

### 8. 着陆页 Footer 增强
- [x] 添加「隐私政策」链接 → `/privacy`
- [x] 添加「服务条款」链接 → `/terms`
- [x] 数据来源声明完善

### 9. 着陆页顶部导航栏
- [x] 添加固定顶部导航栏（Logo + 产品特点锚点 + 开始诊断 CTA）
- [x] 滚动阴影效果 + 移动端适配

### 10. 着陆页「数据来源声明」完善
- [x] Footer 补充完整数据来源说明

---

## P3 — 可选增强（文档/白皮书）

### 11. 研究白皮书 `docs/whitepaper.md`
- [x] 创建研究白皮书 markdown 页面

### 12. 竞赛/演示文档
- [x] `docs/competition_battleplan.md` — 竞赛策略
- [x] `docs/presentation_strategy.md` — 演示策略
- [x] `docs/ppt_design_guide.md` — PPT 设计指南
- [x] `docs/video_script.md` — 视频脚本

---

## P4 — 深度对比发现的缺失项

### 13. Admin API 路由未接入
- `backend/app/api/admin_api.py` 已完整实现（373行，含仪表盘 + BGM CRUD），但 **未在 `routes.py` 中导入和注册**
- [x] 在 `routes.py` 中添加 `from app.api.admin_api import router as admin_router`
- [x] 添加 `router.include_router(admin_router, tags=["admin"])`
- [x] 验证 `/admin` 页面可正常访问

### 14. `/research` 白皮书路由缺失
- NoteRx 在 `/research` 路由提供研究白皮书页面
- TiktokRx 有 `docs/whitepaper.md` 但无 HTTP 路由
- [x] 将 whitepaper.md 核心内容转为 `docs/research_whitepaper.html`（102行完整HTML）
- [x] 在 `main.py` 添加 `/research` 路由指向该 HTML
- [x] 着陆页 Footer 已有「研究白皮书」链接（上一轮完成）

### 15. `image_vision_prep.py` 缺失
- [x] 创建 `backend/app/analysis/image_vision_prep.py`（从 NoteRx 移植，JPEG 压缩 + 等比缩小）
- 功能：`jpeg_bytes_for_vision()` — 将任意图片转为 RGB JPEG，控制体积供多模态 LLM 使用

### 16. `mimo_video.py` 缺失
- [x] 创建 `backend/app/analysis/mimo_video.py`（从 NoteRx 移植，MiMo 视频 URL content part 构建）
- 功能：`build_mimo_video_url_content_part()` — 构造 MiMo 视频理解 API 请求体

### 17. GitHub Actions CI 缺失
- [x] 创建 `.github/workflows/ci.yml`
- 包含：Python 后端 import 检查、前端 TypeScript 类型检查 + Vite 构建

### 18. 研究流水线脚本缺失
- [x] 创建 `scripts/` 目录结构
- [x] 移植 `compute_baseline.py` — 从 diagnosis_history 计算品类基线指标
- 注：完整 11 步研究流水线（数据导入/统计分析/模型训练）为专项工具，按需移植

---

## P5 — 着陆页内容模块补充（优先级：高）

> 对照 NoteRx `research_whitepaper.html`（692行）与 TiktokRx `landing.html`（322行），缺失大量数据驱动内容模块。

### 当前着陆页对比

| 模块 | NoteRx `research_whitepaper.html` | TiktokRx `landing.html` |
|------|------|------|
| Hero + 统计数字动画 | ✅ 4个计数器 | ✅ **已实现** — 数字递增动画 |
| 「不是拍脑袋，是数据说了算」| ✅ About 区块 | ✅ **已实现** — 三特性卡片 + 引用块 |
| 「研究过程」5步时间线 | ✅ 完整流程图 | ✅ **已实现** — 5步时间线（适配抖音数据） |
| 「工作原理：四阶段诊断引擎」| ✅ 4阶段卡片 + 技术名词 + 关键数字 | ✅ **已增强** — 4卡片 + 技术名词 + 5关键数字 |
| 「我们发现了这些秘密」| ✅ 8个数据发现卡片 | ✅ **已实现** — 8张卡片（BGM 38.3%、穿搭 R²=0.017 等） |
| 「每个品类的DNA都不一样」| ✅ 品类对比表 + 权重柱状图 | ✅ **已实现** — 品类对比表 + 5品类权重柱状图 |
| 「大模型发现了什么」| ✅ 5个品类LLM发现卡片 | ✅ **已实现** — 5品类标签药丸 + LLM 结论 |
| 「研究图表」| ✅ 4张 base64 研究图表 | ✅ **已实现** — 2×2 网格占位（待生成实际图表） |
| 「评论区的六种人」| ✅ 评论画像（6种用户类型） | ✅ **已实现** — 6种人格卡片 + 示例 + 占比 |
| 「评分模型验证」| ✅ 预测 vs 实际散点图 | ✅ **已实现** — 4张验证数据卡片 |
| 「冷知识」| ✅ 数据冷知识卡片 | ✅ **已实现** — 7条冷知识卡片 |
| 「即时体验评分」| ✅ 内联 demo 评分函数（JS） | ✅ **已实现** — 6滑块 + 品类切换 + 实时评分 |
| 「数据来源与工作量」| ✅ 数据采集详情 + 工程量 | ✅ **已实现** — 数据卡片 + 技术架构 |
| 「开源与论文」| ✅ GitHub + 论文 + 数据集链接 | ✅ **已实现** — 3个按钮 + `/research` 路由 |
| Sticky CTA（滚动后固定） | ✅ | ✅ **已实现** — IntersectionObserver |
| Launch 动画过渡 | ✅ 全屏渐变过渡 | ✅ **已实现** — cyan→pink 渐变 |
| 滚动渐显动画 | ✅ IntersectionObserver | ✅ **已实现** — `.rv` class + revealed |

### 19. 「不是拍脑袋，是数据说了算」模块
- [x] 在 `#about` 区块添加 About 内容
- [x] 标题：「不是拍脑袋，是数据说了算」
- [x] 内容：说明抖医是基于真实数据训练的 6 AI Agent 多轮辩论诊断系统
- [x] 三张特性卡片：双轨分析（统计 + LLM）、6 Agent 辩论、品类差异化
- [x] 引用块：8880+ 视频 + 6782 评论 + 850 BGM 数据支撑

### 20. 「研究过程」5 步时间线模块
- [x] 在 About 后添加「研究过程」区块
- [x] 5 步时间线：数据采集 → 统计建模 → LLM 分析 → 模型构建 → 验证
- [x] 底部数据来源声明框

### 21. 「工作原理：四阶段诊断引擎」模块增强
- [x] 升级为 4 阶段卡片布局（`dark-sec` 深色背景区块）
- [x] 添加技术名词标注 + 关键数字（8880+/5/6/3/<50ms）
- [x] 与周围内容形成视觉对比

### 22. 「我们发现了这些秘密」模块
- [x] 8 个数据发现卡片（BGM 38.3%、黄金时段、穿搭 R²=0.017、旅行 β=-0.51 等）
- [x] 底部引用块

### 23. 「每个品类的DNA都不一样」模块
- [x] 品类对比数据表格（6 列 × 5 行）
- [x] 5 个品类的权重柱状图（美食/穿搭/科技/旅行/生活）

### 24. 「大模型发现了什么」模块
- [x] 5 个品类卡片 + 标签药丸 + LLM 结论文字
- [x] 底部引用块

### 25. 「研究图表」模块
- [x] 2×2 网格布局（Spearman 热力图、回归系数、箱线图、模型验证占位卡片）

### 26. 「评论区的六种人」模块
- [x] 6 种评论人格卡片（种草/经验/质疑/凑热闹/求链接/求助）+ 占比 + 示例评论

### 27. 「评分模型验证」模块
- [x] 4 张验证数据卡片（训练规模/分类数据/评分一致性/统计显著性）

### 28. 「冷知识」模块
- [x] 7 条冷知识卡片（BGM 4.7 倍差距、适度优化 > 重度优化、感叹号反效果等）

### 29. 「即时体验评分」交互 Demo 模块
- [x] 品类选择器 + 6 维度滑块 + 实时评分（S/A/B/C/D）+ 级别描述
- [x] JS 实现：`MP` 权重对象 + `updateDemo()` 函数，数据来自 `research_data.py`

### 30. 「数据来源与工作量」模块
- [x] 数据采集卡片 + 工程量卡片 + 4 张技术栈卡片

### 31. 「开源与论文」模块
- [x] 3 个按钮（源代码/白皮书/即刻体验）
- [x] Footer 添加「研究白皮书」链接

### 32. 着陆页交互增强
- [x] Sticky CTA 按钮 — IntersectionObserver 检测 Hero 可见性
- [x] Launch 动画过渡 — 全屏 cyan→pink 渐变
- [x] 滚动渐显动画 — `.rv` class + IntersectionObserver
- [x] Hero 数字动画 — 从 0 递增到目标值（1.5s 缓动）
- [x] 导航栏锚点增强 — 添加 关于我们/数据发现/品类DNA/即时体验 锚点

---

## TiktokRx 已有 vs NoteRx 对照

| 功能 | TiktokRx | NoteRx | 说明 |
|------|----------|--------|------|
| 着陆页 | ✅ | ✅ | 风格不同，都含 visit 追踪 |
| 访问追踪 `/api/visit` | ✅ | ✅ | visit_api.py |
| 管理后台 `/admin` | ⚠️ | ✅ | **文件存在但未接入路由** |
| SSE 流式诊断 | ✅ | ✅ | diagnose-stream |
| 多 Agent 辩论 | ✅ 6个 | ✅ 4个 | TiktokRx 多 BGM Agent |
| 雷达图 | ✅ | ✅ | RadarChart.tsx |
| 基线对比 | ✅ | ✅ | BaselineComparison.tsx |
| 模拟评论区 | ✅ | ✅ | SimulatedComments.tsx |
| 优化建议 | ✅ | ✅ | SuggestionList.tsx |
| 诊断卡片导出 | ✅ | ✅ | DiagnoseCard.tsx |
| 错误边界 | ✅ | ✅ | ErrorBoundary.tsx |
| Toast 通知 | ✅ | ✅ | Toast.tsx |
| 公告弹窗 | ✅ | ✅ | AnnouncementDialog.tsx |
| 诊断历史 | ✅ | ✅ | History.tsx + IndexedDB |
| 截图分析 | ✅ | ✅ | ScreenshotAnalysis.tsx |
| 用户认证 | ✅ | ❌ | TiktokRx 独有 |
| 跨设备同步 | ✅ | ❌ | TiktokRx 独有 |
| BGM 分析 | ✅ | ❌ | TiktokRx 独有 |
| 纯文字分析 | ✅ | ❌ | TiktokRx 独有 |
| 隐私政策 | ✅ | ✅ | 已完成 |
| 服务条款 | ✅ | ✅ | 已完成 |
| README.md | ✅ | ✅ | 已完成 |
| .env.example | ✅ | ✅ | 已完成 |
| start.sh | ✅ | ✅ | 已完成 |
| Makefile | ✅ | ✅ | 已完成 |
| 部署脚本 | ✅ | ✅ | 已完成 |
| 顶部导航栏 | ✅ | ✅ | 已完成 |
| 研究白皮书路由 `/research` | ❌ | ✅ | **需补齐** |
| image_vision_prep.py | ❌ | ✅ | **需补齐** |
| mimo_video.py | ❌ | ✅ | **需补齐** |
| GitHub Actions CI | ❌ | ✅ | **需补齐** |
| 研究流水线脚本 | ❌ | ✅ | **需补齐** |
| 「不是拍脑袋」模块 | ❌ | ✅ | **需补齐** |
| 「研究过程」时间线 | ❌ | ✅ | **需补齐** |
| 「四阶段引擎」增强 | ❌ | ✅ | **需补齐** |
| 「我们发现了这些秘密」| ❌ | ✅ | **需补齐** |
| 「每个品类的DNA」| ❌ | ✅ | **需补齐** |
| 「大模型发现了什么」| ❌ | ✅ | **需补齐** |
| 「研究图表」| ❌ | ✅ | **需补齐** |
| 「评论区的六种人」| ❌ | ✅ | **需补齐** |
| 「评分模型验证」| ❌ | ✅ | **需补齐** |
| 「冷知识」| ❌ | ✅ | **需补齐** |
| 「即时体验评分」Demo | ❌ | ✅ | **需补齐** |
| 「数据来源与工作量」| ❌ | ✅ | **需补齐** |
| 「开源与论文」| ❌ | ✅ | **需补齐** |
| Sticky CTA / 动画 | ❌ | ✅ | **需补齐** |

---

## 统计

| 优先级 | 任务数 | 状态 |
|--------|--------|------|
| P0 | 3 | ✅ 全部完成 |
| P1 | 4 | ✅ 全部完成 |
| P2 | 3 | ✅ 全部完成 |
| P3 | 2 | ✅ 全部完成 |
| P4 | 6 | ✅ 全部完成 |
| P5 | 14 | ✅ 全部完成 |
| **合计** | **32** | **✅ 32/32** |
