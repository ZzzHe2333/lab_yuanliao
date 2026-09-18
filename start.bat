@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title 实验室原料管理系统 - 启动器

echo ========================================
echo        实验室原料管理系统
echo        Vue + Python / FastAPI
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 未检测到 Python。建议安装 Python 3.11 或更高版本，并勾选 Add Python to PATH。
  pause
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo [错误] 未检测到 Node.js。请安装 Node.js LTS。
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] 创建 Python 虚拟环境...
  python -m venv .venv
  if errorlevel 1 goto :fail
)

echo [2/4] 检查 Python 依赖...
if not exist ".venv\.deps-ok" (
  ".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
  if errorlevel 1 goto :fail
  type nul > ".venv\.deps-ok"
)

echo [3/4] 检查前端依赖...
if not exist "frontend\node_modules" (
  pushd frontend
  call npm install
  if errorlevel 1 (popd & goto :fail)
  popd
)

echo [4/4] 启动服务...
start "LabYuanliao-Backend" /D "%~dp0backend" cmd /k "..\.venv\Scripts\python.exe run.py"
start "LabYuanliao-Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

timeout /t 3 >nul
start "" "http://127.0.0.1:5173"

echo.
echo 前端: http://127.0.0.1:5173
echo 后端: http://127.0.0.1:8000
echo API文档: http://127.0.0.1:8000/docs
echo 数据目录: %~dp0data  ^(已被 Git 忽略^)
echo.
echo 可以关闭本启动器窗口；后端和前端会在各自窗口继续运行。
exit /b 0

:fail
echo.
echo [错误] 初始化或启动失败，请查看上方错误信息。
pause
exit /b 1
