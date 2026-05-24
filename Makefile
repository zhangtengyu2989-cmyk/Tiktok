.PHONY: install dev build data test clean

# 安装所有依赖
install:
	cd backend && python -m venv venv && source venv/Scripts/activate 2>/dev/null || source venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

# 启动开发环境（后端 + 前端）
dev:
	python start_project.py

# 仅启动后端
backend:
	cd backend && source venv/Scripts/activate 2>/dev/null || source venv/bin/activate && uvicorn app.main:app --port 8000 --reload

# 仅启动前端
frontend:
	cd frontend && npm run dev

# 构建前端
build:
	cd frontend && npm run build

# 初始化数据库
data:
	cd backend && source venv/Scripts/activate 2>/dev/null || source venv/bin/activate && python -c "from app.main import _ensure_history_table; _ensure_history_table()"

# 运行前端类型检查
check:
	cd frontend && npx tsc --noEmit

# 清理构建产物
clean:
	rm -rf frontend/dist
	rm -rf backend/data/temp_videos/*
