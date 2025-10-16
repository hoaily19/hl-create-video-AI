# 🔑 Hướng dẫn API Keys

Hướng dẫn chi tiết về cách lấy và sử dụng API keys cho các AI services.

## 📋 Danh sách API Keys được hỗ trợ

### 🤖 Script Generation

#### 1. OpenAI API
- **Mô tả**: GPT models cho script generation
- **Website**: https://platform.openai.com/
- **Pricing**: Pay per use ($0.0015/1K tokens cho GPT-4o-mini)
- **Free tier**: $5 credit khi đăng ký

**Cách lấy API key:**
1. Đăng ký tài khoản tại https://platform.openai.com/
2. Vào Settings > API Keys
3. Tạo API key mới
4. Copy và lưu key (bắt đầu với `sk-`)

#### 2. Anthropic Claude (Tương lai)
- **Mô tả**: Claude models cho script generation
- **Website**: https://console.anthropic.com/
- **Pricing**: Pay per use
- **Free tier**: Limited

#### 3. Google Gemini (Tương lai)
- **Mô tả**: Gemini models cho script generation
- **Website**: https://makersuite.google.com/
- **Pricing**: Free tier generous
- **Free tier**: 60 requests/minute

### 🖼️ Image Generation

#### 1. Pollinations AI (Miễn phí)
- **Mô tả**: Free image generation
- **Website**: https://pollinations.ai/
- **Pricing**: Hoàn toàn miễn phí
- **API Key**: Không cần

#### 2. OpenAI DALL-E
- **Mô tả**: High-quality image generation
- **Website**: https://platform.openai.com/
- **Pricing**: $0.040/image (1024x1024)
- **API Key**: Cùng với OpenAI API key

#### 3. Stability AI
- **Mô tả**: Stable Diffusion models
- **Website**: https://platform.stability.ai/
- **Pricing**: $0.004/image
- **Free tier**: 25 credits khi đăng ký

**Cách lấy API key:**
1. Đăng ký tại https://platform.stability.ai/
2. Vào Account > API Keys
3. Tạo API key mới
4. Copy và lưu key

#### 4. Replicate
- **Mô tả**: Various AI models
- **Website**: https://replicate.com/
- **Pricing**: Pay per use
- **Free tier**: $10 credit

**Cách lấy API key:**
1. Đăng ký tại https://replicate.com/
2. Vào Account > API Tokens
3. Tạo token mới
4. Copy token (bắt đầu với `r8_`)

#### 5. Hugging Face
- **Mô tả**: Open source AI models
- **Website**: https://huggingface.co/
- **Pricing**: Free/Paid
- **Free tier**: Generous

**Cách lấy API key:**
1. Đăng ký tại https://huggingface.co/
2. Vào Settings > Access Tokens
3. Tạo token mới
4. Copy token (bắt đầu với `hf_`)

### 🎤 Voice Generation

#### 1. Edge TTS (Miễn phí)
- **Mô tả**: Microsoft Edge TTS
- **Website**: https://github.com/rany2/edge-tts
- **Pricing**: Hoàn toàn miễn phí
- **API Key**: Không cần

#### 2. OpenAI TTS
- **Mô tả**: High-quality text-to-speech
- **Website**: https://platform.openai.com/
- **Pricing**: $0.015/1K characters
- **API Key**: Cùng với OpenAI API key

#### 3. Google TTS
- **Mô tả**: Google Text-to-Speech
- **Website**: https://cloud.google.com/text-to-speech
- **Pricing**: Free tier available
- **API Key**: Không cần (cho gTTS)

## ⚙️ Cách thiết lập API Keys

### Phương pháp 1: Trong ứng dụng Streamlit
1. Mở ứng dụng: `streamlit run app.py`
2. Vào sidebar > API Keys
3. Chọn tab tương ứng (Script/Image/Voice)
4. Nhập API key vào ô input
5. Key sẽ được lưu tự động

### Phương pháp 2: Environment Variables
```bash
# Windows
set OPENAI_API_KEY=your_openai_key_here
set STABILITY_API_KEY=your_stability_key_here

# Linux/Mac
export OPENAI_API_KEY=your_openai_key_here
export STABILITY_API_KEY=your_stability_key_here
```

### Phương pháp 3: File config.json
```json
{
  "api_keys": {
    "openai": "sk-your_openai_key_here",
    "stability": "your_stability_key_here",
    "replicate": "r8_your_replicate_key_here",
    "huggingface": "hf_your_hf_key_here"
  }
}
```

## 💰 Chi phí ước tính

### Script Generation
- **OpenAI GPT-4o-mini**: ~$0.0015/1K tokens
- **Ví dụ**: 1 script 3 cảnh ≈ $0.01-0.02

### Image Generation
- **Pollinations**: Miễn phí
- **OpenAI DALL-E**: $0.040/image
- **Stability AI**: $0.004/image
- **Ví dụ**: 3 ảnh ≈ $0.12 (DALL-E) hoặc $0.012 (Stability)

### Voice Generation
- **Edge TTS**: Miễn phí
- **OpenAI TTS**: $0.015/1K characters
- **Ví dụ**: 1 video 30 giây ≈ $0.01-0.02

### Tổng chi phí cho 1 video
- **Chỉ dùng miễn phí**: $0 (Pollinations + Edge TTS)
- **Premium**: $0.15-0.20/video (OpenAI cho tất cả)

## 🔒 Bảo mật API Keys

### ✅ Nên làm:
- Lưu API keys trong file config.json (không commit vào git)
- Sử dụng environment variables
- Thường xuyên rotate API keys
- Monitor usage và billing

### ❌ Không nên:
- Hardcode API keys trong code
- Commit API keys vào git repository
- Chia sẻ API keys qua email/chat
- Sử dụng API keys trên public repositories

## 🚀 Khuyến nghị cho người mới

### Bắt đầu miễn phí:
1. **Script**: Sử dụng template fallback (không cần API key)
2. **Image**: Pollinations AI (miễn phí)
3. **Voice**: Edge TTS (miễn phí)

### Nâng cấp khi cần:
1. **Script**: OpenAI API ($5 free credit)
2. **Image**: Stability AI (25 free credits)
3. **Voice**: Giữ Edge TTS (đủ tốt)

### Premium setup:
1. **Script**: OpenAI GPT-4o-mini
2. **Image**: OpenAI DALL-E 3
3. **Voice**: OpenAI TTS

## 🛠️ Troubleshooting

### Lỗi "API key not found"
- Kiểm tra API key đã được nhập chưa
- Kiểm tra format API key (sk-, r8_, hf_)
- Restart ứng dụng sau khi thêm API key

### Lỗi "Rate limit exceeded"
- Chờ một lúc rồi thử lại
- Kiểm tra usage limits trong dashboard
- Upgrade plan nếu cần

### Lỗi "Invalid API key"
- Kiểm tra API key có đúng không
- Tạo API key mới
- Kiểm tra API key chưa expired

### Lỗi "Insufficient credits"
- Kiểm tra balance trong dashboard
- Thêm credits vào account
- Chuyển sang provider khác

## 📞 Hỗ trợ

- **OpenAI**: https://help.openai.com/
- **Stability AI**: https://support.stability.ai/
- **Replicate**: https://replicate.com/docs
- **Hugging Face**: https://huggingface.co/docs

---

**Lưu ý**: Giá cả có thể thay đổi, vui lòng kiểm tra website chính thức để có thông tin mới nhất.
