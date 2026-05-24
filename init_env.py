#!/usr/bin/env python3
"""初始化项目环境：创建虚拟环境并安装依赖"""
import subprocess
import sys
import os

def run(cmd, cwd=None):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Failed: {cmd}")
        sys.exit(1)

def main():
    # 创建后端虚拟环境
    if not os.path.exists("backend/venv"):
        run("python -m venv backend/venv")

    # 安装后端依赖
    run("backend/venv/Scripts/pip install -r backend/requirements.txt")

    # 安装前端依赖
    if not os.path.exists("frontend/node_modules"):
        run("npm install", cwd="frontend")

    print("环境初始化完成！")

if __name__ == "__main__":
    main()
