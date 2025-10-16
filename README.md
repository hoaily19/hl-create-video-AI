# 🎬 AI Video Generator

Tạo video từ ý tưởng của bạn bằng AI - Script, Ảnh, Voice và Video hoàn chỉnh!

## ✨ Tính năng

### 🎬 Tạo Video AI
- 🤖 **Tạo Script tự động** bằng GPT/Gemini từ ý tưởng của bạn
- 🖼️ **Sinh ảnh AI** từ nhiều provider (OpenAI DALL-E, Stability AI, Pollinations, Replicate, HuggingFace)
- 🎤 **Tạo giọng đọc** bằng TTS (Edge TTS, OpenAI TTS, Google TTS, Azure Speech, ElevenLabs)
- 🎬 **Tạo video** với hiệu ứng chuyển động (Ken Burns, zoom, pan, fade)
- 🎵 **Ghép nhạc nền** và voice over
- 📊 **Quản lý dự án** và xuất file

### 📁 Quản lý File
- 📤 **Tải kịch bản** từ file JSON/TXT
- 📋 **File mẫu kịch bản** - Template JSON để chỉnh sửa
- 🖼️ **Tải ảnh hàng loạt** để sử dụng thay vì tạo mới
- 🎵 **Test giọng nói** trước khi tạo video
- 📥 **Tải xuống kịch bản** (JSON/TXT) sau khi tạo
- 📥 **Tải xuống ảnh** (riêng lẻ hoặc ZIP) sau khi tạo
- 📥 **Tải âm thanh xuống** để sử dụng riêng
- 🗑️ **Xóa kịch bản/ảnh/video** để dọn dẹp và tiết kiệm dung lượng

### 🧪 Test & Debug
- 🔍 **Test API Keys** để kiểm tra kết nối
- 📊 **API Status** hiển thị trạng thái thực tế
- 🎵 **Test Voice** để nghe thử giọng nói
- 🔧 **Debug Info** để kiểm tra session state

### 🌊 Tích hợp
- 🌊 **Google Flow** - Chuyển dữ liệu sang Google Flow
- 📱 **Responsive UI** - Giao diện thân thiện
- 🎨 **Custom Styling** - Giao diện đẹp mắt

## 🚀 Cài đặt

### 1. Clone repository
```bash
git clone <repository-url>
cd hl-create-video-AI
```

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```
### 3. Lệnh chạy
```bash
python -m streamlit run app.py --server.port 8502 --server.address localhost
```
#### Thư viện chính:
- **streamlit** - Web UI framework
- **openai** - OpenAI API client
- **google-generativeai** - Google Gemini API
- **azure-cognitiveservices-speech** - Azure Speech Service
- **edge-tts** - Microsoft Edge TTS
- **gtts** - Google Text-to-Speech
- **requests** - HTTP requests
- **pillow** - Image processing
- **moviepy** - Video editing
- **psutil** - System utilities
- **pathlib** - File path handling

### 3. Thiết lập API Keys (tùy chọn)

**🔑 Bảng Cấu hình API Keys trong ứng dụng:**
- Mở ứng dụng → Sidebar "⚙️ Cấu hình" → "🔑 Bảng Cấu hình API Keys"
- Nhập API keys trực tiếp trong giao diện
- Click "💾 Lưu Tất Cả API Keys" để lưu
- Test API keys bằng nút "🧪 Test"

**🆓 Miễn phí:**
- Google Gemini (Script) - Cần API key
- Edge TTS (Voice) - Không cần API key  
- Pollinations AI (Image) - Không cần API key
- MoviePy (Video) - Không cần API key

**💰 Trả phí (chất lượng cao hơn):**
- OpenAI GPT (Script) - `OPENAI_API_KEY`
- Stability AI (Image) - `STABILITY_API_KEY`
- ElevenLabs (Voice) - `ELEVENLABS_API_KEY`
- Azure Speech (Voice) - `AZURE_SPEECH_KEY`

**📖 Chi tiết:** Xem [API_SETUP_GUIDE.md](API_SETUP_GUIDE.md)
```

**Lưu ý:** 
- Bạn có thể sử dụng **Pollinations AI** (miễn phí) cho ảnh mà không cần API key
- Bạn có thể sử dụng **Edge TTS** (miễn phí) cho giọng nói mà không cần API key
- **Google Gemini** cung cấp miễn phí cho script generation

## 🎯 Sử dụng

### Chạy ứng dụng Streamlit
```bash
streamlit run app.py
```

### Sử dụng từng module riêng lẻ

#### 1. Tạo Script
```python
from modules.script_generator import ScriptGenerator

generator = ScriptGenerator(api_key="your-openai-key")
scenes = generator.generate_script(
    prompt="Một cuộc phiêu lưu kỳ thú trong rừng rậm",
    num_scenes=3,
    style="cinematic"
)
```

#### 2. Tạo Ảnh
```python
from modules.image_generator import ImageGenerator

generator = ImageGenerator("pollinations")  # Miễn phí
image_path = generator.generate_image(
    prompt="Beautiful sunset over mountains, cinematic style",
    output_path="outputs/images/scene_1.png"
)
```

#### 3. Tạo Video
```python
from modules.video_maker import VideoMaker

maker = VideoMaker()
video_path = maker.create_video_from_images(
    image_paths=["scene_1.png", "scene_2.png"],
    output_path="outputs/videos/final_video.mp4",
    scene_durations=[3, 3],
    effects=["ken_burns", "zoom_in"]
)
```

