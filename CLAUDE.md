# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install all dependencies (backend venv + frontend npm)
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd frontend && npm install

# Initialize database (tables auto-created on startup via lifespan)
cd backend && source venv/bin/activate && python -c "from app.main import _ensure_history_table; _ensure_history_table()"

# Start backend (port 8002)
cd backend && source venv/bin/activate && uvicorn app.main:app --port 8002 --reload

# Start frontend (port 5173)
cd frontend && npm run dev

# Frontend + backend together
cd frontend && npm run dev:all

# Production: build frontend then serve from backend
cd frontend && npm run build
cd backend && source venv/bin/activate && uvicorn app.main:app --port 8002

# Frontend type check + build
cd frontend && npx tsc --noEmit && npx vite build

# Run backend tests
cd backend && pytest tests/ -v
```

## Architecture

抖医 (TiktokRx) is a TikTok content diagnosis platform. Users upload content (video file, images, or text), and 5-6 AI agents analyze it through a multi-round debate via SSE streaming.

### Content Types

| Type | Input | Dimensions | Agents |
|------|-------|------------|--------|
| 短视频 (video) | 视频文件上传 | 6维 | 6 (Content+Visual+Growth+UserSim+Judge+BGM) |
| 图文 (image+text) | 图片+文字 | 5维 | 5 (no BGM) |
| 纯文字 (pure_text) | 纯文本 | 5维 | 5 (no BGM) |
| BGM分析 | 音频/歌曲名 | 独立评分 | BGMAgent |

### 6-Dimension Scoring (视频)

1. **content_quality** - 文案质量（标题、钩子、信息密度）
2. **visual_performance** - 视觉表现（封面、第一帧）
3. **bgm_adaptation** - BGM适配度（热度、节奏匹配）
4. **growth_strategy** - 增长策略（标签、发布时间）
5. **user_resonance** - 用户共鸣（评论区预测）
6. **technical_performance** - 技术表现（画质、剪辑节奏）

### 5-Dimension Scoring (图文/纯文字)

无 bgm_adaptation 维度，其余相同。

### Multi-Agent Flow (backend/app/agents/orchestrator.py)

```
Input → TextAnalyzer / ImageAnalyzer
     → BaselineComparator (SQLite tiktok_baseline.db)
     → Round 1: 5 agents diagnose in parallel (asyncio.gather)
        ContentAgent | VisualAgent | GrowthAgent | UserSimAgent | BGMAgent (if video)
     → Round 2: Each agent debates others' opinions
     → Round 3: JudgeAgent synthesizes final report
```

SSE events are pushed from `api/diagnose.py` → `diagnose_stream()`. Frontend maps events to 12 steps via `EVENT_STEP_MAP` in `Diagnosing.tsx`.

### BGM Heat Levels

| Level | Threshold | Traffic Boost |
|-------|-----------|---------------|
| S+ | 100万+ | +30% |
| S | 50-100万 | +20% |
| A | 10-50万 | +15% |
| B | 1-10万 | +5% |
| C | <1万 | 0% |

### Model Tiers (configured in backend/.env)

Three models via Xiaomi MiMo API (OpenAI-compatible):
- `LLM_MODEL_PRO` (mimo-v2-pro) — 1M context, all agent diagnosis + debate + judging
- `LLM_MODEL_OMNI` (mimo-v2-omni) — multimodal, OCR/image/video analysis
- `LLM_MODEL_FAST` (mimo-v2-flash) — quick tasks (comments, labels)

`base_agent.py` handles MiMo gateway quirks: `max_completion_tokens` instead of `max_tokens`, fallback when `response_format=json_object` is unsupported, proxy bypass via `trust_env=False`.

### Frontend-Backend Connection

- **Dev mode**: Vite dev middleware directly serves static HTML pages (`docs/*.html`) for `/`, `/paper`, `/research`, `/terms`, `/privacy`. Proxy forwards `/api/*` and `/health` to backend.
- **Production**: FastAPI serves the built SPA via `SPAMiddleware` — all non-`/api` routes fall through to `index.html`. Static pages excluded via `STATIC_ROUTES` set.
- Frontend proxy target: `VITE_API_PROXY_TARGET` in `frontend/.env.development` (default `http://localhost:8002`).

### Database

SQLite at `backend/data/tiktok_baseline.db`. Tables:

**Core:**
- **diagnosis_history** — diagnosis records with `input_type` and optional `user_id`
- **baseline_stats** — per-category baselines (seeded at startup, static)
- **bgm_database** — 850 BGM with heat levels (S+/S/A/B/C)
- **text_baseline** / **comment_baseline** / **publish_time_baseline** / **title_baseline** / **tag_baseline** — per-category statistical baselines

**Analytics (real-time writes):**
- **usage_log** — every diagnosis request (IP, tokens, duration, status)
- **visit_log** — every page visit (visitor hash, path)

**Auth/Sync:**
- **users** — user accounts (username, email, password_hash)
- **user_devices** — multi-device support
- **sync_log** — cross-device sync records

### Key API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/diagnose` | Main diagnosis (multipart, supports video/image/text) |
| POST | `/api/diagnose-stream` | SSE streaming diagnosis |
| POST | `/api/pre-score` | Instant deterministic pre-score (no LLM) |
| POST | `/api/generate-comments` | Simulated comments (flash model) |
| POST | `/api/analyze-text` | Pure text analysis |
| POST | `/api/analyze-bgm` | BGM heat/adaptation/traffic prediction |
| GET | `/api/bgm-hot` | Hot BGM list |
| GET | `/api/baseline/{category}` | Category baseline stats |
| POST | `/api/screenshot/deep-analyze` | Screenshot deep analysis |
| POST | `/api/optimize` | Generate optimization plan |
| POST | `/api/visit` | Track page visit |
| GET | `/admin` | Admin dashboard (auto-refresh 30s) |
| GET | `/admin/api/stats` | Admin stats (password-protected) |

### Frontend Stack

React 19 + TypeScript + MUI v9 + Vite (base: `/app/`). Framer Motion for page transitions. ECharts for radar chart. html2canvas for export. Axios for API calls.

### Theme

TikTok dark mode: `#121212` background, primary cyan `#25f4ee`, secondary pink `#fe2c55`.

Pages: Home (upload) → Diagnosing (SSE streaming, 12 steps) → Report (radar, dimensions, baseline comparison, export card).

## Configuration

Copy `backend/env.example` to `backend/.env`. Key vars:
- `OPENAI_API_KEY` / `OPENAI_BASE_URL` — API credentials (or `ANTHROPIC_API_KEY`)
- `LLM_MODEL_FAST` / `LLM_MODEL_PRO` / `LLM_MODEL_OMNI` — model names per tier
- `LLM_PROVIDER` — `openai` (default) or `anthropic`
- `MAX_VIDEO_UPLOAD_MB` — max video size (default 300)
- `VIDEO_STT_ENABLED` — enable Whisper STT for video audio extraction

The `_is_mimo_openai_compat()` function in `base_agent.py` auto-detects MiMo gateway from URL or model name.
