# 🔑 Hướng dẫn thiết lập API Keys

## 📋 Tổng quan

AI Video Generator hỗ trợ nhiều nhà cung cấp API khác nhau. Bạn có thể sử dụng miễn phí hoặc trả phí tùy theo nhu cầu.

## 🆓 Dịch vụ MIỄN PHÍ

### ✅ Không cần API Key
- **Edge TTS**: Text-to-Speech miễn phí của Microsoft
- **Google TTS**: Text-to-Speech miễn phí của Google  
- **Pollinations AI**: Tạo ảnh miễn phí
- **MoviePy**: Tạo video miễn phí

### 🔑 Cần API Key (Miễn phí)
- **Google Gemini**: Tạo kịch bản miễn phí
  - Link: https://makersuite.google.com/app/apikey
  - Hướng dẫn: Đăng nhập Google → Create API Key

## 💰 Dịch vụ TRẢ PHÍ

### 🤖 Script Generation
- **OpenAI GPT**: $0.002/1K tokens
  - Link: https://platform.openai.com/api-keys
  - Hướng dẫn: Đăng ký → Billing → Create API Key

### 🖼️ Image Generation  
- **OpenAI DALL-E**: $0.04/ảnh
- **Stability AI**: $0.004/ảnh
  - Link: https://platform.stability.ai/account/keys
- **Replicate**: $0.01-0.05/ảnh
  - Link: https://replicate.com/account/api-tokens

### 🎤 Voice Generation
- **Azure Speech**: $4/1M characters
  - Link: https://portal.azure.com/
- **ElevenLabs**: $5/tháng (1M characters)
  - Link: https://elevenlabs.io/app/settings/api-keys
- **OpenAI TTS**: $0.015/1K characters

### 🎬 Motion Generation
- **Google Flow**: $0.10/video
- **RunwayML**: $12/tháng
  - Link: https://runwayml.com/

## 🚀 Cách sử dụng

### 1. Mở ứng dụng
```bash
streamlit run app.py
```

### 2. Vào phần "⚙️ Cấu hình" trong sidebar

### 3. Nhập API Keys
- Điền vào bảng "🔑 Bảng Cấu hình API Keys"
- Click "💾 Lưu Tất Cả API Keys"

### 4. Test API Keys
- Click các nút "🧪 Test" để kiểm tra
- Xem trạng thái trong bảng "📊 Trạng thái API Keys"

## 💡 Gợi ý cấu hình

### 🆓 Cấu hình MIỄN PHÍ
```
Google Gemini: ✅ (Tạo kịch bản)
Edge TTS: ✅ (Giọng đọc)
Pollinations: ✅ (Tạo ảnh)
MoviePy: ✅ (Tạo video)
```

### 💰 Cấu hình TRẢ PHÍ (Chất lượng cao)
```
OpenAI GPT: ✅ (Kịch bản tốt hơn)
Stability AI: ✅ (Ảnh chất lượng cao)
ElevenLabs: ✅ (Giọng đọc tự nhiên)
Google Flow: ✅ (Motion chuyên nghiệp)
```

## ⚠️ Lưu ý bảo mật

- ✅ **AN TOÀN**: Nhập API keys trực tiếp trong ứng dụng
- ✅ **AN TOÀN**: Keys được lưu local, không gửi lên server
- ❌ **NGUY HIỂM**: Không commit API keys vào Git
- ❌ **NGUY HIỂM**: Không chia sẻ API keys với người khác

## 🔧 Xử lý lỗi

### Lỗi 403 (Edge TTS)
```bash
pip install -U edge-tts
```

### Lỗi 429 (Quota exceeded)
- Kiểm tra billing account
- Nâng cấp plan hoặc đợi reset quota

### Lỗi 401 (Unauthorized)
- Kiểm tra API key đúng chưa
- Kiểm tra API key còn hạn không

## 📞 Hỗ trợ

Nếu gặp vấn đề, hãy:
1. Kiểm tra API key trong bảng trạng thái
2. Test API key bằng nút test
3. Xem log lỗi chi tiết
4. Thử provider khác (fallback tự động)
