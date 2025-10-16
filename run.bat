@echo off
echo 🎬 AI Video Generator - Quick Start
echo ====================================

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python chưa được cài đặt hoặc không có trong PATH
    echo Vui lòng cài đặt Python từ https://python.org
    pause
    exit /b 1
)

REM Kiểm tra pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip chưa được cài đặt
    pause
    exit /b 1
)

REM Cài đặt dependencies nếu cần
echo 📦 Kiểm tra dependencies...
pip install -r requirements.txt

REM Tạo thư mục cần thiết
if not exist "outputs" mkdir outputs
if not exist "outputs\images" mkdir outputs\images
if not exist "outputs\videos" mkdir outputs\videos
if not exist "outputs\audio" mkdir outputs\audio
if not exist "outputs\scripts" mkdir outputs\scripts
if not exist "outputs\projects" mkdir outputs\projects
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp

echo ✅ Đã chuẩn bị xong
echo.
echo 🚀 Khởi động ứng dụng...
echo Ứng dụng sẽ mở tại: http://localhost:8501
echo Nhấn Ctrl+C để dừng
echo.

REM Chạy ứng dụng
python run.py

pause
