#!/usr/bin/env python3
"""一键启动项目（后端 + 前端）"""
import subprocess
import sys
import os

def main():
    # 启动后端
    print("启动后端...")
    backend_proc = subprocess.Popen(
        "backend/venv/Scripts/python -m uvicorn app.main:app --port 8002 --reload",
        shell=True,
        cwd=os.path.join(os.path.dirname(__file__), "backend")
    )

    # 启动前端
    print("启动前端...")
    frontend_proc = subprocess.Popen(
        "npm run dev",
        shell=True,
        cwd=os.path.join(os.path.dirname(__file__), "frontend")
    )

    print("\n服务已启动:")
    print("  前端: http://localhost:5173/app/")
    print("  后端: http://127.0.0.1:8002")
    print("\n按 Ctrl+C 停止所有服务")

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        backend_proc.terminate()
        frontend_proc.terminate()
        print("\n已停止所有服务")

if __name__ == "__main__":
    main()
