"""
AI Video Generator - Main Application
Ứng dụng chính để tạo video từ prompt sử dụng AI
"""

import streamlit as st
import os
import sys
import json
import time
import datetime
import shutil
from pathlib import Path

# Thêm modules vào path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.script_generator import ScriptGenerator
from modules.image_generator import ImageGenerator
from modules.video_maker import VideoMaker
from modules.voice_generator import VoiceGenerator
from modules.motion_generator import MotionGenerator
from modules.flow_integration import FlowIntegration
from modules.veo3_integration import VEO3Integration, extract_cookie_from_browser
from modules.google_flow_integration import GoogleFlowIntegration, extract_bearer_token_from_cookie
from modules.file_manager import FileManager
from modules.api_manager import api_manager
from modules.utils import (
    ConfigManager, ProjectManager, ProgressTracker, 
    DataValidator, ErrorHandler, setup_logging
)

# Thiết lập trang
st.set_page_config(
    page_title="🎬 AI Video Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Thiết lập logging
setup_logging()

# CSS tùy chỉnh
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .step-header {
        color: #FF6B6B;
        border-bottom: 2px solid #FF6B6B;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .info-box {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #4ECDC4;
        margin: 10px 0;
    }
    .success-box {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #4ECDC4;
        margin: 10px 0;
    }
    .metric-container {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

def create_api_keys_section():
    """Tạo phần cấu hình API Keys"""
    st.markdown("### ⚙️ Cấu hình")
    
    # Đọc API keys từ config.json
    import json
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        config_keys = config.get('api_keys', {})
    except:
        config_keys = {}
    
    # Chỉ hiển thị các API keys đã có trong config
    available_keys = {
        "google": ("🤖 Google Gemini", "Script Generation", "Miễn phí", "https://makersuite.google.com/app/apikey"),
        "openai": ("🤖 OpenAI", "Script/Image/Voice", "Trả phí", "https://platform.openai.com/api-keys"),
        "stability": ("🖼️ Stability AI", "Image Generation", "Trả phí", "https://platform.stability.ai/account/keys"),
        "elevenlabs": ("🎤 ElevenLabs", "Voice Generation", "Trả phí", "https://elevenlabs.io/app/settings/api-keys"),
        "google_flow": ("🎬 Google Flow", "Motion Generation", "Trả phí", "https://aistudio.google.com/")
    }
    
    # Lọc chỉ những keys có trong config
    active_keys = {k: v for k, v in available_keys.items() if k in config_keys}
    
    # API Status Dashboard
    st.markdown("**📊 API Status**")
    
    # Tạo status compact
    status_cols = st.columns(min(len(active_keys), 4))
    for i, (provider, (name, purpose, cost, link)) in enumerate(active_keys.items()):
        with status_cols[i % len(status_cols)]:
            current_key = api_manager.get_api_key(provider) or config_keys.get(provider, "")
            has_key = bool(current_key and current_key.strip())
            
            if has_key:
                st.success(f"✅ {name.split(' ', 1)[1].replace('AI', '').replace('Google', 'G').replace('OpenAI', 'OAI')}")
            else:
                st.warning(f"⚠️ {name.split(' ', 1)[1].replace('AI', '').replace('Google', 'G').replace('OpenAI', 'OAI')}")
    
    # API Keys Management
    with st.expander("🔧 API Keys Management", expanded=True):
        with st.form("api_keys_form"):
            st.markdown("**Nhập API Keys:**")
            
            # Tạo columns cho inputs
            cols = st.columns(2)
            key_inputs = {}
            
            for i, (provider, (name, purpose, cost, link)) in enumerate(active_keys.items()):
                col_idx = i % 2
                with cols[col_idx]:
                    current_key = api_manager.get_api_key(provider) or config_keys.get(provider, "")
                    key_inputs[provider] = st.text_input(
                        name.split(' ', 1)[1],
                        value=current_key,
                        type="password",
                        help=f"{purpose} - {cost}",
                        key=f"key_{provider}"
                    )
            
            # Action buttons
            col_save, col_load, col_clear = st.columns(3)
            
            with col_save:
                save_keys = st.form_submit_button("💾 Lưu Keys", type="primary", width='stretch')
            
            with col_load:
                load_config = st.form_submit_button("🔄 Load Config", type="secondary", width='stretch')
            
            with col_clear:
                clear_keys = st.form_submit_button("🗑️ Xóa Keys", type="secondary", width='stretch')
            
            if save_keys:
                saved_count = 0
                for provider, key in key_inputs.items():
                    if key and key.strip():
                        api_manager.set_api_key(provider, key.strip())
                        saved_count += 1
                
                if saved_count > 0:
                    st.success(f"✅ Đã lưu {saved_count} API keys!")
                else:
                    st.warning("⚠️ Không có API key nào được nhập")
            
            if load_config:
                for provider in active_keys.keys():
                    config_key = config_keys.get(provider, "")
                    if config_key:
                        api_manager.set_api_key(provider, config_key)
                st.success("✅ Đã load API keys từ config.json!")
            
            if clear_keys:
                for provider in active_keys.keys():
                    api_manager.set_api_key(provider, "")
                st.success("✅ Đã xóa tất cả API keys!")
    
    # Test API Keys
    st.markdown("**🧪 Test API Keys**")
    
    test_cols = st.columns(min(len(active_keys), 3))
    for i, (provider, (name, purpose, cost, link)) in enumerate(active_keys.items()):
        col_idx = i % len(test_cols)
        with test_cols[col_idx]:
            current_key = api_manager.get_api_key(provider) or config_keys.get(provider, "")
            has_key = bool(current_key and current_key.strip())
            
            if has_key:
                button_type = "primary"
                button_text = f"🧪 {name.split(' ', 1)[1].replace('AI', '').replace('Google', 'G').replace('OpenAI', 'OAI')}"
            else:
                button_type = "secondary"
                button_text = f"⚠️ {name.split(' ', 1)[1].replace('AI', '').replace('Google', 'G').replace('OpenAI', 'OAI')}"
            
            if st.button(button_text, type=button_type, width='stretch', key=f"test_{provider}"):
                if has_key:
                    try:
                        if provider == "google":
                            from modules.script_generator import ScriptGenerator
                            script_gen = ScriptGenerator()
                            result = script_gen.generate_script("Test", "google", 1, "cinematic", False, False, "general", "short")
                            if result and result.get('scenes'):
                                st.success("✅ Google Gemini OK!")
                            else:
                                st.error("❌ Google Gemini Error")
                        
                        elif provider == "openai":
                            import openai
                            client = openai.OpenAI(api_key=current_key)
                            response = client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[{"role": "user", "content": "Hello"}],
                                max_tokens=10
                            )
                            if response.choices:
                                st.success("✅ OpenAI OK!")
                            else:
                                st.error("❌ OpenAI Error")
                        
                        elif provider == "elevenlabs":
                            import requests
                            url = "https://api.elevenlabs.io/v1/voices"
                            headers = {"xi-api-key": current_key}
                            response = requests.get(url, headers=headers)
                            if response.status_code == 200:
                                st.success("✅ ElevenLabs OK!")
                            else:
                                st.error(f"❌ ElevenLabs Error: {response.status_code}")
                        
                        else:
                            st.info(f"✅ {name} OK!")
                            
                    except Exception as e:
                        st.error(f"❌ {name}: {str(e)[:30]}...")
                else:
                    st.warning(f"⚠️ No key for {name}")
    
    # Hướng dẫn lấy API Keys
    with st.expander("📖 Hướng dẫn lấy API Keys", expanded=False):
        st.markdown("### 🔑 Hướng dẫn chi tiết lấy API Keys")
        
        # Tabs cho từng loại API
        guide_tabs = st.tabs(["🤖 Script", "🖼️ Image", "🎤 Voice", "🎬 Motion"])
        
        with guide_tabs[0]:
            st.markdown("#### 🤖 Script Generation APIs")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Google Gemini (Miễn phí)**")
                st.markdown("""
                1. Truy cập: https://makersuite.google.com/app/apikey
                2. Đăng nhập Google account
                3. Click "Create API Key"
                4. Copy key và paste vào ô trên
                5. **Miễn phí**: 60 requests/phút
                """)
                
                if st.button("🔗 Mở Google Gemini", key="open_google"):
                    st.markdown("👉 [Truy cập Google Gemini](https://makersuite.google.com/app/apikey)")
            
            with col2:
                st.markdown("**OpenAI GPT (Trả phí)**")
                st.markdown("""
                1. Truy cập: https://platform.openai.com/api-keys
                2. Đăng nhập OpenAI account
                3. Click "Create new secret key"
                4. Copy key và paste vào ô trên
                5. **Chi phí**: $0.002/1K tokens
                """)
                
                if st.button("🔗 Mở OpenAI", key="open_openai"):
                    st.markdown("👉 [Truy cập OpenAI](https://platform.openai.com/api-keys)")
        
        with guide_tabs[1]:
            st.markdown("#### 🖼️ Image Generation APIs")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Stability AI (Trả phí)**")
                st.markdown("""
                1. Truy cập: https://platform.stability.ai/account/keys
                2. Đăng ký tài khoản
                3. Tạo API key mới
                4. Copy key và paste vào ô trên
                5. **Chi phí**: $0.004/ảnh
                """)
                
                if st.button("🔗 Mở Stability AI", key="open_stability"):
                    st.markdown("👉 [Truy cập Stability AI](https://platform.stability.ai/account/keys)")
            
            with col2:
                st.markdown("**Pollinations AI (Miễn phí)**")
                st.markdown("""
                1. Không cần API key
                2. Sử dụng trực tiếp
                3. **Miễn phí**: Không giới hạn
                4. Chất lượng tốt
                5. Tốc độ nhanh
                """)
                
                st.success("✅ Pollinations AI đã sẵn sàng!")
        
        with guide_tabs[2]:
            st.markdown("#### 🎤 Voice Generation APIs")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**ElevenLabs (Trả phí)**")
                st.markdown("""
                1. Truy cập: https://elevenlabs.io/app/settings/api-keys
                2. Đăng ký tài khoản
                3. Tạo API key mới
                4. Copy key và paste vào ô trên
                5. **Chi phí**: $5/tháng (1M characters)
                """)
                
                if st.button("🔗 Mở ElevenLabs", key="open_elevenlabs"):
                    st.markdown("👉 [Truy cập ElevenLabs](https://elevenlabs.io/app/settings/api-keys)")
            
            with col2:
                st.markdown("**Edge TTS (Miễn phí)**")
                st.markdown("""
                1. Không cần API key
                2. Sử dụng trực tiếp
                3. **Miễn phí**: Không giới hạn
                4. Chất lượng tốt
                5. Nhiều giọng đọc
                """)
                
                st.success("✅ Edge TTS đã sẵn sàng!")
        
        with guide_tabs[3]:
            st.markdown("#### 🎬 Motion Generation APIs")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Google Flow (Trả phí)**")
                st.markdown("""
                1. Truy cập: https://aistudio.google.com/
                2. Đăng nhập Google account
                3. Tạo API key mới
                4. Copy key và paste vào ô trên
                5. **Chi phí**: $0.10/video
                """)
                
                if st.button("🔗 Mở Google Flow", key="open_google_flow"):
                    st.markdown("👉 [Truy cập Google Flow](https://aistudio.google.com/)")
            
            with col2:
                st.markdown("**RunwayML (Trả phí)**")
                st.markdown("""
                1. Truy cập: https://runwayml.com/
                2. Đăng ký tài khoản
                3. Tạo API key mới
                4. Copy key và paste vào ô trên
                5. **Chi phí**: $12/tháng
                """)
                
                if st.button("🔗 Mở RunwayML", key="open_runwayml"):
                    st.markdown("👉 [Truy cập RunwayML](https://runwayml.com/)")
        
        # Tóm tắt chi phí
        st.markdown("---")
        st.markdown("### 💰 Tóm tắt chi phí")
        
        cost_cols = st.columns(2)
        
        with cost_cols[0]:
            st.markdown("**🆓 Miễn phí:**")
            st.markdown("""
            - Google Gemini (Script)
            - Edge TTS (Voice)
            - Pollinations AI (Image)
            - MoviePy (Video)
            """)
        
        with cost_cols[1]:
            st.markdown("**💰 Trả phí:**")
            st.markdown("""
            - OpenAI: $0.002/1K tokens
            - Stability AI: $0.004/ảnh
            - ElevenLabs: $5/tháng
            - Google Flow: $0.10/video
            """)
        
        # Lưu ý bảo mật
        st.markdown("---")
        st.markdown("### 🔒 Lưu ý bảo mật")
        st.warning("""
        ⚠️ **Quan trọng:**
        - Không chia sẻ API keys với người khác
        - Không commit keys vào Git
        - Keys được lưu local, an toàn
        - Có thể xóa keys bất kỳ lúc nào
        """)
    
    st.markdown("---")
    
    # Tabs cho các loại API
    api_tab1, api_tab2, api_tab3, api_tab4 = st.tabs(["Script", "Image", "Voice", "Motion"])
    
    with api_tab1:
        st.markdown("**Script Generation**")
        script_provider = st.selectbox(
            "Provider", 
            api_manager.get_available_providers("script"),
            index=0,
            key="script_provider"
        )
        
        if script_provider == "google":
            google_key = st.text_input("Google Gemini API Key", type="password", 
                                     value=api_manager.get_api_key("google") or "",
                                     key="google_key")
            if google_key and google_key != api_manager.get_api_key("google"):
                api_manager.set_api_key("google", google_key)
                st.success("✅ Google Gemini API key đã được lưu")
        
        if script_provider == "openai":
            openai_key = st.text_input("OpenAI API Key", type="password", 
                                     value=api_manager.get_api_key("openai") or "",
                                     key="openai_key")
            if openai_key and openai_key != api_manager.get_api_key("openai"):
                api_manager.set_api_key("openai", openai_key)
                st.success("✅ OpenAI API key đã được lưu")
    
    with api_tab2:
        st.markdown("**Image Generation**")
        image_provider = st.selectbox(
            "Provider", 
            api_manager.get_available_providers("image"),
            index=0,
            key="image_provider"
        )
        
        if image_provider == "openai":
            openai_key = st.text_input("OpenAI API Key", type="password", 
                                     value=api_manager.get_api_key("openai") or "",
                                     key="openai_key_image")
            if openai_key and openai_key != api_manager.get_api_key("openai"):
                api_manager.set_api_key("openai", openai_key)
                st.success("✅ OpenAI API key đã được lưu")
        
        if image_provider == "stability":
            stability_key = st.text_input("Stability AI API Key", type="password", 
                                        value=api_manager.get_api_key("stability") or "",
                                        key="stability_key")
            if stability_key and stability_key != api_manager.get_api_key("stability"):
                api_manager.set_api_key("stability", stability_key)
                st.success("✅ Stability AI API key đã được lưu")
    
    with api_tab3:
        st.markdown("**Voice Generation**")
        voice_provider = st.selectbox(
            "Provider", 
            api_manager.get_available_providers("voice"),
            index=0,
            key="voice_provider"
        )
        
        if voice_provider == "azure":
            azure_key = st.text_input("Azure Speech Service Key", type="password", 
                                    value=api_manager.get_api_key("azure") or "",
                                    key="azure_key_voice")
            if azure_key and azure_key != api_manager.get_api_key("azure"):
                api_manager.set_api_key("azure", azure_key)
                st.success("✅ Azure Speech Service API key đã được lưu")
        
        if voice_provider == "openai":
            openai_key = st.text_input("OpenAI API Key", type="password", 
                                     value=api_manager.get_api_key("openai") or "",
                                     key="openai_key_voice")
            if openai_key and openai_key != api_manager.get_api_key("openai"):
                api_manager.set_api_key("openai", openai_key)
                st.success("✅ OpenAI API key đã được lưu")
        
        if voice_provider == "elevenlabs":
            elevenlabs_key = st.text_input("ElevenLabs API Key", type="password", 
                                         value=api_manager.get_api_key("elevenlabs") or "",
                                         key="elevenlabs_key_voice")
            if elevenlabs_key and elevenlabs_key != api_manager.get_api_key("elevenlabs"):
                api_manager.set_api_key("elevenlabs", elevenlabs_key)
                st.success("✅ ElevenLabs API key đã được lưu")
    
    with api_tab4:
        st.markdown("**Motion Generation**")
        motion_provider = st.selectbox(
            "Provider", 
            api_manager.get_available_providers("motion"),
            index=0,
            key="motion_provider"
        )
        
        if motion_provider == "google_flow":
            google_flow_key = st.text_input("Google Flow API Key", type="password", 
                                          value=api_manager.get_api_key("google_flow") or "")
            if google_flow_key and google_flow_key != api_manager.get_api_key("google_flow"):
                api_manager.set_api_key("google_flow", google_flow_key)
                st.success("✅ Google Flow API key đã được lưu")
    
    # Test API Keys
    st.markdown("---")
    st.markdown("### 🧪 Test API Keys")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Test Script APIs", type="secondary"):
            test_script_apis()
    
    with col2:
        if st.button("🖼️ Test Image APIs", type="secondary"):
            test_image_apis()
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("🎤 Test Voice APIs", type="secondary"):
            test_voice_apis()
    
    with col4:
        if st.button("🎬 Test Motion APIs", type="secondary"):
            test_motion_apis()
    
    # API Status
    st.markdown("---")
    st.markdown("### 📊 API Status")
    
    # Tính toán API status thực tế
    total_apis = 0
    available_apis = 0
    free_apis = 0
    paid_apis = 0
    
    # Script APIs
    script_providers = api_manager.get_available_providers("script")
    total_apis += len(script_providers)
    for provider in script_providers:
        if provider == "google":
            available_apis += 1
            free_apis += 1
        elif provider in ["openai", "anthropic"]:
            if api_manager.get_api_key(provider):
                available_apis += 1
                paid_apis += 1
    
    # Image APIs
    image_providers = api_manager.get_available_providers("image")
    total_apis += len(image_providers)
    for provider in image_providers:
        if provider == "pollinations":
            available_apis += 1
            free_apis += 1
        elif provider in ["openai", "stability", "replicate", "huggingface"]:
            if api_manager.get_api_key(provider):
                available_apis += 1
                paid_apis += 1
    
    # Voice APIs
    voice_providers = api_manager.get_available_providers("voice")
    total_apis += len(voice_providers)
    for provider in voice_providers:
        if provider in ["edge", "gtts"]:
            available_apis += 1
            free_apis += 1
        elif provider in ["openai", "azure", "elevenlabs"]:
            if api_manager.get_api_key(provider):
                available_apis += 1
                paid_apis += 1
    
    # Motion APIs
    motion_providers = api_manager.get_available_providers("motion")
    total_apis += len(motion_providers)
    for provider in motion_providers:
        if provider == "free":
            available_apis += 1
            free_apis += 1
        elif provider in ["google_flow", "runwayml", "pika_labs", "leia_pix"]:
            if api_manager.get_api_key(provider):
                available_apis += 1
                paid_apis += 1
    
    # Hiển thị API Status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Available", available_apis)
    
    with col2:
        st.metric("Total", total_apis)
    
    with col3:
        st.metric("Free", free_apis)
    
    with col4:
        st.metric("Paid", paid_apis)

def test_script_apis():
    """Test script generation APIs"""
    st.info("🧪 Testing Script APIs...")
    
    try:
        from modules.script_generator import ScriptGenerator
        
        # Test Google Gemini (free)
        if api_manager.get_api_key("google"):
            try:
                generator = ScriptGenerator(provider="google")
                test_scenes = generator.generate_script("Test prompt", num_scenes=1, style="cinematic")
                if test_scenes:
                    st.success("✅ Google Gemini: Working")
                else:
                    st.error("❌ Google Gemini: Failed")
            except Exception as e:
                st.error(f"❌ Google Gemini: {str(e)[:100]}")
        else:
            st.warning("⚠️ Google Gemini: No API key")
        
        # Test OpenAI
        if api_manager.get_api_key("openai"):
            try:
                generator = ScriptGenerator(provider="openai")
                test_scenes = generator.generate_script("Test prompt", num_scenes=1, style="cinematic")
                if test_scenes:
                    st.success("✅ OpenAI: Working")
                else:
                    st.error("❌ OpenAI: Failed")
            except Exception as e:
                st.error(f"❌ OpenAI: {str(e)[:100]}")
        else:
            st.warning("⚠️ OpenAI: No API key")
            
    except Exception as e:
        st.error(f"❌ Script API Test Error: {e}")

def test_image_apis():
    """Test image generation APIs"""
    st.info("🧪 Testing Image APIs...")
    
    try:
        from modules.image_generator import ImageGenerator
        
        # Test Pollinations (free)
        try:
            generator = ImageGenerator(provider="pollinations")
            test_path = "temp/test_pollinations.png"
            os.makedirs("temp", exist_ok=True)
            result = generator.generate_image("test image", test_path, "1024x1024")
            if os.path.exists(result):
                st.success("✅ Pollinations: Working")
                os.remove(result)  # Clean up
            else:
                st.error("❌ Pollinations: Failed")
        except Exception as e:
            st.error(f"❌ Pollinations: {str(e)[:100]}")
        
        # Test OpenAI
        if api_manager.get_api_key("openai"):
            try:
                generator = ImageGenerator(provider="openai")
                test_path = "temp/test_openai.png"
                result = generator.generate_image("test image", test_path, "1024x1024")
                if os.path.exists(result):
                    st.success("✅ OpenAI DALL-E: Working")
                    os.remove(result)  # Clean up
                else:
                    st.error("❌ OpenAI DALL-E: Failed")
            except Exception as e:
                st.error(f"❌ OpenAI DALL-E: {str(e)[:100]}")
        else:
            st.warning("⚠️ OpenAI DALL-E: No API key")
            
    except Exception as e:
        st.error(f"❌ Image API Test Error: {e}")

def test_voice_apis():
    """Test voice generation APIs"""
    st.info("🧪 Testing Voice APIs...")
    
    try:
        from modules.voice_generator import VoiceGenerator
        
        # Test Edge TTS (free)
        try:
            generator = VoiceGenerator(provider="edge")
            test_path = "temp/test_edge.mp3"
            os.makedirs("temp", exist_ok=True)
            result = generator.generate_voice("test", test_path, "vi-VN-HoaiMyNeural")
            if os.path.exists(result):
                st.success("✅ Edge TTS: Working")
                os.remove(result)  # Clean up
            else:
                st.error("❌ Edge TTS: Failed")
        except Exception as e:
            st.error(f"❌ Edge TTS: {str(e)[:100]}")
        
        # Test ElevenLabs
        if api_manager.get_api_key("elevenlabs"):
            try:
                generator = VoiceGenerator(provider="elevenlabs")
                test_path = "temp/test_elevenlabs.mp3"
                result = generator.generate_voice("test", test_path, "21m00Tcm4TlvDq8ikWAM")
                if os.path.exists(result):
                    st.success("✅ ElevenLabs: Working")
                    os.remove(result)  # Clean up
                else:
                    st.error("❌ ElevenLabs: Failed")
            except Exception as e:
                st.error(f"❌ ElevenLabs: {str(e)[:100]}")
        else:
            st.warning("⚠️ ElevenLabs: No API key")
            
    except Exception as e:
        st.error(f"❌ Voice API Test Error: {e}")

def test_motion_apis():
    """Test motion generation APIs"""
    st.info("🧪 Testing Motion APIs...")
    
    try:
        from modules.motion_generator import MotionGenerator
        
        # Test Free motion
        try:
            generator = MotionGenerator(provider="free")
            test_path = "temp/test_motion.mp4"
            os.makedirs("temp", exist_ok=True)
            result = generator.generate_motion("outputs/images/scene_01.png", test_path)
            if os.path.exists(result):
                st.success("✅ Free Motion: Working")
                os.remove(result)  # Clean up
            else:
                st.error("❌ Free Motion: Failed")
        except Exception as e:
            st.error(f"❌ Free Motion: {str(e)[:100]}")
        
        # Test Google Flow
        if api_manager.get_api_key("google_flow"):
            try:
                generator = MotionGenerator(provider="google_flow")
                st.success("✅ Google Flow: API key available")
            except Exception as e:
                st.error(f"❌ Google Flow: {str(e)[:100]}")
        else:
            st.warning("⚠️ Google Flow: No API key")
            
    except Exception as e:
        st.error(f"❌ Motion API Test Error: {e}")

def create_veo3_tab():
    """Tab VEO3 Video Generation"""
    st.markdown('<h2 class="step-header">🎬 VEO3 Video Generation</h2>', unsafe_allow_html=True)
    
    st.info("🎬 VEO3 là công cụ tạo video AI mạnh mẽ từ ảnh. Bạn có thể tạo video chuyển động từ ảnh đã tạo.")
    st.warning("⚠️ **Lưu ý:** VEO3 sử dụng cookie từ veo3.com, không phải Bearer Token từ Google Flow.")
    
    # Kiểm tra có ảnh không
    has_images = 'image_paths' in st.session_state and st.session_state.image_paths
    
    if not has_images:
        st.warning("⚠️ Vui lòng tạo ảnh trước khi sử dụng VEO3")
        return
    
    # Lấy dữ liệu
    scenes = st.session_state.get('scenes', st.session_state.get('saved_scenes', []))
    image_paths = st.session_state.image_paths
    
    st.success(f"✅ Sẵn sàng với {len(scenes)} cảnh và {len(image_paths)} ảnh")
    
    # VEO3 Cookie Input
    st.markdown("### 🔑 Cấu hình VEO3")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        veo3_cookie = st.text_area(
            "VEO3 Cookie",
            placeholder="Dán cookie từ VEO3 website vào đây...",
            help="Lấy cookie từ VEO3 website (F12 -> Application -> Cookies)",
            height=100
        )
    
    with col2:
        st.markdown("**Cách lấy cookie:**")
        st.markdown("""
        1. Mở VEO3.com
        2. Đăng nhập tài khoản
        3. F12 -> Application
        4. Cookies -> Copy tất cả
        5. Dán vào ô bên trái
        """)
    
    # Initialize VEO3
    if veo3_cookie:
        try:
            # Clean cookie
            clean_cookie = extract_cookie_from_browser(veo3_cookie)
            veo3 = VEO3Integration(clean_cookie)
            
            # Validate cookie
            if veo3.validate_cookie():
                st.success("✅ VEO3 Cookie hợp lệ!")
                
                # Video generation settings
                st.markdown("### ⚙️ Cài đặt Video")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    duration = st.slider("Thời lượng (giây)", 1, 10, 5)
                    style = st.selectbox("Phong cách", ["cinematic", "documentary", "artistic", "dramatic"])
                
                with col2:
                    quality = st.selectbox("Chất lượng", ["high", "medium", "low"])
                    fps = st.selectbox("FPS", [24, 30, 60])
                
                with col3:
                    resolution = st.selectbox("Độ phân giải", ["1024x1024", "1280x720", "1920x1080"])
                
                # Generate videos
                if st.button("🎬 Tạo Video VEO3", type="primary"):
                    if not scenes:
                        st.error("❌ Không có kịch bản để tạo video")
                        return
                    
                    # Prepare prompts
                    prompts = []
                    for i, scene in enumerate(scenes):
                        if i < len(image_paths):
                            # Create motion prompt from scene description
                            motion_prompt = f"Camera movement: {scene.get('description', '')[:100]}"
                            prompts.append(motion_prompt)
                    
                    # Generate videos
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    results = []
                    for i, (image_path, prompt) in enumerate(zip(image_paths, prompts)):
                        if i < len(scenes):
                            status_text.text(f"Đang tạo video {i+1}/{len(image_paths)}...")
                            
                            result = veo3.generate_video_from_image(
                                image_path, 
                                prompt,
                                duration=duration,
                                style=style
                            )
                            
                            if "error" not in result:
                                # Wait for completion
                                job_id = result.get("job_id")
                                if job_id:
                                    video_info = veo3.wait_for_video_completion(job_id)
                                    if video_info and "video_url" in video_info:
                                        # Download video
                                        video_filename = f"veo3_scene_{i+1:02d}.mp4"
                                        video_path = os.path.join("outputs/videos", video_filename)
                                        os.makedirs("outputs/videos", exist_ok=True)
                                        
                                        if veo3.download_video(video_info["video_url"], video_path):
                                            video_info["local_path"] = video_path
                                            video_info["filename"] = video_filename
                                            results.append(video_info)
                                        else:
                                            results.append({"error": f"Failed to download video {i+1}"})
                                    else:
                                        results.append({"error": f"Video {i+1} generation failed"})
                                else:
                                    results.append({"error": f"No job ID for video {i+1}"})
                            else:
                                results.append(result)
                            
                            progress_bar.progress((i + 1) / len(image_paths))
                    
                    # Store results
                    st.session_state.veo3_results = results
                    status_text.text("✅ Hoàn thành!")
                
                # Display results
                if 'veo3_results' in st.session_state and st.session_state.veo3_results:
                    st.markdown("### 🎬 Video đã tạo")
                    
                    results = st.session_state.veo3_results
                    
                    # Download all videos
                    if st.button("📥 Tải tất cả video (ZIP)"):
                        import zipfile
                        from io import BytesIO
                        
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for result in results:
                                if "local_path" in result and os.path.exists(result["local_path"]):
                                    zip_file.write(result["local_path"], result["filename"])
                        
                        zip_buffer.seek(0)
                        st.download_button(
                            label="📥 Tải ZIP",
                            data=zip_buffer.getvalue(),
                            file_name="veo3_videos.zip",
                            mime="application/zip"
                        )
                    
                    # Display individual videos
                    for i, result in enumerate(results):
                        if "error" not in result and "local_path" in result:
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.video(result["local_path"])
                                st.caption(f"Scene {i+1}: {result.get('filename', 'Unknown')}")
                            
                            with col2:
                                if os.path.exists(result["local_path"]):
                                    with open(result["local_path"], 'rb') as f:
                                        st.download_button(
                                            label=f"📥 Tải Scene {i+1}",
                                            data=f.read(),
                                            file_name=result["filename"],
                                            mime="video/mp4"
                                        )
                        else:
                            st.error(f"❌ Scene {i+1}: {result.get('error', 'Unknown error')}")
                
            else:
                st.error("❌ VEO3 Cookie không hợp lệ. Vui lòng kiểm tra lại.")
        
        except Exception as e:
            st.error(f"❌ Lỗi VEO3: {e}")
    
    else:
        st.warning("⚠️ Vui lòng nhập VEO3 Cookie để tiếp tục")

def main():
    """Main function"""
    # Sidebar
    with st.sidebar:
        st.title("🎬 AI Video Generator")
        
        # API Keys configuration
        create_api_keys_section()
        
        # Script configuration
        st.markdown("---")
        st.markdown("### 📝 Cấu hình Kịch bản")
        
        script_provider = st.selectbox(
            "Nhà cung cấp Script",
            api_manager.get_available_providers("script"),
            index=api_manager.get_available_providers("script").index(api_manager.get_default_provider("script")) if api_manager.get_default_provider("script") in api_manager.get_available_providers("script") else 0,
            help="Chọn nhà cung cấp để tạo kịch bản"
        )
        
        num_scenes = st.slider("Số cảnh", 1, 10, 3, help="Số lượng cảnh trong video")
        video_style = st.selectbox("Phong cách video", ["cinematic", "documentary", "educational", "storytelling"], index=0)
        include_dialogue = st.checkbox("Bao gồm đối thoại", value=True, help="Thêm đối thoại giữa các nhân vật")
        
        # Cấu hình độ dài kịch bản
        st.markdown("### 📏 Cấu hình Độ dài Kịch bản")
        script_length = st.selectbox("Độ dài kịch bản", 
                                   ["ngắn", "trung bình", "dài", "rất dài", "siêu dài (2 phút/cảnh)"],
                                   index=4, # Default to ultra_long
                                   help="Độ dài kịch bản ảnh hưởng đến chi tiết và mô tả. 'Siêu dài' tạo kịch bản 2 phút mỗi cảnh")
        
        # Cấu hình người dẫn chuyện
        st.markdown("### 🎭 Cấu hình Người dẫn chuyện")
        include_narrator = st.checkbox("Bao gồm người dẫn chuyện", value=True, help="Thêm lời dẫn chuyện cho video")
        narrator_style = st.selectbox("Phong cách dẫn chuyện", ["cinematic", "documentary", "educational", "storytelling"], index=0)
        
        # Image configuration
        st.markdown("---")
        st.markdown("### 🖼️ Cấu hình Ảnh")
        
        image_provider = st.selectbox(
            "Nhà cung cấp Ảnh",
            api_manager.get_available_providers("image"),
            index=api_manager.get_available_providers("image").index(api_manager.get_default_provider("image")) if api_manager.get_default_provider("image") in api_manager.get_available_providers("image") else 0,
            help="Chọn nhà cung cấp để tạo ảnh"
        )
        
        image_size = st.selectbox("Kích thước ảnh", ["1024x1024", "1792x1024", "1024x1792"], index=0)
        
        # Voice configuration
        st.markdown("---")
        st.markdown("### 🎤 Cấu hình Giọng nói")
        
        voice_provider = st.selectbox(
            "Nhà cung cấp TTS",
            api_manager.get_available_providers("voice"),
            index=api_manager.get_available_providers("voice").index(api_manager.get_default_provider("voice")) if api_manager.get_default_provider("voice") in api_manager.get_available_providers("voice") else 0,
            help="Chọn nhà cung cấp text-to-speech"
        )
    
    # Main content
    st.title("🎬 AI Video Generator")
    st.markdown("Tạo video AI từ ý tưởng của bạn với kịch bản, ảnh, âm thanh và chuyển động tự động!")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Tạo Kịch bản", "🖼️ Tạo Ảnh", "🎬 Tạo Video", "🎬 VEO3 Video"])
    
    with tab1:
        create_script_tab(script_provider, num_scenes, video_style, include_dialogue, include_narrator, narrator_style, script_length)
    
    with tab2:
        create_images_tab(image_provider, image_size)
    
    with tab3:
        create_video_tab()
    
    with tab4:
        create_veo3_tab()

def create_script_tab(script_provider, num_scenes, video_style, include_dialogue, include_narrator, narrator_style, script_length):
    """Tab tạo kịch bản"""
    st.markdown('<h2 class="step-header">📝 Bước 1: Tạo Kịch bản</h2>', unsafe_allow_html=True)
    
    # Tải kịch bản từ file
    st.markdown("### 📁 Tải Kịch bản từ File")
    
    # Nút tải file mẫu
    col_template, col_upload = st.columns([1, 2])
    
    with col_template:
        st.markdown("**📋 File mẫu:**")
        if os.path.exists("templates/script_template.json"):
            with open("templates/script_template.json", "r", encoding="utf-8") as f:
                template_data = f.read()
            
            st.download_button(
                label="📥 Tải File Mẫu JSON",
                data=template_data,
                file_name="script_template.json",
                mime="application/json",
                type="secondary",
                help="Tải file mẫu để chỉnh sửa theo ý tưởng của bạn"
            )
        else:
            st.warning("⚠️ File mẫu không tồn tại")
    
    with col_upload:
        st.markdown("**📤 Upload kịch bản:**")
        uploaded_script = st.file_uploader(
            "Chọn file kịch bản (JSON hoặc TXT)",
            type=['json', 'txt'],
            help="Tải kịch bản đã tạo trước đó để tiếp tục chỉnh sửa",
            label_visibility="collapsed"
        )
    
    if uploaded_script is not None:
        try:
            if uploaded_script.type == "application/json":
                # Tải kịch bản JSON
                script_data = json.load(uploaded_script)
                if 'scenes' in script_data:
                    st.session_state.scenes = script_data['scenes']
                    st.session_state.saved_scenes = script_data['scenes']
                    st.session_state.saved_project_scenes = script_data['scenes']
                    st.session_state.script_created = True
                    st.success(f"✅ Đã tải kịch bản với {len(script_data['scenes'])} cảnh!")
                    st.rerun()
                else:
                    st.error("❌ File JSON không đúng định dạng kịch bản")
            else:
                # Tải kịch bản TXT
                script_text = uploaded_script.read().decode('utf-8')
                st.session_state.uploaded_script_text = script_text
                st.success("✅ Đã tải file kịch bản TXT!")
                st.info("💡 Sử dụng text này làm prompt để tạo kịch bản mới")
        except Exception as e:
            st.error(f"❌ Lỗi tải file: {e}")
    
    # Hiển thị script text đã tải nếu có
    if 'uploaded_script_text' in st.session_state:
        st.text_area("Kịch bản đã tải:", value=st.session_state.uploaded_script_text, height=100)
        if st.button("🗑️ Xóa Script đã tải"):
            del st.session_state.uploaded_script_text
            st.rerun()
    
    # Kiểm tra và hiển thị kịch bản đã tạo trước đó (nếu có)
    if 'scenes' not in st.session_state and 'saved_scenes' not in st.session_state:
        # Kiểm tra file backup
        if os.path.exists('outputs/script_backup.json'):
            st.markdown("### 📋 Kịch bản đã tạo trước đó")
            st.info("Tìm thấy kịch bản đã tạo trước đó. Bạn có thể khôi phục hoặc tạo kịch bản mới.")
            
            try:
                with open('outputs/script_backup.json', 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                if 'scenes' in backup_data:
                    st.write(f"**Số cảnh:** {len(backup_data['scenes'])}")
                    st.write(f"**Prompt:** {backup_data.get('prompt', 'N/A')}")
                    st.write(f"**Phong cách:** {backup_data.get('style', 'N/A')}")
                    
                    col_restore, col_delete = st.columns(2)
                    
                    with col_restore:
                        if st.button("🔄 Khôi phục kịch bản", type="secondary"):
                            st.session_state.saved_scenes = backup_data['scenes']
                            st.session_state.script_metadata = {
                                'prompt': backup_data.get('prompt', ''),
                                'style': backup_data.get('style', 'cinematic'),
                                'provider': backup_data.get('provider', 'google'),
                                'timestamp': backup_data.get('timestamp', '')
                            }
                            st.rerun()
                    
                    with col_delete:
                        if st.button("🗑️ Xóa kịch bản cũ", type="secondary"):
                            if os.path.exists('outputs/script_backup.json'):
                                os.remove('outputs/script_backup.json')
                            st.rerun()
                        
            except Exception as e:
                st.warning(f"⚠️ Không thể đọc file backup: {e}")
            
            st.markdown("---")
    
    # Input prompt
    prompt = st.text_area(
        "Nhập ý tưởng video của bạn:",
        placeholder="Ví dụ: Một cuộc phiêu lưu kỳ thú trong rừng rậm với những con vật biết nói...",
        height=100,
        value=st.session_state.get('uploaded_script_text', '')
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Kiểm tra API key
        if script_provider in ["openai", "anthropic"] and not api_manager.get_api_key(script_provider):
            st.error(f"Vui lòng nhập {script_provider.title()} API Key trong sidebar")
            return
        
        if st.button("🎬 Tạo Kịch bản", type="primary", width='stretch'):
            if not prompt.strip():
                st.error("Vui lòng nhập ý tưởng video")
                return
            
            try:
                # Tạo script generator
                generator = ScriptGenerator(provider=script_provider)
                
                # Mapping độ dài
                length_mapping = {
                    "ngắn": "short",
                    "trung bình": "medium", 
                    "dài": "long",
                    "rất dài": "very_long",
                    "siêu dài (2 phút/cảnh)": "ultra_long"
                }
                script_length_key = length_mapping.get(script_length, "medium")
                
                # Tạo script
                with st.spinner("Đang tạo kịch bản..."):
                    scenes = generator.generate_script(
                        prompt=prompt,
                        num_scenes=num_scenes,
                        style=video_style,
                        include_dialogue=include_dialogue,
                        script_length=script_length_key
                    )
                
                # Thêm narrator nếu cần
                if include_narrator:
                    from modules.script_generator import add_narrator_to_scenes
                    scenes = add_narrator_to_scenes(scenes, narrator_style)
                
                # Lưu vào session state
                st.session_state.scenes = scenes
                st.session_state.saved_scenes = scenes
                st.session_state.saved_project_scenes = scenes
                st.session_state.script_created = True
                st.session_state.script_prompt = prompt
                st.session_state.script_style = video_style
                
                # Lưu backup
                backup_data = {
                    'scenes': scenes,
                    'prompt': prompt,
                    'style': video_style,
                    'provider': script_provider,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                os.makedirs('outputs', exist_ok=True)
                with open('outputs/script_backup.json', 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
                st.success(f"✅ Đã tạo kịch bản với {len(scenes)} cảnh!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Lỗi tạo kịch bản: {e}")
    
    with col2:
        # Khôi phục từ backup
        if st.button("🔄 Khôi phục Script", type="secondary"):
            if os.path.exists('outputs/script_backup.json'):
                try:
                    with open('outputs/script_backup.json', 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    st.session_state.scenes = backup_data['scenes']
                    st.session_state.saved_scenes = backup_data['scenes']
                    st.session_state.saved_project_scenes = backup_data['scenes']
                    st.session_state.script_created = True
                    st.success("✅ Đã khôi phục từ backup!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi khôi phục: {e}")
            else:
                st.warning("⚠️ Không có file backup")
    
    # Hiển thị kịch bản đã tạo
    if 'scenes' in st.session_state and st.session_state.scenes:
        st.markdown("### 📋 Kịch bản đã tạo")
        
        # Nút tải xuống kịch bản
        col_download1, col_download2 = st.columns(2)
        
        with col_download1:
            # Tải xuống JSON
            script_json = json.dumps({
                'scenes': st.session_state.scenes,
                'prompt': st.session_state.get('script_prompt', ''),
                'style': st.session_state.get('script_style', ''),
                'provider': script_provider,
                'timestamp': datetime.datetime.now().isoformat()
            }, ensure_ascii=False, indent=2)
            
            st.download_button(
                label="📥 Tải Kịch bản JSON",
                data=script_json,
                file_name=f"script_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                type="secondary"
            )
        
        with col_download2:
            # Tải xuống TXT
            script_text = f"KỊCH BẢN VIDEO\n"
            script_text += f"Ngày tạo: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            script_text += f"Prompt: {st.session_state.get('script_prompt', '')}\n"
            script_text += f"Phong cách: {st.session_state.get('script_style', '')}\n"
            script_text += f"Số cảnh: {len(st.session_state.scenes)}\n\n"
            
            for i, scene in enumerate(st.session_state.scenes):
                script_text += f"🎬 CẢNH {i+1}: {scene.get('title', 'Untitled')}\n"
                script_text += f"Mô tả: {scene.get('description', '')}\n"
                if scene.get('dialogue'):
                    script_text += f"Đối thoại: {scene.get('dialogue', '')}\n"
                if scene.get('narrator'):
                    script_text += f"Người dẫn chuyện: {scene.get('narrator', '')}\n"
                script_text += f"Thời lượng: {scene.get('duration', 'N/A')}\n"
                script_text += f"Chuyển cảnh: {scene.get('transition', 'N/A')}\n\n"
            
            st.download_button(
                label="📄 Tải Kịch bản TXT",
                data=script_text,
                file_name=f"script_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                type="secondary"
            )
        
        # Nút xóa kịch bản
        col_delete_script = st.columns(1)[0]
        with col_delete_script:
            if st.button("🗑️ Xóa Kịch bản", type="secondary", width='stretch'):
                try:
                    # Xóa khỏi session state
                    keys_to_delete = ['scenes', 'saved_scenes', 'saved_project_scenes', 'script_created', 'script_prompt', 'script_style']
                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Xóa file backup
                    if os.path.exists('outputs/script_backup.json'):
                        os.remove('outputs/script_backup.json')
                    
                    st.success("✅ Đã xóa kịch bản!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi xóa kịch bản: {e}")
        
        # Hiển thị chi tiết kịch bản
        for i, scene in enumerate(st.session_state.scenes):
            with st.expander(f"🎬 Cảnh {i+1}: {scene.get('title', 'Untitled')}"):
                st.write(f"**Mô tả:** {scene.get('description', '')}")
                if scene.get('dialogue'):
                    st.write(f"**Đối thoại:** {scene.get('dialogue', '')}")
                if scene.get('narrator'):
                    st.write(f"**Người dẫn chuyện:** {scene.get('narrator', '')}")
                st.write(f"**Thời lượng:** {scene.get('duration', 'N/A')}")
                st.write(f"**Chuyển cảnh:** {scene.get('transition', 'N/A')}")

def create_images_tab(image_provider, image_size):
    """Tab tạo ảnh"""
    st.markdown('<h2 class="step-header">🖼️ Bước 2: Tạo Ảnh</h2>', unsafe_allow_html=True)
    
    # Tải ảnh hàng loạt
    st.markdown("### 📁 Tải Ảnh Hàng loạt")
    uploaded_images = st.file_uploader(
        "Chọn nhiều ảnh cùng lúc",
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=True,
        help="Tải nhiều ảnh để sử dụng thay vì tạo ảnh mới"
    )
    
    if uploaded_images:
        st.success(f"✅ Đã tải {len(uploaded_images)} ảnh!")
        
        # Lưu ảnh đã tải
        uploaded_image_paths = []
        for i, uploaded_file in enumerate(uploaded_images):
            # Tạo tên file
            file_extension = uploaded_file.name.split('.')[-1]
            image_path = f"outputs/images/uploaded_scene_{i+1:02d}.{file_extension}"
            
            # Lưu file
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            uploaded_image_paths.append(image_path)
        
        # Lưu vào session state với timestamp để tránh conflict
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.uploaded_images = uploaded_image_paths
        st.session_state.image_paths = uploaded_image_paths
        st.session_state.uploaded_images_timestamp = timestamp
        
        # Lưu backup thông tin ảnh đã upload
        backup_info = {
            'uploaded_images': uploaded_image_paths,
            'timestamp': timestamp,
            'count': len(uploaded_image_paths)
        }
        os.makedirs('outputs', exist_ok=True)
        with open('outputs/uploaded_images_backup.json', 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
        # Hiển thị ảnh đã tải
        st.markdown("#### 🖼️ Ảnh đã tải:")
        
        # Nút tải xuống ZIP cho ảnh đã upload
        import zipfile
        import io
        
        # Tạo ZIP data trước
        zip_data = None
        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, image_path in enumerate(uploaded_image_paths):
                    if os.path.exists(image_path):
                        with open(image_path, 'rb') as f:
                            image_data = f.read()
                        zip_file.writestr(f"uploaded_scene_{i+1:02d}.{image_path.split('.')[-1]}", image_data)
            
            zip_buffer.seek(0)
            zip_data = zip_buffer.getvalue()
        except Exception as e:
            st.error(f"❌ Lỗi tạo ZIP: {e}")
        
        if zip_data:
            st.download_button(
                label="📦 Tải ZIP ảnh đã upload",
                data=zip_data,
                file_name=f"uploaded_images_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                type="secondary",
                key=f"download_uploaded_zip_{len(uploaded_image_paths)}"
            )
        
        cols = st.columns(min(len(uploaded_image_paths), 3))
        for i, image_path in enumerate(uploaded_image_paths):
            with cols[i % 3]:
                st.image(image_path, caption=f"Scene {i+1}", width='stretch')
                
                # Nút tải xuống từng ảnh đã upload - sử dụng key unique
                if os.path.exists(image_path):
                    with open(image_path, "rb") as file:
                        file_data = file.read()
                        st.download_button(
                            label=f"📥 Tải Scene {i+1}",
                            data=file_data,
                            file_name=f"uploaded_scene_{i+1:02d}.{image_path.split('.')[-1]}",
                            mime="image/png",
                            key=f"download_uploaded_scene_{i}_{len(uploaded_image_paths)}",  # Unique key
                            type="secondary",
                            width='stretch'
                        )
        
        if st.button("🗑️ Xóa ảnh đã tải"):
            # Xóa file ảnh
            for image_path in uploaded_image_paths:
                if os.path.exists(image_path):
                    os.remove(image_path)
            # Xóa khỏi session state
            if 'uploaded_images' in st.session_state:
                del st.session_state.uploaded_images
            if 'image_paths' in st.session_state:
                del st.session_state.image_paths
            st.success("✅ Đã xóa ảnh đã tải!")
            st.rerun()
        
        st.info("💡 Ảnh đã tải sẽ được sử dụng thay vì tạo ảnh mới. Bạn có thể chuyển sang tab 'Tạo Video' để tạo video.")
        return
    
    # Kiểm tra có script không
    if 'scenes' not in st.session_state and 'saved_scenes' not in st.session_state:
        st.markdown('<div class="info-box">ℹ️ Vui lòng tạo kịch bản trước khi tạo ảnh</div>', 
                   unsafe_allow_html=True)
        return
    
    # Kiểm tra và hiển thị ảnh đã tạo trước đó (nếu có)
    existing_images = []
    if os.path.exists("outputs/images"):
        for file in os.listdir("outputs/images"):
            if file.startswith("scene_") and file.endswith((".png", ".jpg", ".jpeg", ".webp")):
                existing_images.append(os.path.join("outputs/images", file))
    
    # Kiểm tra ảnh đã upload trước đó
    uploaded_images_backup = []
    if os.path.exists("outputs/uploaded_images_backup.json"):
        try:
            with open("outputs/uploaded_images_backup.json", "r", encoding="utf-8") as f:
                backup_data = json.load(f)
            if 'uploaded_images' in backup_data:
                # Kiểm tra file ảnh còn tồn tại
                for image_path in backup_data['uploaded_images']:
                    if os.path.exists(image_path):
                        uploaded_images_backup.append(image_path)
        except Exception as e:
            st.warning(f"⚠️ Không thể đọc backup ảnh đã upload: {e}")
    
    # Nếu có ảnh đã upload trước đó và chưa có trong session state
    if uploaded_images_backup and 'image_paths' not in st.session_state:
        st.markdown("### 📤 Ảnh đã upload trước đó")
        st.info(f"Tìm thấy {len(uploaded_images_backup)} ảnh đã upload trước đó. Bạn có thể sử dụng chúng hoặc upload ảnh mới.")
        
        # Hiển thị ảnh đã upload
        cols = st.columns(min(len(uploaded_images_backup), 3))
        for i, image_path in enumerate(uploaded_images_backup):
            with cols[i % 3]:
                st.image(image_path, caption=f"Uploaded Scene {i+1}", width='stretch')
        
        # Nút sử dụng và xóa ảnh đã upload
        col_use_uploaded, col_delete_uploaded = st.columns(2)
        
        with col_use_uploaded:
            if st.button("🔄 Sử dụng ảnh đã upload", type="primary", width='stretch'):
                st.session_state.image_paths = sorted(uploaded_images_backup)
                st.session_state.saved_project_images = sorted(uploaded_images_backup)
                st.session_state.uploaded_images = sorted(uploaded_images_backup)
                st.success("✅ Đã load ảnh đã upload trước đó!")
                st.rerun()
        
        with col_delete_uploaded:
            if st.button("🗑️ Xóa ảnh đã upload", type="secondary", width='stretch'):
                try:
                    # Xóa file ảnh
                    for image_path in uploaded_images_backup:
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    
                    # Xóa file backup
                    if os.path.exists("outputs/uploaded_images_backup.json"):
                        os.remove("outputs/uploaded_images_backup.json")
                    
                    # Xóa khỏi session state nếu có
                    if 'image_paths' in st.session_state:
                        del st.session_state.image_paths
                    if 'saved_project_images' in st.session_state:
                        del st.session_state.saved_project_images
                    if 'uploaded_images' in st.session_state:
                        del st.session_state.uploaded_images
                    
                    st.success("✅ Đã xóa ảnh đã upload!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi xóa ảnh: {e}")
        
        st.markdown("---")
    
    # Nếu có ảnh đã tạo trước đó và chưa có trong session state
    if existing_images and 'image_paths' not in st.session_state:
        st.markdown("### 🖼️ Ảnh đã tạo trước đó")
        st.info(f"Tìm thấy {len(existing_images)} ảnh đã tạo trước đó. Bạn có thể sử dụng chúng hoặc tạo ảnh mới.")
        
        # Hiển thị ảnh đã có
        cols = st.columns(min(len(existing_images), 3))
        for i, image_path in enumerate(existing_images):
            with cols[i % 3]:
                st.image(image_path, caption=f"Scene {i+1}", width='stretch')
        
        # Nút sử dụng và xóa ảnh đã có
        col_use_images, col_delete_images = st.columns(2)
        
        with col_use_images:
            if st.button("🔄 Sử dụng ảnh đã tạo", type="primary", width='stretch'):
                st.session_state.image_paths = sorted(existing_images)
                st.session_state.saved_project_images = sorted(existing_images)
                st.success("✅ Đã load ảnh đã tạo trước đó!")
                st.rerun()
        
        with col_delete_images:
            if st.button("🗑️ Xóa ảnh cũ", type="secondary", width='stretch'):
                try:
                    # Xóa file ảnh
                    for image_path in existing_images:
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    
                    # Xóa khỏi session state nếu có
                    if 'image_paths' in st.session_state:
                        del st.session_state.image_paths
                    if 'saved_project_images' in st.session_state:
                        del st.session_state.saved_project_images
                    
                    st.success("✅ Đã xóa ảnh cũ!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi xóa ảnh: {e}")
        
        st.markdown("---")
    
    # Lấy danh sách các kịch bản có sẵn
    available_scripts = []
    
    # Load từ session state
    if 'scenes' in st.session_state:
        script_name = f"Kịch bản hiện tại ({len(st.session_state.scenes)} cảnh)"
        available_scripts.append((script_name, st.session_state.scenes))
    
    if 'saved_scenes' in st.session_state:
        script_name = f"Kịch bản đã lưu ({len(st.session_state.saved_scenes)} cảnh)"
        available_scripts.append((script_name, st.session_state.saved_scenes))
    
    # Load từ file backup
    if os.path.exists('outputs/script_backup.json'):
        try:
            with open('outputs/script_backup.json', 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            if 'scenes' in backup_data:
                script_name = f"Kịch bản từ file ({len(backup_data['scenes'])} cảnh)"
                available_scripts.append((script_name, backup_data['scenes']))
        except Exception as e:
            st.warning(f"⚠️ Không thể đọc file backup: {e}")
    
    if not available_scripts:
        st.markdown('<div class="info-box">ℹ️ Không có kịch bản nào để tạo ảnh</div>', 
                   unsafe_allow_html=True)
        return
    
    # Dropdown chọn kịch bản
    st.markdown("### 📋 Chọn kịch bản để tạo ảnh")
    if len(available_scripts) == 1:
        selected_script_name, selected_scenes = available_scripts[0]
        st.info(f"📝 Sử dụng: {selected_script_name}")
    else:
        script_options = [script[0] for script in available_scripts]
        selected_script_idx = st.selectbox("Chọn kịch bản:", range(len(script_options)), 
                                         format_func=lambda x: script_options[x])
        selected_script_name, selected_scenes = available_scripts[selected_script_idx]
    
    # Kiểm tra API key
    if image_provider in ["openai", "stability", "replicate", "huggingface"] and not api_manager.get_api_key(image_provider):
        st.error(f"Vui lòng nhập {image_provider.title()} API Key trong sidebar")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎨 Tạo Ảnh", type="primary", width='stretch'):
            try:
                # Xóa ảnh cũ trước khi tạo mới
                if os.path.exists("outputs/images"):
                    for file in os.listdir("outputs/images"):
                        if file.startswith("scene_") and file.endswith((".png", ".jpg", ".jpeg", ".webp")):
                            os.remove(os.path.join("outputs/images", file))
                            st.write(f"🗑️ Deleted: {file}")
                
                # Tạo image generator
                generator = ImageGenerator(provider=image_provider)
                
                # Tạo thư mục output
                os.makedirs("outputs/images", exist_ok=True)
                
                # Tạo ảnh cho từng scene
                image_paths = []
                progress_bar = st.progress(0)
                
                for i, scene in enumerate(selected_scenes):
                    with st.spinner(f"Đang tạo ảnh cho cảnh {i+1}/{len(selected_scenes)}..."):
                        # Tạo prompt cho ảnh
                        image_prompt = scene.get('image_prompt', scene.get('description', ''))
                        
                        # Debug: Hiển thị thông tin prompt
                        st.write(f"**Scene {i+1}:** {scene.get('title', 'Untitled')}")
                        st.write(f"**Prompt length:** {len(image_prompt)} characters")
                        st.write(f"**Prompt:** {image_prompt[:100]}...")
                        
                        # Tạo ảnh
                        image_path = f"outputs/images/scene_{i+1:02d}.png"
                        result_path = generator.generate_image(
                            prompt=image_prompt,
                            output_path=image_path,
                            size=image_size
                        )
                        
                        image_paths.append(result_path)
                        progress_bar.progress((i + 1) / len(selected_scenes))
                
                # Lưu vào session state
                st.session_state.image_paths = image_paths
                st.session_state.saved_project_images = image_paths
                
                st.success(f"✅ Đã tạo {len(image_paths)} ảnh!")
                
                # Hiển thị ảnh đã tạo
                st.markdown("### 🖼️ Ảnh đã tạo")
                
                # Hiển thị ảnh
                cols = st.columns(min(len(image_paths), 3))
                for i, image_path in enumerate(image_paths):
                    with cols[i % 3]:
                        if os.path.exists(image_path):
                            st.image(image_path, caption=f"Scene {i+1}", width='stretch')
                            st.download_button(
                                label=f"Tải Scene {i+1}",
                                data=open(image_path, "rb").read(),
                                file_name=f"scene_{i+1:02d}.png",
                                mime="image/png",
                                width='stretch'
                            )
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Lỗi tạo ảnh: {e}")
                st.exception(e)
    
    # Base64 Conversion Section
    if 'image_paths' in st.session_state and st.session_state.image_paths:
        st.markdown("---")
        st.markdown("### 🔄 Chuyển đổi Base64")
        
        try:
            from modules.image_generator import batch_images_to_base64
            base64_data = batch_images_to_base64(st.session_state.image_paths)
            
            if base64_data:
                st.success(f"✅ Đã chuyển đổi {len(base64_data)} ảnh sang Base64")
                
                # Hiển thị thông tin Base64
                st.markdown("#### 📊 Thông tin Base64")
                import pandas as pd
                df_data = []
                for i, data in enumerate(base64_data):
                    df_data.append({
                        'Scene': f"Scene {i+1}",
                        'File Size': f"{data['file_size']} bytes",
                        'Base64 Size': f"{data['base64_size']} bytes",
                        'Resolution': data['resolution'],
                        'Format': data['format']
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
                
                # Nút tải xuống Base64
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📥 Tải tất cả Base64 (ZIP)", type="secondary"):
                        import zipfile
                        import io
                        
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for i, data in enumerate(base64_data):
                                zip_file.writestr(f"scene_{i+1:02d}_base64.txt", data['base64_string'])
                        
                        zip_buffer.seek(0)
                        st.download_button(
                            label="📦 Tải ZIP Base64",
                            data=zip_buffer.getvalue(),
                            file_name=f"base64_images_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                            mime="application/zip",
                            width='stretch'
                        )
                
                with col2:
                    if st.button("👁️ Xem Base64", type="secondary"):
                        for i, data in enumerate(base64_data):
                            with st.expander(f"Scene {i+1} Base64"):
                                st.text_area(f"Base64 Scene {i+1}", value=data['base64_string'][:500] + "...", height=100)
                                st.download_button(
                                    label=f"Tải Scene {i+1} Base64",
                                    data=data['base64_string'],
                                    file_name=f"scene_{i+1:02d}_base64.txt",
                                    mime="text/plain",
                                    width='stretch'
                                )
        
        except ImportError as e:
            st.error(f"❌ Lỗi import: {e}")
        except Exception as e:
            st.error(f"❌ Lỗi chuyển đổi Base64: {e}")

def create_video_tab():
    """Tab tạo video"""
    st.markdown('<h2 class="step-header">🎬 Bước 3: Tạo Video</h2>', unsafe_allow_html=True)
    
    # Kiểm tra có ảnh không
    if 'image_paths' not in st.session_state or not st.session_state.image_paths:
        st.markdown('<div class="info-box">ℹ️ Vui lòng tạo ảnh trước khi tạo video</div>', 
                   unsafe_allow_html=True)
        return
                
                with col_download_zip:
                    # Nút xóa tất cả ảnh
                    if st.button("🗑️ Xóa tất cả ảnh", type="secondary"):
                        try:
                            # Xóa file ảnh
                            for image_path in image_paths:
                                if os.path.exists(image_path):
                                    os.remove(image_path)
                            
                            # Xóa khỏi session state
                            if 'image_paths' in st.session_state:
                            del st.session_state.image_paths
                        if 'saved_project_images' in st.session_state:
                            del st.session_state.saved_project_images
                        
                        st.success("✅ Đã xóa tất cả ảnh!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Lỗi xóa ảnh: {e}")
            
            # Hiển thị ảnh với nút tải xuống riêng lẻ
            cols = st.columns(min(len(image_paths), 3))
            for i, image_path in enumerate(image_paths):
                with cols[i % 3]:
                    st.image(image_path, caption=f"Scene {i+1}", width='stretch')
                    
                    # Nút tải xuống từng ảnh - sử dụng key unique để tránh reload
                    if os.path.exists(image_path):
                        with open(image_path, "rb") as file:
                            file_data = file.read()
                            st.download_button(
                                label=f"📥 Tải Scene {i+1}",
                                data=file_data,
                                file_name=f"scene_{i+1:02d}.png",
                                mime="image/png",
                                key=f"download_scene_{i}_{len(image_paths)}",  # Unique key
                                type="secondary",
                                width='stretch'
                            )
            
        except Exception as e:
            st.error(f"❌ Lỗi tạo ảnh: {e}")
    
    # Base64 Conversion Section
    if 'image_paths' in st.session_state and st.session_state.image_paths:
        st.markdown("---")
        st.markdown("### 🔄 Chuyển đổi Base64")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔄 Chuyển ảnh thành Base64", type="secondary"):
                try:
                    image_paths = st.session_state.image_paths
                    
                    # Tạo thư mục base64
                    base64_dir = "outputs/base64"
                    os.makedirs(base64_dir, exist_ok=True)
                    
                    # Import Base64 functions
                    try:
                        from modules.image_generator import batch_images_to_base64
                        # Chuyển đổi tất cả ảnh thành Base64
                        results = batch_images_to_base64(image_paths, base64_dir)
                    except ImportError as e:
                        st.error(f"❌ Lỗi import Base64 functions: {e}")
                        return
                    
                    # Lưu kết quả vào session state
                    st.session_state.base64_results = results
                    
                    st.success(f"✅ Đã chuyển đổi {len([r for r in results if 'error' not in r])} ảnh thành Base64!")
                    
                except Exception as e:
                    st.error(f"❌ Lỗi chuyển đổi Base64: {e}")
        
        with col2:
            if st.button("📊 Xem thông tin Base64", type="secondary"):
                if 'base64_results' in st.session_state:
                    results = st.session_state.base64_results
                    
                    # Hiển thị bảng thông tin
                    import pandas as pd
                    
                    data = []
                    for i, result in enumerate(results):
                        if 'error' not in result:
                            data.append({
                                'Ảnh': f"Scene {i+1}",
                                'Kích thước file (MB)': result['file_size_mb'],
                                'Kích thước Base64 (MB)': result['base64_size_mb'],
                                'Độ phân giải': f"{result['image_width']}x{result['image_height']}",
                                'Định dạng': result['image_format']
                            })
                    
                    if data:
                        df = pd.DataFrame(data)
                        st.dataframe(df, width='stretch')
                        
                        # Tổng kết
                        total_file_size = sum(r['file_size_mb'] for r in results if 'error' not in r)
                        total_base64_size = sum(r['base64_size_mb'] for r in results if 'error' not in r)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Tổng ảnh", len(data))
                        with col2:
                            st.metric("Tổng kích thước file", f"{total_file_size:.2f} MB")
                        with col3:
                            st.metric("Tổng kích thước Base64", f"{total_base64_size:.2f} MB")
                    else:
                        st.warning("Không có dữ liệu Base64")
                else:
                    st.warning("Vui lòng chuyển đổi ảnh thành Base64 trước")
        
        # Hiển thị kết quả Base64
        if 'base64_results' in st.session_state and st.session_state.base64_results:
            st.markdown("#### 📋 Kết quả Base64:")
            
            results = st.session_state.base64_results
            
            # Download tất cả file Base64
            if st.button("📥 Tải tất cả file Base64 (ZIP)"):
                import zipfile
                from io import BytesIO
                
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for i, result in enumerate(results):
                        if 'error' not in result and 'base64_file' in result:
                            if os.path.exists(result['base64_file']):
                                zip_file.write(result['base64_file'], f"scene_{i+1:02d}_base64.txt")
                
                zip_buffer.seek(0)
                st.download_button(
                    label="📥 Tải ZIP Base64",
                    data=zip_buffer.getvalue(),
                    file_name="images_base64.zip",
                    mime="application/zip"
                )
            
            # Hiển thị từng file Base64
            for i, result in enumerate(results):
                if 'error' not in result:
                    with st.expander(f"Scene {i+1} - Base64 Info"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.json({
                                "File Path": result['file_path'],
                                "File Size": f"{result['file_size_mb']} MB",
                                "Base64 Size": f"{result['base64_size_mb']} MB",
                                "Resolution": f"{result['image_width']}x{result['image_height']}",
                                "Format": result['image_format']
                            })
                        
                        with col2:
                            if 'base64_file' in result and os.path.exists(result['base64_file']):
                                with open(result['base64_file'], 'r', encoding='utf-8') as f:
                                    base64_content = f.read()
                                
                                st.download_button(
                                    label=f"📥 Tải Base64 Scene {i+1}",
                                    data=base64_content,
                                    file_name=f"scene_{i+1:02d}_base64.txt",
                                    mime="text/plain"
                                )
                        
                        # Hiển thị preview Base64
                        st.text_area(
                            f"Base64 Preview Scene {i+1}",
                            value=result['base64_preview'],
                            height=100,
                            disabled=True
                        )
                else:
                    st.error(f"❌ Scene {i+1}: {result['error']}")

def create_video_tab():
    """Tab tạo video"""
    st.markdown('<h2 class="step-header">🎬 Bước 3: Tạo Video</h2>', unsafe_allow_html=True)
    
    # Kiểm tra có ảnh không
    if 'image_paths' not in st.session_state or not st.session_state.image_paths:
        st.markdown('<div class="info-box">ℹ️ Vui lòng tạo ảnh trước khi tạo video</div>', 
                   unsafe_allow_html=True)
        return
    
    # Kiểm tra có script không
    if 'scenes' not in st.session_state and 'saved_scenes' not in st.session_state:
        st.markdown('<div class="info-box">ℹ️ Vui lòng tạo kịch bản trước khi tạo video</div>', 
                   unsafe_allow_html=True)
        return
    
    # Lấy scenes và images
    scenes = st.session_state.get('scenes', st.session_state.get('saved_scenes', []))
    image_paths = st.session_state.image_paths
    
    st.info(f"Sẽ tạo video từ {len(scenes)} cảnh với {len(image_paths)} ảnh")
    
    # Cấu hình voice settings
    st.markdown("### 🎤 Cấu hình Giọng nói")
    
    col1, col2 = st.columns(2)
    
    with col1:
        voice_provider = st.selectbox(
            "Nhà cung cấp TTS",
            ["edge", "elevenlabs", "openai", "gtts", "azure"],
            index=1,
            help="Chọn nhà cung cấp text-to-speech"
        )
        
        # Voice selection based on provider
        if voice_provider == "edge":
            available_voices = [
                "vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural", "vi-VN-ThanhDatNeural",
                "vi-VN-LinhNeural", "en-US-AriaNeural", "en-US-JennyNeural",
                "en-US-GuyNeural", "en-GB-SoniaNeural", "en-GB-RyanNeural"
            ]
            selected_voice = st.selectbox("Giọng nói", available_voices, index=0)
        elif voice_provider == "openai":
            available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            selected_voice = st.selectbox("Giọng nói", available_voices, index=0)
        elif voice_provider == "azure":
            available_voices = [
                "vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural", "vi-VN-ThanhDatNeural",
                "vi-VN-LinhNeural", "en-US-AriaNeural", "en-US-JennyNeural",
                "en-US-GuyNeural", "en-US-DavisNeural", "en-US-EmmaNeural",
                "en-US-BrianNeural", "en-GB-SoniaNeural", "en-GB-RyanNeural",
                "en-GB-LibbyNeural", "en-GB-MaisieNeural"
            ]
            selected_voice = st.selectbox("Giọng nói", available_voices, index=0)
        elif voice_provider == "elevenlabs":
            available_voices = [
                "21m00Tcm4TlvDq8ikWAM", "AZnzlk1XvdvUeBnXmlld", "EXAVITQu4vr4xnSDxMaL",
                "ErXwobaYiN019PkySvjV", "MF3mGyEYCl7XYWbV9V6O", "TxGEqnHWrfWFTfGW9XjX",
                "VR6AewLTigWG4xSOukaG", "pNInz6obpgDQGcFmaJgB", "yoZ06aMxZJJ28mfd3POQ"
            ]
            selected_voice = st.selectbox("Giọng nói", available_voices, index=0)
        else:  # gtts
            available_voices = ["vi", "en", "en-us", "en-gb"]
            selected_voice = st.selectbox("Giọng nói", available_voices, index=0)
    
    with col2:
        voice_rate = st.selectbox(
            "Tốc độ nói",
            ["-50%", "-25%", "+0%", "+25%", "+50%"],
            index=2,
            help="Điều chỉnh tốc độ nói"
        )
        
        voice_pitch = st.selectbox(
            "Cao độ giọng",
            ["-50Hz", "-25Hz", "+0Hz", "+25Hz", "+50Hz"],
            index=2,
            help="Điều chỉnh cao độ giọng nói"
        )
    
    # Test voice button
    if st.button("🎵 Test Giọng nói", type="secondary"):
        test_text = "Xin chào, đây là test giọng nói. Bạn có thể nghe thấy tôi không?"
        try:
            from modules.voice_generator import VoiceGenerator
            generator = VoiceGenerator(provider=voice_provider)
            test_path = "temp/test_voice.mp3"
            os.makedirs("temp", exist_ok=True)
            result = generator.generate_voice(test_text, test_path, selected_voice, voice_rate, voice_pitch)
            if os.path.exists(result):
                st.audio(result)
                st.success("✅ Test giọng nói thành công!")
            else:
                st.error("❌ Không thể tạo file audio test")
        except Exception as e:
            st.error(f"❌ Lỗi test giọng nói: {e}")
    
    # Cấu hình video effects
    st.markdown("### ✨ Cấu hình Video")
    
    col3, col4 = st.columns(2)
    
    with col3:
        video_effect = st.selectbox("Hiệu ứng video", ["ken_burns", "zoom_in", "zoom_out", "pan_left", "pan_right", "static"], index=0)
        video_fps = st.slider("FPS", 24, 60, 30)
        scene_duration = st.slider("Thời lượng mỗi cảnh (giây)", 1, 300, 120, help="Thời gian hiển thị mỗi ảnh trong video (1-300 giây = 5 phút)")
    
    with col4:
        video_resolution = st.selectbox("Độ phân giải", ["1920x1080", "1280x720", "854x480"], index=0)
        
        # Background music upload
        st.markdown("**Nhạc nền (tùy chọn)**")
        background_music = st.file_uploader(
            "Chọn file nhạc nền",
            type=['mp3', 'wav', 'm4a'],
            help="Tải lên file nhạc nền cho video"
        )
        
        background_music_path = None
        if background_music:
            background_music_path = f"temp/background_music.{background_music.name.split('.')[-1]}"
            with open(background_music_path, "wb") as f:
                f.write(background_music.getbuffer())
            st.success("✅ Đã tải nhạc nền!")
    
    # Tạo video
    if st.button("🎬 Tạo Video với TTS", type="primary", width='stretch'):
        try:
            # Kiểm tra API key nếu cần
            if voice_provider in ["openai", "azure", "elevenlabs"] and not api_manager.get_api_key(voice_provider):
                st.error(f"Vui lòng nhập {voice_provider.title()} API Key trong sidebar")
                return
            
            # Voice settings
            voice_settings = {
                "provider": voice_provider,
                "voice": selected_voice,
                "rate": voice_rate,
                "pitch": voice_pitch,
                "api_key": api_manager.get_api_key(voice_provider) if voice_provider != "gtts" else None
            }
            
            # Tạo VideoMaker
            video_maker = VideoMaker(fps=video_fps, resolution=tuple(map(int, video_resolution.split('x'))))
            
            # Đường dẫn output
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"outputs/videos/final_video_{timestamp}.mp4"
            os.makedirs("outputs/videos", exist_ok=True)
            
            # Tạo video
            with st.spinner("Đang tạo video..."):
                result = video_maker.create_complete_video(
                    scenes=scenes,
                    image_paths=image_paths,
                    output_path=output_path,
                    voice_settings=voice_settings,
                    background_music=background_music_path,
                    scene_duration=scene_duration
                )
            
            st.success(f"✅ Video đã được tạo: {result}")
            
            # Hiển thị video
            st.video(result)
            
            # Download button
            with open(result, "rb") as file:
                st.download_button(
                    label="📥 Tải Video",
                    data=file.read(),
                    file_name=f"video_{timestamp}.mp4",
                    mime="video/mp4"
                )
            
        except Exception as e:
            st.error(f"❌ Lỗi tạo video: {e}")
    
    # Xóa video đã tạo
    st.markdown("### 🗑️ Quản lý Video")
    if st.button("🗑️ Xóa tất cả Video đã tạo", type="secondary"):
        try:
            videos_dir = "outputs/videos"
            if os.path.exists(videos_dir):
                for file in os.listdir(videos_dir):
                    if file.endswith('.mp4'):
                        os.remove(os.path.join(videos_dir, file))
                st.success("✅ Đã xóa tất cả video!")
            else:
                st.info("ℹ️ Không có video nào để xóa")
        except Exception as e:
            st.error(f"❌ Lỗi xóa video: {e}")

def create_flow_tab():
    """Tab Google Flow"""
    st.markdown('<h2 class="step-header">🌊 Google Flow Integration</h2>', unsafe_allow_html=True)
    
    st.info("🌊 Google Flow là công cụ tạo video AI mạnh mẽ từ Google. Bạn có thể sử dụng ảnh và kịch bản đã tạo để tạo video trên Google Flow.")
    
    # Kiểm tra có ảnh và script không
    has_images = 'image_paths' in st.session_state and st.session_state.image_paths
    has_script = 'scenes' in st.session_state or 'saved_scenes' in st.session_state
    
    if not has_images or not has_script:
        st.warning("⚠️ Vui lòng tạo ảnh và kịch bản trước khi sử dụng Google Flow")
        return
    
    # Lấy dữ liệu
    scenes = st.session_state.get('scenes', st.session_state.get('saved_scenes', []))
    image_paths = st.session_state.image_paths
    
    st.success(f"✅ Sẵn sàng với {len(scenes)} cảnh và {len(image_paths)} ảnh")
    
    # Tạo Flow Integration
    flow_integration = FlowIntegration()
    
    # Chuẩn bị dữ liệu cho Flow
    flow_data = flow_integration.prepare_flow_data(scenes, image_paths)
    
    # Hiển thị thông tin
    st.markdown("### 📋 Dữ liệu cho Google Flow")
    st.json(flow_data)
    
    # Download flow data
    flow_json = json.dumps(flow_data, ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 Tải dữ liệu Flow",
        data=flow_json,
        file_name="flow_data.json",
        mime="application/json"
    )
    
    # Google Flow Integration
    st.markdown("### 🌊 Google Flow Video Generator")
    
    # Input Bearer Token
    bearer_token = st.text_input(
        "🔑 Google Flow Bearer Token:",
        placeholder="",
        help="Lấy từ Developer Tools > Network > Headers > Authorization: Bearer [token]"
    )
    
    if bearer_token:
        clean_token = extract_bearer_token_from_cookie(bearer_token)
        
        # Nút tạo video Google Flow
        if st.button("🚀 Tạo Video Google Flow", type="primary", use_container_width=True):
            try:
                # Lấy script data từ session state
                script_data = {
                    "title": st.session_state.get('script_prompt', 'AI Generated Video'),
                    "scenes": scenes
                }
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                flow = GoogleFlowIntegration(clean_token)
                
                status_text.text("🔄 Đang tạo video với Google Flow...")
                
                # Tạo video từ kịch bản và ảnh
                result = flow.create_video_from_script_and_images(script_data, image_paths)
                
                progress_bar.progress(0.5)
                
                if result["success"]:
                    st.success("✅ Video đã được tạo thành công!")
                    
                    media_generation_id = result["media_generation_id"]
                    st.session_state.google_flow_video_id = media_generation_id
                    
                    st.info(f"🎬 Media Generation ID: {media_generation_id}")
                    st.info(f"📊 Status: {result.get('status', 'Unknown')}")
                    st.info(f"🎫 Remaining Credits: {result.get('remaining_credits', 'Unknown')}")
                    
                    # Check video status
                    status_text.text("🔄 Đang kiểm tra trạng thái video...")
                    
                    max_attempts = 30  # 5 minutes max
                    for attempt in range(max_attempts):
                        status_result = flow.check_video_status(media_generation_id)
                        
                        if status_result["success"]:
                            status = status_result["status"]
                            
                            if status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                                video_url = status_result["video_url"]
                                fife_url = status_result.get("fife_url")
                                
                                st.success("🎉 Video đã hoàn thành!")
                                st.info(f"🎫 Remaining Credits: {status_result.get('remaining_credits', 'Unknown')}")
                                
                                if video_url or fife_url:
                                    # Download video
                                    status_text.text("📥 Đang tải video...")
                                    
                                    output_path = f"outputs/videos/google_flow_video_{int(time.time())}.mp4"
                                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                                    
                                    # Sử dụng fife_url nếu có, nếu không thì dùng video_url
                                    download_url = fife_url or video_url
                                    
                                    if flow.download_video(download_url, output_path):
                                        st.success(f"✅ Video đã được tải về: {output_path}")
                                        
                                        # Show video
                                        st.video(output_path)
                                        
                                        # Download button
                                        with open(output_path, 'rb') as f:
                                            video_data = f.read()
                                        
                                        st.download_button(
                                            label="📥 Tải Video",
                                            data=video_data,
                                            file_name=f"google_flow_video_{int(time.time())}.mp4",
                                            mime="video/mp4"
                                        )
                                        
                                        progress_bar.progress(1.0)
                                        status_text.text("✅ Hoàn thành!")
                                        break
                                    else:
                                        st.error("❌ Lỗi tải video")
                                        break
                                else:
                                    st.warning("⚠️ Video hoàn thành nhưng không có URL download")
                                    break
                                    
                            elif status == "MEDIA_GENERATION_STATUS_FAILED":
                                st.error("❌ Video tạo thất bại")
                                break
                            else:
                                # Still processing
                                progress = (attempt + 1) / max_attempts
                                progress_bar.progress(progress)
                                status_text.text(f"🔄 Đang xử lý video... ({status})")
                                time.sleep(10)  # Wait 10 seconds
                        else:
                            st.error(f"❌ Lỗi kiểm tra trạng thái: {status_result['error']}")
                            break
                    else:
                        st.warning("⏰ Video đang xử lý quá lâu. Vui lòng thử lại sau.")
                        
                else:
                    st.error(f"❌ Lỗi tạo video: {result['error']}")
                    
            except Exception as e:
                st.error(f"❌ Lỗi tạo video: {e}")
    
    st.markdown("---")
    
    # Redirect to Google Flow
    st.markdown("### 🌊 Chuyển đến Google Flow")
    st.markdown("""
    <div style="text-align: center; padding: 20px; background-color: #1E1E1E; border-radius: 10px;">
        <h3>🚀 Sẵn sàng tạo video với Google Flow!</h3>
        <p>Bạn có thể sử dụng ảnh và kịch bản đã tạo để tạo video trên Google Flow.</p>
        <a href="https://flow.google.com" target="_blank" style="background-color: #FF6B6B; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px;">
            🌊 Mở Google Flow
        </a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()