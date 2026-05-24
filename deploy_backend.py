#!/usr/bin/env python3
"""
抖医 TiktokRx 生产部署脚本
构建前端 → 启动 FastAPI 服务（含静态文件）
"""
import subprocess
import sys
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT, "frontend")
BACKEND_DIR = os.path.join(ROOT, "backend")
DIST_DIR = os.path.join(FRONTEND_DIR, "dist")


def run(cmd, cwd=None):
    """运行命令并检查返回值"""
    print(f"  → {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or ROOT)
    if result.returncode != 0:
        print(f"  ✗ 命令失败 (exit {result.returncode})")
        sys.exit(result.returncode)


def build_frontend():
    """构建前端"""
    print("\n[1/3] 构建前端...")
    if os.path.isdir(os.path.join(FRONTEND_DIR, "node_modules")):
        run("npm run build", cwd=FRONTEND_DIR)
    else:
        print("  安装前端依赖...")
        run("npm install", cwd=FRONTEND_DIR)
        run("npm run build", cwd=FRONTEND_DIR)

    if not os.path.isdir(DIST_DIR):
        print("  ✗ 前端构建失败：dist 目录不存在")
        sys.exit(1)
    print("  ✓ 前端构建完成")


def install_backend_deps():
    """安装后端依赖"""
    print("\n[2/3] 检查后端依赖...")
    venv_dir = os.path.join(BACKEND_DIR, "venv")
    if not os.path.isdir(venv_dir):
        print("  创建虚拟环境...")
        run(f"{sys.executable} -m venv venv", cwd=BACKEND_DIR)

    # 激活 venv 并安装
    if os.name == "nt":
        pip = os.path.join(venv_dir, "Scripts", "pip")
    else:
        pip = os.path.join(venv_dir, "bin", "pip")
    run(f"{pip} install -r requirements.txt", cwd=BACKEND_DIR)
    print("  ✓ 后端依赖就绪")


def start_server(port=8000, host="0.0.0.0"):
    """启动生产服务器"""
    print(f"\n[3/3] 启动服务器 ({host}:{port})...")
    print(f"  前端静态文件: {DIST_DIR}")
    print(f"  后端 API: http://{host}:{port}/api/")
    print(f"  着陆页: http://{host}:{port}/")
    print(f"  产品页: http://{host}:{port}/app/")
    print()

    if os.name == "nt":
        uvicorn = os.path.join(BACKEND_DIR, "venv", "Scripts", "uvicorn")
    else:
        uvicorn = os.path.join(BACKEND_DIR, "venv", "bin", "uvicorn")

    run(f"{uvicorn} app.main:app --host {host} --port {port}", cwd=BACKEND_DIR)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="抖医 TiktokRx 生产部署")
    parser.add_argument("--port", type=int, default=8000, help="服务端口 (默认 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认 0.0.0.0)")
    parser.add_argument("--skip-build", action="store_true", help="跳过前端构建")
    parser.add_argument("--skip-deps", action="store_true", help="跳过依赖安装")
    args = parser.parse_args()

    print("=" * 50)
    print("  抖医 TiktokRx — 生产部署")
    print("=" * 50)

    if not args.skip_build:
        build_frontend()
    else:
        print("\n[1/3] 跳过前端构建")

    if not args.skip_deps:
        install_backend_deps()
    else:
        print("\n[2/3] 跳过依赖安装")

    start_server(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
