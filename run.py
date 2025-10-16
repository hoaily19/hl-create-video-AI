#!/usr/bin/env python3
"""
Quick start script for AI Video Generator
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Kiểm tra dependencies"""
    try:
        import streamlit
        import openai
        import PIL
        import moviepy
        print("✅ Tất cả dependencies đã được cài đặt")
        return True
    except ImportError as e:
        print(f"❌ Thiếu dependency: {e}")
        print("Vui lòng chạy: pip install -r requirements.txt")
        return False

def setup_directories():
    """Tạo các thư mục cần thiết"""
    dirs = [
        "outputs/images",
        "outputs/videos", 
        "outputs/audio",
        "outputs/scripts",
        "outputs/projects",
        "logs",
        "temp"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Đã tạo các thư mục cần thiết")

def check_api_keys():
    """Kiểm tra API keys"""
    openai_key = os.getenv('OPENAI_API_KEY')
    stability_key = os.getenv('STABILITY_API_KEY')
    
    if not openai_key:
        print("⚠️  Chưa set OPENAI_API_KEY (cần cho script generation)")
    else:
        print("✅ OpenAI API key đã được set")
    
    if not stability_key:
        print("ℹ️  Chưa set STABILITY_API_KEY (có thể dùng Pollinations miễn phí)")
    else:
        print("✅ Stability API key đã được set")

def main():
    """Hàm chính"""
    print("🎬 AI Video Generator - Quick Start")
    print("=" * 50)
    
    # Kiểm tra dependencies
    if not check_dependencies():
        return
    
    # Tạo thư mục
    setup_directories()
    
    # Kiểm tra API keys
    check_api_keys()
    
    print("\n🚀 Khởi động ứng dụng...")
    print("Ứng dụng sẽ mở tại: http://localhost:8501")
    print("Nhấn Ctrl+C để dừng")
    
    try:
        # Chạy Streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Đã dừng ứng dụng")

if __name__ == "__main__":
    main()
