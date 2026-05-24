# TiktokRx 一键部署脚本 (Windows Server)
# 使用方式: 右键 -> 使用 PowerShell 运行，或管理员 PowerShell 中执行:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\deploy.ps1

$ErrorActionPreference = "Stop"
$PROJECT_DIR = "C:\Users\Administrator\Downloads\Tiktok\Tiktok"
$PORT = 8002

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TiktokRx 一键部署脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ── Step 1: 检查 Node.js ──
Write-Host "`n[1/6] 检查 Node.js..." -ForegroundColor Yellow
try {
    $nodeVer = node --version
    Write-Host "  Node.js $nodeVer 已安装" -ForegroundColor Green
} catch {
    Write-Host "  未检测到 Node.js，请先安装: https://nodejs.org" -ForegroundColor Red
    exit 1
}

# ── Step 2: 检查 Python ──
Write-Host "`n[2/6] 检查 Python..." -ForegroundColor Yellow
try {
    $pyVer = python --version
    Write-Host "  $pyVer 已安装" -ForegroundColor Green
} catch {
    Write-Host "  未检测到 Python，请先安装: https://python.org" -ForegroundColor Red
    exit 1
}

# ── Step 3: 安装后端依赖 ──
Write-Host "`n[3/6] 安装后端依赖..." -ForegroundColor Yellow
Set-Location "$PROJECT_DIR\backend"

if (-not (Test-Path "venv")) {
    Write-Host "  创建虚拟环境..." -ForegroundColor Gray
    python -m venv venv
}

& "venv\Scripts\activate.ps1"
pip install -r requirements.txt --quiet
Write-Host "  后端依赖安装完成" -ForegroundColor Green

# ── Step 4: 构建前端 ──
Write-Host "`n[4/6] 构建前端..." -ForegroundColor Yellow
Set-Location "$PROJECT_DIR\frontend"
npm install --silent
npm run build
Write-Host "  前端构建完成" -ForegroundColor Green

# ── Step 5: 配置环境变量 ──
Write-Host "`n[5/6] 配置环境变量..." -ForegroundColor Yellow
Set-Location "$PROJECT_DIR\backend"
if (-not (Test-Path ".env")) {
    Copy-Item "env.example" ".env"
    Write-Host "  已创建 .env 文件，请编辑填入 API Key:" -ForegroundColor Green
    Write-Host "  $PROJECT_DIR\backend\.env" -ForegroundColor Cyan
    Write-Host "  需要填写: OPENAI_API_KEY, OPENAI_BASE_URL" -ForegroundColor Yellow
} else {
    Write-Host "  .env 已存在，跳过" -ForegroundColor Green
}

# ── Step 6: 启动服务 ──
Write-Host "`n[6/6] 启动服务..." -ForegroundColor Yellow

# 检查端口是否已被占用
$existing = Get-NetTCPConnection -LocalPort $PORT -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "  端口 $PORT 已被占用，正在关闭旧进程..." -ForegroundColor Yellow
    $pid = (Get-NetTCPConnection -LocalPort $PORT).OwningProcess | Select-1
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# 检查是否有旧的 uvicorn 进程
$oldUvicorn = Get-Process uvicorn -ErrorAction SilentlyContinue
if ($oldUvicorn) {
    Write-Host "  关闭旧的 uvicorn 进程..." -ForegroundColor Yellow
    Stop-Process -Name uvicorn -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Host "  启动 uvicorn..." -ForegroundColor Gray
$backendDir = "$PROJECT_DIR\backend"
$uvicornExe = "$backendDir\venv\Scripts\uvicorn.exe"
Start-Process -WindowStyle Hidden -FilePath $uvicornExe -ArgumentList "app.main:app --host 0.0.0.0 --port $PORT" -WorkingDirectory $backendDir

Start-Sleep -Seconds 3

# 验证服务是否启动
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:$PORT/api/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "  服务启动成功!" -ForegroundColor Green
} catch {
    Write-Host "  服务启动中，请稍候..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# ── 完成 ──
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  部署完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  访问地址:" -ForegroundColor White
Write-Host "  http://localhost:$PORT" -ForegroundColor Cyan
Write-Host "  http://你的服务器IP:$PORT" -ForegroundColor Cyan
Write-Host ""
Write-Host "  管理命令:" -ForegroundColor White
Write-Host "  查看进程:  Get-Process uvicorn" -ForegroundColor Gray
Write-Host "  停止服务:  Stop-Process -Name uvicorn" -ForegroundColor Gray
Write-Host "  重启服务:  重新运行此脚本" -ForegroundColor Gray
Write-Host ""
Write-Host "  ⚠️  记得在防火墙/安全组放行端口 $PORT" -ForegroundColor Yellow
Write-Host ""