#### 4. Tạo Voice
```python
from modules.voice_generator import VoiceGenerator

generator = VoiceGenerator("edge")  # Miễn phí
audio_path = generator.generate_voice(
    text="Xin chào, đây là giọng đọc tiếng Việt",
    output_path="outputs/audio/voice.mp3",
    voice="vi-VN-HoaiMyNeural"
)
```

## 📂 Cấu trúc dự án

```
hl-create-video-AI/
│
├── app.py                         # Ứng dụng Streamlit chính
├── requirements.txt               # Dependencies
├── README.md                     # Hướng dẫn này
│
├── modules/                      # Các module chính
│   ├── script_generator.py       # Tạo script bằng GPT
│   ├── image_generator.py        # Tạo ảnh từ prompt
│   ├── video_maker.py            # Tạo video từ ảnh
│   ├── voice_generator.py        # Tạo giọng đọc TTS
│   └── utils.py                  # Hàm phụ trợ
│
├── assets/                       # Tài nguyên
│   ├── music/                    # Nhạc nền
│   ├── fonts/                    # Font chữ
│   └── templates/                # Template video
│
├── outputs/                      # Kết quả đầu ra
│   ├── images/                   # Ảnh được tạo
│   ├── videos/                   # Video hoàn chỉnh
│   ├── audio/                    # File audio
│   ├── scripts/                  # Script JSON
│   └── projects/                 # Dự án đã lưu
│
└── logs/                         # Log files
```

## 🎨 Các Provider được hỗ trợ

### Image Generation
- **Pollinations AI** (miễn phí) - Khuyến nghị cho test
- **OpenAI DALL-E 3** (trả phí) - Chất lượng cao
- **Stability AI** (trả phí) - Tùy chỉnh nhiều

### Voice Generation
- **Edge TTS** (miễn phí) - Hỗ trợ tiếng Việt tốt
- **OpenAI TTS** (trả phí) - Chất lượng cao
- **Google TTS** (miễn phí) - Đơn giản

### Script Generation
- **OpenAI GPT-4o-mini** (trả phí) - Chất lượng tốt, giá rẻ

## 🎬 Hiệu ứng Video

- **Ken Burns**: Zoom + pan tạo chuyển động mượt mà
- **Zoom In**: Phóng to dần vào ảnh
- **Zoom Out**: Thu nhỏ dần từ ảnh
- **Pan Left/Right**: Di chuyển ngang
- **Fade**: Chuyển cảnh mờ dần

## 🔧 Cấu hình

Tạo file `config.json` để cấu hình mặc định:

```json
{
  "openai_api_key": "",
  "stability_api_key": "",
  "default_image_provider": "pollinations",
  "default_voice_provider": "edge",
  "default_voice": "vi-VN-HoaiMyNeural",
  "video_fps": 24,
  "video_resolution": [1920, 1080],
  "scene_duration": 3.0,
  "transition_duration": 0.5,
  "output_quality": "high"
}
```

## 🚀 Ví dụ sử dụng

### Tạo video hoàn chỉnh từ prompt

```python
from modules.script_generator import ScriptGenerator
from modules.image_generator import ImageGenerator
from modules.video_maker import VideoMaker
from modules.voice_generator import VoiceGenerator

# 1. Tạo script
script_gen = ScriptGenerator("your-openai-key")
scenes = script_gen.generate_script("Một cuộc phiêu lưu trong rừng rậm", 3)

# 2. Tạo ảnh
img_gen = ImageGenerator("pollinations")
image_paths = []
for i, scene in enumerate(scenes):
    path = f"outputs/images/scene_{i+1}.png"
    img_gen.generate_image(scene['image_prompt'], path)
    image_paths.append(path)

# 3. Tạo voice
voice_gen = VoiceGenerator("edge")
voice_paths = voice_gen.generate_voice_for_scenes(scenes)
combined_voice = voice_gen.combine_audio_files(voice_paths, "outputs/audio/voice.mp3")

# 4. Tạo video
video_maker = VideoMaker()
video_path = video_maker.create_video_from_images(
    image_paths,
    "outputs/videos/final_video.mp4",
    voice_over=combined_voice
)

print(f"Video đã tạo: {video_path}")
```

## 🎯 Tích hợp Google Flow (Tương lai)

Hiện tại Google Flow chưa có API công khai, nhưng khi có thể tích hợp:

```python
# modules/flow_api.py (tương lai)
def animate_image_with_flow(image_path):
    # Gọi Google Flow API để tạo chuyển động
    pass
```

## 🐛 Xử lý lỗi

Ứng dụng có hệ thống xử lý lỗi thông minh:

- **Rate Limit**: Tự động thông báo và gợi ý thử lại
- **API Key**: Kiểm tra và thông báo lỗi API key
- **Network**: Xử lý lỗi kết nối mạng
- **File**: Kiểm tra và tạo file placeholder khi cần

## 📝 Logs

Logs được lưu trong thư mục `logs/`:
- `app.log`: Log chính của ứng dụng
- Tự động xoay log khi file quá lớn

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/) - GPT và DALL-E
- [Stability AI](https://stability.ai/) - Stable Diffusion
- [Pollinations AI](https://pollinations.ai/) - Miễn phí image generation
- [Edge TTS](https://github.com/rany2/edge-tts) - Miễn phí TTS
- [MoviePy](https://zulko.github.io/moviepy/) - Video processing
- [Streamlit](https://streamlit.io/) - Web UI

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra logs trong thư mục `logs/`
2. Đảm bảo đã cài đặt đầy đủ dependencies
3. Kiểm tra API keys và kết nối mạng
4. Tạo issue trên GitHub với thông tin chi tiết

---

**Chúc bạn tạo được những video tuyệt vời! 🎬✨**
