# 🚀 Quick Start Guide

Hướng dẫn nhanh để bắt đầu sử dụng AI Video Generator.

## ⚡ Cài đặt nhanh

### 1. Clone và cài đặt
```bash
git clone <repository-url>
cd hl-create-video-AI
pip install -r requirements.txt
```

### 2. Chạy ứng dụng
```bash
python run.py
```

Hoặc chạy trực tiếp:
```bash
streamlit run app.py
```

## 🎯 Sử dụng cơ bản

### Bước 1: Tạo Script
1. Mở ứng dụng tại `http://localhost:8501`
2. Nhập ý tưởng video vào ô "Nhập ý tưởng video"
3. Nhấn "🚀 Tạo Script"
4. Xem script được tạo trong các tab

### Bước 2: Tạo Ảnh
1. Chuyển sang tab "🖼️ Tạo Ảnh"
2. Chọn provider ảnh (Pollinations miễn phí)
3. Nhấn "🎨 Tạo Ảnh"
4. Xem ảnh được tạo

### Bước 3: Tạo Video
1. Chuyển sang tab "🎬 Tạo Video"
2. Cấu hình thời lượng và hiệu ứng
3. Tạo voice over (tùy chọn)
4. Nhấn "🎬 Tạo Video"
5. Tải video về

## 🔑 API Keys (Tùy chọn)

### OpenAI API (Khuyến nghị)
- Đăng ký tại: https://platform.openai.com/
- Set biến môi trường: `export OPENAI_API_KEY="your-key"`
- Dùng cho: Script generation, ảnh DALL-E

### Stability AI API (Tùy chọn)
- Đăng ký tại: https://platform.stability.ai/
- Set biến môi trường: `export STABILITY_API_KEY="your-key"`
- Dùng cho: Ảnh chất lượng cao

### Không cần API Key
- **Pollinations AI**: Tạo ảnh miễn phí
- **Edge TTS**: Tạo giọng nói miễn phí

## 📝 Ví dụ Prompt

### Cinematic
```
"Một cuộc phiêu lưu kỳ thú trong rừng rậm với những con vật biết nói, ánh sáng vàng chiếu qua tán lá"
```

### Documentary
```
"Cuộc sống hàng ngày của một gia đình ở vùng nông thôn Việt Nam, từ bình minh đến hoàng hôn"
```

### Educational
```
"Quá trình phát triển của một cây từ hạt giống đến cây trưởng thành, với các giai đoạn sinh trưởng"
```

### Animation
```
"Thế giới kỳ diệu của những chú robot nhỏ trong thành phố tương lai, với màu sắc tươi sáng"
```

## 🎨 Cấu hình nâng cao

### Video Effects
- **ken_burns**: Zoom + pan mượt mà (khuyến nghị)
- **zoom_in**: Phóng to dần
- **zoom_out**: Thu nhỏ dần
- **pan_left/right**: Di chuyển ngang

### Voice Options
- **vi-VN-HoaiMyNeural**: Giọng nữ Việt Nam
- **vi-VN-NamMinhNeural**: Giọng nam Việt Nam
- **en-US-AriaNeural**: Giọng nữ tiếng Anh

### Image Sizes
- **1024x1024**: Vuông, phù hợp mọi loại video
- **1792x1024**: Rộng, phù hợp landscape
- **1024x1792**: Cao, phù hợp portrait

## 🐛 Xử lý lỗi thường gặp

### Lỗi "Module not found"
```bash
pip install -r requirements.txt
```

### Lỗi "API key not found"
- Kiểm tra biến môi trường
- Hoặc nhập trực tiếp trong sidebar

### Lỗi "Permission denied"
```bash
chmod +x run.py
```

### Video không có âm thanh
- Kiểm tra file audio có tồn tại
- Thử tạo lại voice over

## 📊 Tips tối ưu

### Để có video chất lượng tốt:
1. Sử dụng prompt chi tiết cho ảnh
2. Chọn hiệu ứng Ken Burns cho chuyển động mượt
3. Thêm voice over để tăng tính chuyên nghiệp
4. Sử dụng ảnh kích thước 1024x1024

### Để tiết kiệm chi phí:
1. Dùng Pollinations AI cho ảnh (miễn phí)
2. Dùng Edge TTS cho voice (miễn phí)
3. Chỉ dùng OpenAI cho script generation
4. Tạo video ngắn (2-3 cảnh)

## 🎬 Ví dụ hoàn chỉnh

```python
# Tạo video "Cuộc phiêu lưu trong rừng"
prompt = "Một cuộc phiêu lưu kỳ thú trong rừng rậm với những con vật biết nói"

# Cấu hình:
# - 3 cảnh
# - Phong cách cinematic  
# - Ảnh Pollinations (miễn phí)
# - Voice Edge TTS (miễn phí)
# - Hiệu ứng Ken Burns
# - Thời lượng 3 giây/cảnh

# Kết quả: Video MP4 9 giây với voice over tiếng Việt
```

## 📞 Hỗ trợ

- 📖 Đọc README.md để biết chi tiết
- 🐛 Báo lỗi trên GitHub Issues
- 💡 Đề xuất tính năng mới

---

**Chúc bạn tạo được những video tuyệt vời! 🎬✨**
