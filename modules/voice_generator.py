"""
Voice Generator Module
Tạo giọng đọc (TTS) từ text sử dụng các API khác nhau
"""

import os
import logging
import asyncio
import edge_tts
import openai
from typing import Optional, List, Dict
import tempfile
import json
from .api_manager import api_manager

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceGenerator:
    def __init__(self, provider: str = "edge", api_key: Optional[str] = None):
        """
        Khởi tạo VoiceGenerator
        
        Args:
            provider: Nhà cung cấp TTS ("edge", "openai", "gtts")
            api_key: API key (cho OpenAI)
        """
        self.provider = provider.lower()
        self.api_key = api_key or api_manager.get_api_key(self.provider)
        
        if self.provider == "openai":
            if not self.api_key:
                raise ValueError("OpenAI API key is required. Set API key in config or pass api_key parameter.")
            # OpenAI API key sẽ được sử dụng trong client initialization
    
    def generate_voice(self, text: str, output_path: str, 
                      voice: str = "vi-VN-HoaiMyNeural", 
                      rate: str = "+0%", 
                      pitch: str = "+0Hz") -> str:
        """
        Tạo file audio từ text với fallback mechanism
        
        Args:
            text: Văn bản cần chuyển thành giọng nói
            output_path: Đường dẫn lưu file audio
            voice: Giọng nói (tùy thuộc vào provider)
            rate: Tốc độ nói
            pitch: Cao độ giọng nói
            
        Returns:
            str: Đường dẫn file audio đã tạo
        """
        # Đảm bảo text là string và không rỗng
        if not text:
            raise ValueError("Text cannot be empty")
        
        text = str(text).strip()
        if not text:
            raise ValueError("Text cannot be empty after stripping")
        
        # Đảm bảo thư mục output tồn tại
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Danh sách providers để thử (với fallback)
        providers_to_try = []
        
        if self.provider == "edge":
            providers_to_try = ["edge", "elevenlabs", "gtts", "openai", "azure"]
        elif self.provider == "openai":
            providers_to_try = ["openai", "elevenlabs", "gtts", "edge", "azure"]
        elif self.provider == "gtts":
            providers_to_try = ["gtts", "elevenlabs", "edge", "openai", "azure"]
        elif self.provider == "azure":
            providers_to_try = ["azure", "elevenlabs", "gtts", "edge", "openai"]
        elif self.provider == "elevenlabs":
            providers_to_try = ["elevenlabs", "edge", "gtts", "openai", "azure"]
        else:
            providers_to_try = ["elevenlabs", "gtts", "edge", "openai", "azure"]
        
        # Thử từng provider cho đến khi thành công
        last_error = None
        for provider in providers_to_try:
            try:
                logger.info(f"Trying TTS provider: {provider}")
                
                if provider == "edge":
                    return self._generate_edge_tts(text, output_path, voice, rate, pitch)
                elif provider == "openai":
                    return self._generate_openai_tts(text, output_path, voice)
                elif provider == "gtts":
                    return self._generate_gtts(text, output_path, voice)
                elif provider == "azure":
                    return self._generate_azure_tts(text, output_path, voice, rate, pitch)
                elif provider == "elevenlabs":
                    return self._generate_elevenlabs_tts(text, output_path, voice)
                    
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}")
                last_error = e
                continue
        
        # Nếu tất cả providers đều thất bại
        raise Exception(f"All TTS providers failed. Last error: {last_error}")
    
    def _generate_edge_tts(self, text: str, output_path: str, voice: str, rate: str, pitch: str) -> str:
        """Tạo giọng nói bằng Edge TTS (miễn phí) với header trình duyệt Edge"""
        try:
            logger.info(f"Generating voice with Edge TTS: {str(text)[:50]}...")
            
            # Thử với các voice khác nhau nếu voice chính thất bại
            voices_to_try = [voice, "vi-VN-HoaiMyNeural", "vi-VN-HoaiMyNeural", "en-US-AriaNeural"]
            
            for current_voice in voices_to_try:
                try:
                    # Tạo audio với header trình duyệt Edge (cách 2)
                    async def _generate():
                        communicate = edge_tts.Communicate(
                            text=text,
                            voice=current_voice,
                            pitch=pitch,
                            rate=rate
                        )
                        await communicate.save(output_path)
                    
                    # Chạy async function với timeout
                    try:
                        # Sử dụng asyncio.run() trong thread riêng để tránh conflict
                        import concurrent.futures
                        import threading
                        
                        def run_async():
                            return asyncio.run(asyncio.wait_for(_generate(), timeout=30))
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_async)
                            future.result(timeout=35)  # Timeout lớn hơn một chút
                            
                    except (asyncio.TimeoutError, concurrent.futures.TimeoutError):
                        logger.warning(f"Edge TTS timeout for voice {current_voice}")
                        continue
                    
                    logger.info(f"Voice generated with {current_voice}: {output_path}")
                    return output_path
                    
                except Exception as voice_error:
                    logger.warning(f"Edge TTS failed with voice {current_voice}: {voice_error}")
                    if "403" in str(voice_error) or "Invalid response status" in str(voice_error):
                        logger.warning("Edge TTS 403 error - trying next voice")
                        continue
                    else:
                        raise voice_error
            
            # Nếu tất cả voices đều thất bại
            raise Exception("All Edge TTS voices failed")
            
        except Exception as e:
            logger.error(f"Error generating Edge TTS: {e}")
            raise
    
    def _generate_openai_tts(self, text: str, output_path: str, voice: str) -> str:
        """Tạo giọng nói bằng OpenAI TTS"""
        try:
            logger.info(f"Generating voice with OpenAI TTS: {str(text)[:50]}...")
            
            # Lấy cấu hình từ api_manager
            config = api_manager.get_provider_config("openai")
            model = config.get("tts_model", "tts-1")
            default_voice = config.get("tts_voice", "alloy")
            
            # Map voice names
            voice_map = {
                "alloy": "alloy",
                "echo": "echo", 
                "fable": "fable",
                "onyx": "onyx",
                "nova": "nova",
                "shimmer": "shimmer"
            }
            
            openai_voice = voice_map.get(voice, default_voice)
            
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.audio.speech.create(
                model=model,
                voice=openai_voice,
                input=text
            )
            
            # Lưu audio
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Voice generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating OpenAI TTS: {e}")
            raise
    
    def _generate_gtts(self, text: str, output_path: str, voice: str) -> str:
        """Tạo giọng nói bằng Google TTS"""
        try:
            from gtts import gTTS
            
            logger.info(f"Generating voice with Google TTS: {str(text)[:50]}...")
            
            # Map voice to language
            voice_map = {
                "vi": "vi",
                "en": "en",
                "en-us": "en",
                "en-gb": "en"
            }
            
            lang = voice_map.get(voice, "vi")
            
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_path)
            
            logger.info(f"Voice generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating Google TTS: {e}")
            raise
    
    def _generate_azure_tts(self, text: str, output_path: str, voice: str, rate: str, pitch: str) -> str:
        """Tạo giọng nói bằng Azure Speech Service"""
        try:
            logger.info(f"Generating voice with Azure TTS: {str(text)[:50]}...")
            
            # Import Azure Speech SDK
            try:
                import azure.cognitiveservices.speech as speechsdk
            except ImportError:
                logger.error("Azure Speech SDK not installed. Install with: pip install azure-cognitiveservices-speech")
                raise ImportError("Azure Speech SDK not installed. Install with: pip install azure-cognitiveservices-speech")
            
            # Lấy cấu hình Azure
            config = api_manager.get_provider_config("azure")
            region = config.get("region", "eastus")
            default_voice = config.get("default_voice", "vi-VN-HoaiMyNeural")
            default_rate = config.get("default_rate", "+0%")
            default_pitch = config.get("default_pitch", "+0Hz")
            
            # Cấu hình Azure Speech
            speech_config = speechsdk.SpeechConfig(
                subscription=self.api_key,
                region=region
            )
            
            # Cấu hình giọng nói
            selected_voice = voice or default_voice
            speech_config.speech_synthesis_voice_name = selected_voice
            
            # Cấu hình SSML cho rate và pitch
            ssml_text = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="vi-VN">
                <voice name="{selected_voice}">
                    <prosody rate="{rate or default_rate}" pitch="{pitch or default_pitch}">
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            # Cấu hình audio output
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
            
            # Tạo synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            
            # Thực hiện synthesis
            result = synthesizer.speak_ssml_async(ssml_text).get()
            
            # Kiểm tra kết quả
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"Azure TTS audio saved to: {output_path}")
                return output_path
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"Azure TTS canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Error details: {cancellation_details.error_details}")
                raise Exception(f"Azure TTS canceled: {cancellation_details.reason}")
            else:
                raise Exception(f"Azure TTS failed with reason: {result.reason}")
                
        except Exception as e:
            logger.error(f"Error generating Azure TTS: {e}")
            raise
    
    def generate_voice_for_scenes(self, scenes: List[Dict], output_dir: str = "outputs/audio",
                                voice: str = "vi-VN-HoaiMyNeural") -> List[str]:
        """
        Tạo giọng nói cho từng cảnh
        
        Args:
            scenes: Danh sách các cảnh từ script generator
            output_dir: Thư mục lưu audio
            voice: Giọng nói
            
        Returns:
            List[str]: Danh sách đường dẫn các file audio
        """
        os.makedirs(output_dir, exist_ok=True)
        audio_paths = []
        
        for i, scene in enumerate(scenes):
            # Tạo text từ description
            text = f"{scene.get('title', '')}. {scene.get('description', '')}"
            
            # Tạo file audio
            audio_path = os.path.join(output_dir, f"scene_{i+1:02d}.mp3")
            
            try:
                self.generate_voice(text, audio_path, voice)
                audio_paths.append(audio_path)
                logger.info(f"Generated voice for scene {i+1}/{len(scenes)}")
                
            except Exception as e:
                logger.error(f"Failed to generate voice for scene {i+1}: {e}")
                audio_paths.append(None)
        
        return audio_paths
    
    def _generate_elevenlabs_tts(self, text: str, output_path: str, voice: str) -> str:
        """Tạo giọng nói bằng ElevenLabs TTS"""
        try:
            logger.info(f"Generating voice with ElevenLabs TTS: {str(text)[:50]}...")
            
            # Import ElevenLabs
            try:
                import requests
            except ImportError:
                logger.error("requests library not installed. Install with: pip install requests")
                raise ImportError("requests library not installed. Install with: pip install requests")
            
            # Lấy cấu hình ElevenLabs
            config = api_manager.get_provider_config("elevenlabs")
            model = config.get("model", "eleven_multilingual_v2")
            default_voice = config.get("default_voice", "21m00Tcm4TlvDq8ikWAM")
            default_stability = config.get("default_stability", 0.5)
            default_similarity_boost = config.get("default_similarity_boost", 0.5)
            default_style = config.get("default_style", 0.0)
            
            # Cấu hình voice
            selected_voice = voice or default_voice
            
            # ElevenLabs API URL
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{selected_voice}"
            
            # Headers
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            # Voice settings
            voice_settings = config.get("voice_settings", {})
            stability = voice_settings.get("stability", default_stability)
            similarity_boost = voice_settings.get("similarity_boost", default_similarity_boost)
            style = voice_settings.get("style", default_style)
            use_speaker_boost = voice_settings.get("use_speaker_boost", True)
            
            # Data payload
            data = {
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
                }
            }
            
            # Gửi request
            response = requests.post(url, json=data, headers=headers, timeout=60)
            response.raise_for_status()
            
            # Lưu audio
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"ElevenLabs TTS audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating ElevenLabs TTS: {e}")
            raise
    
    def get_available_voices(self) -> Dict[str, List[str]]:
        """
        Lấy danh sách giọng nói có sẵn
        
        Returns:
            Dict: Danh sách giọng nói theo provider
        """
        # Lấy từ config nếu có
        config_voices = api_manager.config.get("available_voices", {})
        if config_voices:
            return config_voices
        
        # Fallback voices
        voices = {
            "edge": [
                "vi-VN-HoaiMyNeural",
                "vi-VN-NamMinhNeural", 
                "vi-VN-ThanhDatNeural",
                "vi-VN-LinhNeural",
                "en-US-AriaNeural",
                "en-US-JennyNeural",
                "en-US-GuyNeural",
                "en-GB-SoniaNeural",
                "en-GB-RyanNeural"
            ],
            "openai": [
                "alloy",
                "echo",
                "fable", 
                "onyx",
                "nova",
                "shimmer"
            ],
            "gtts": [
                "vi",
                "en",
                "en-us",
                "en-gb"
            ],
            "azure": [
                "vi-VN-HoaiMyNeural",
                "vi-VN-NamMinhNeural",
                "vi-VN-ThanhDatNeural",
                "vi-VN-LinhNeural",
                "en-US-AriaNeural",
                "en-US-JennyNeural",
                "en-US-GuyNeural",
                "en-US-DavisNeural",
                "en-US-EmmaNeural",
                "en-US-BrianNeural",
                "en-GB-SoniaNeural",
                "en-GB-RyanNeural",
                "en-GB-LibbyNeural",
                "en-GB-MaisieNeural"
            ]
        }
        
        return voices
    
    def create_narration_script(self, scenes: List[Dict], style: str = "cinematic") -> List[str]:
        """
        Tạo script narration cho từng cảnh
        
        Args:
            scenes: Danh sách các cảnh
            style: Phong cách narration (cinematic, documentary, educational)
            
        Returns:
            List[str]: Danh sách text narration
        """
        narrations = []
        
        for i, scene in enumerate(scenes):
            title = scene.get('title', f'Scene {i+1}')
            description = scene.get('description', '')
            
            if style == "cinematic":
                narration = f"Trong cảnh này, {description.lower()}"
            elif style == "documentary":
                narration = f"Chúng ta thấy {description.lower()}"
            elif style == "educational":
                narration = f"Hãy quan sát {description.lower()}"
            else:
                narration = f"{title}. {description}"
            
            narrations.append(narration)
        
        return narrations
    
    def combine_audio_files(self, audio_paths: List[str], output_path: str, 
                          fade_duration: float = 0.5) -> str:
        """
        Ghép nhiều file audio thành một
        
        Args:
            audio_paths: Danh sách đường dẫn audio
            output_path: Đường dẫn lưu audio đã ghép
            fade_duration: Thời lượng fade giữa các đoạn
            
        Returns:
            str: Đường dẫn audio đã ghép
        """
        try:
            from moviepy.editor import AudioFileClip, concatenate_audioclips
            
            # Lọc bỏ None values
            valid_paths = [path for path in audio_paths if path and os.path.exists(path)]
            
            if not valid_paths:
                logger.warning("No valid audio files to combine")
                return None
            
            # Load audio clips
            clips = []
            for path in valid_paths:
                clip = AudioFileClip(path)
                clips.append(clip)
            
            # Ghép clips với fade
            if len(clips) > 1:
                # Thêm fade in/out cho clips ở giữa
                for i in range(1, len(clips) - 1):
                    clips[i] = clips[i].fadein(fade_duration).fadeout(fade_duration)
                
                # Fade in cho clip đầu
                clips[0] = clips[0].fadein(fade_duration)
                
                # Fade out cho clip cuối
                clips[-1] = clips[-1].fadeout(fade_duration)
            
            # Ghép tất cả clips
            final_audio = concatenate_audioclips(clips)
            
            # Lưu file
            final_audio.write_audiofile(output_path)
            
            # Cleanup
            final_audio.close()
            for clip in clips:
                clip.close()
            
            logger.info(f"Combined audio saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error combining audio files: {e}")
            raise


# Hàm tiện ích
def generate_voice(text: str, output_path: str, provider: str = "edge", 
                  voice: str = "vi-VN-HoaiMyNeural", **kwargs) -> str:
    """
    Hàm tiện ích để tạo giọng nói nhanh
    
    Args:
        text: Văn bản cần chuyển thành giọng nói
        output_path: Đường dẫn lưu audio
        provider: Nhà cung cấp TTS
        voice: Giọng nói
        **kwargs: Các tham số khác
        
    Returns:
        str: Đường dẫn audio đã tạo
    """
    generator = VoiceGenerator(provider)
    return generator.generate_voice(text, output_path, voice, **kwargs)


if __name__ == "__main__":
    # Test voice generator
    generator = VoiceGenerator("edge")
    
    test_text = "Xin chào, đây là test giọng nói tiếng Việt."
    output_path = "test_voice.mp3"
    
    try:
        result = generator.generate_voice(test_text, output_path)
        print(f"Voice generated successfully: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test available voices
    voices = generator.get_available_voices()
    print("\nAvailable voices:")
    for provider, voice_list in voices.items():
        print(f"{provider}: {voice_list[:3]}...")  # Chỉ hiển thị 3 giọng đầu
