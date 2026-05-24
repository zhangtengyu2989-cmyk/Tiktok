#!/bin/bash
# 启动后端服务
cd backend && source venv/Scripts/activate && uvicorn app.main:app --port 8002 --reload
