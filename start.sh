#!/bin/bash
# 抖医 TiktokRx 一键启动脚本
# 同时启动后端 (FastAPI) 和前端 (Vite dev server)

set -e

# 颜色定义
CYAN='\033[0;36m'
PINK='\033[0;35m'
NC='\033[0m'

echo -e "${CYAN}━━━ 抖医 TiktokRx 启动 ━━━${NC}"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 检查后端 venv
if [ ! -d "$SCRIPT_DIR/backend/venv" ]; then
  echo -e "${PINK}[!] 后端虚拟环境不存在，正在创建...${NC}"
  cd "$SCRIPT_DIR/backend"
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  cd "$SCRIPT_DIR"
fi

# 检查 frontend node_modules
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
  echo -e "${PINK}[!] 前端依赖未安装，正在安装...${NC}"
  cd "$SCRIPT_DIR/frontend"
  npm install
  cd "$SCRIPT_DIR"
fi

# 清理函数
cleanup() {
  echo ""
  echo -e "${CYAN}正在停止服务...${NC}"
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
  echo -e "${CYAN}已停止。${NC}"
  exit 0
}

trap cleanup SIGINT SIGTERM

# 启动后端
echo -e "${CYAN}[1/2] 启动后端 (port 8000)...${NC}"
cd "$SCRIPT_DIR/backend"
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
uvicorn app.main:app --port 8000 --reload &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# 启动前端
echo -e "${CYAN}[2/2] 启动前端 (port 5173)...${NC}"
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  前端: ${PINK}http://localhost:5173/app/${NC}"
echo -e "  后端: ${PINK}http://127.0.0.1:8000${NC}"
echo -e "  着陆页: ${PINK}http://localhost:5173/${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "按 Ctrl+C 停止所有服务"

wait
