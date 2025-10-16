"""
API Manager Module
Quản lý tất cả API keys và cấu hình cho các AI services
"""

import os
import json
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIManager:
    """Quản lý API keys và cấu hình cho tất cả AI services"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.api_keys = self.config.get("api_keys", {})
        self.default_providers = self.config.get("default_providers", {})
        
        # Load API keys từ environment variables
        self.load_env_keys()
    
    def load_config(self) -> Dict[str, Any]:
        """Tải cấu hình từ file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Cấu hình mặc định
        return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Cấu hình mặc định"""
        return {
            "api_keys": {
                "openai": "",
                "stability": "",
                "replicate": "",
                "huggingface": "",
                "runwayml": "",
                "pika_labs": "",
                "leia_pix": "",
                "midjourney": ""
            },
            "default_providers": {
                "script": "openai",
                "image": "pollinations",
                "voice": "edge",
                "video": "moviepy"
            },
            "openai": {
                "model": "gpt-4o-mini",
                "temperature": 0.8,
                "max_tokens": 2000,
                "image_model": "dall-e-3",
                "image_size": "1024x1024",
                "image_quality": "standard",
                "image_style": "vivid",
                "tts_model": "tts-1",
                "tts_voice": "alloy"
            },
            "stability": {
                "model": "stable-diffusion-xl-1024-v1-0",
                "cfg_scale": 7,
                "steps": 30,
                "samples": 1
            },
            "pollinations": {
                "base_url": "https://image.pollinations.ai/prompt/",
                "default_size": "1024x1024",
                "nologo": True
            },
            "edge_tts": {
                "default_voice": "vi-VN-HoaiMyNeural",
                "default_rate": "+0%",
                "default_pitch": "+0Hz"
            },
            "video": {
                "fps": 24,
                "resolution": [1920, 1080],
                "scene_duration": 3.0,
                "transition_duration": 0.5,
                "output_quality": "high"
            }
        }
    
    def load_env_keys(self):
        """Tải API keys từ environment variables"""
        env_mapping = {
            "OPENAI_API_KEY": "openai",
            "STABILITY_API_KEY": "stability",
            "REPLICATE_API_KEY": "replicate",
            "HUGGINGFACE_API_KEY": "huggingface",
            "RUNWAYML_API_KEY": "runwayml",
            "PIKA_LABS_API_KEY": "pika_labs",
            "LEIA_PIX_API_KEY": "leia_pix",
            "MIDJOURNEY_API_KEY": "midjourney"
        }
        
        for env_var, key_name in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value and not self.api_keys.get(key_name):
                self.api_keys[key_name] = env_value
                logger.info(f"Loaded {key_name} API key from environment")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Lấy API key cho provider
        
        Args:
            provider: Tên provider (openai, stability, etc.)
            
        Returns:
            str: API key hoặc None
        """
        return self.api_keys.get(provider)
    
    def set_api_key(self, provider: str, api_key: str):
        """
        Đặt API key cho provider
        
        Args:
            provider: Tên provider
            api_key: API key
        """
        self.api_keys[provider] = api_key
        self.config["api_keys"][provider] = api_key
        self.save_config()
        logger.info(f"Set API key for {provider}")
    
    def remove_api_key(self, provider: str):
        """
        Xóa API key cho provider
        
        Args:
            provider: Tên provider
        """
        if provider in self.api_keys:
            del self.api_keys[provider]
            self.config["api_keys"][provider] = ""
            self.save_config()
            logger.info(f"Removed API key for {provider}")
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """
        Lấy cấu hình cho provider
        
        Args:
            provider: Tên provider
            
        Returns:
            Dict: Cấu hình provider
        """
        return self.config.get(provider, {})
    
    def get_default_provider(self, service_type: str) -> str:
        """
        Lấy provider mặc định cho service type
        
        Args:
            service_type: Loại service (script, image, voice, video)
            
        Returns:
            str: Tên provider mặc định
        """
        return self.default_providers.get(service_type, "")
    
    def set_default_provider(self, service_type: str, provider: str):
        """
        Đặt provider mặc định cho service type
        
        Args:
            service_type: Loại service
            provider: Tên provider
        """
        self.default_providers[service_type] = provider
        self.config["default_providers"][service_type] = provider
        self.save_config()
        logger.info(f"Set default {service_type} provider to {provider}")
    
    def is_provider_available(self, provider: str) -> bool:
        """
        Kiểm tra provider có sẵn không (có API key hoặc miễn phí)
        
        Args:
            provider: Tên provider
            
        Returns:
            bool: True nếu provider có sẵn
        """
        free_providers = ["pollinations", "edge", "gtts"]
        
        if provider in free_providers:
            return True
        
        return bool(self.get_api_key(provider))
    
    def get_available_providers(self, service_type: str) -> List[str]:
        """
        Lấy danh sách provider có sẵn cho service type
        
        Args:
            service_type: Loại service
            
        Returns:
            List[str]: Danh sách provider có sẵn
        """
        all_providers = {
            "script": ["openai", "anthropic", "google"],
            "image": ["pollinations", "openai", "stability", "replicate", "huggingface"],
            "voice": ["edge", "openai", "gtts"],
            "video": ["moviepy", "runwayml", "pika_labs", "leia_pix"]
        }
        
        providers = all_providers.get(service_type, [])
        available = []
        
        for provider in providers:
            if self.is_provider_available(provider):
                available.append(provider)
        
        return available
    
    def validate_api_key(self, provider: str, api_key: str = None) -> bool:
        """
        Validate API key cho provider
        
        Args:
            provider: Tên provider
            api_key: API key để validate (nếu None sẽ dùng key đã lưu)
            
        Returns:
            bool: True nếu API key hợp lệ
        """
        if api_key is None:
            api_key = self.get_api_key(provider)
        
        if not api_key:
            return False
        
        # Basic validation patterns
        validation_patterns = {
            "openai": r"^sk-[a-zA-Z0-9]{48}$",
            "stability": r"^[a-zA-Z0-9]{32,}$",
            "replicate": r"^r8_[a-zA-Z0-9]{32,}$",
            "huggingface": r"^hf_[a-zA-Z0-9]{34}$"
        }
        
        import re
        pattern = validation_patterns.get(provider)
        if pattern:
            return bool(re.match(pattern, api_key))
        
        # Default: check if not empty
        return len(api_key.strip()) > 0
    
    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """
        Lấy thông tin về provider
        
        Args:
            provider: Tên provider
            
        Returns:
            Dict: Thông tin provider
        """
        provider_info = {
            "openai": {
                "name": "OpenAI",
                "description": "GPT models, DALL-E, TTS",
                "pricing": "Pay per use",
                "free_tier": "Limited",
                "website": "https://openai.com"
            },
            "stability": {
                "name": "Stability AI",
                "description": "Stable Diffusion models",
                "pricing": "Pay per use",
                "free_tier": "Limited",
                "website": "https://stability.ai"
            },
            "pollinations": {
                "name": "Pollinations AI",
                "description": "Free image generation",
                "pricing": "Free",
                "free_tier": "Unlimited",
                "website": "https://pollinations.ai"
            },
            "edge": {
                "name": "Edge TTS",
                "description": "Microsoft Edge TTS",
                "pricing": "Free",
                "free_tier": "Unlimited",
                "website": "https://github.com/rany2/edge-tts"
            },
            "gtts": {
                "name": "Google TTS",
                "description": "Google Text-to-Speech",
                "pricing": "Free",
                "free_tier": "Limited",
                "website": "https://cloud.google.com/text-to-speech"
            },
            "replicate": {
                "name": "Replicate",
                "description": "Various AI models",
                "pricing": "Pay per use",
                "free_tier": "Limited",
                "website": "https://replicate.com"
            },
            "huggingface": {
                "name": "Hugging Face",
                "description": "Open source AI models",
                "pricing": "Free/Paid",
                "free_tier": "Generous",
                "website": "https://huggingface.co"
            }
        }
        
        return provider_info.get(provider, {
            "name": provider.title(),
            "description": "Unknown provider",
            "pricing": "Unknown",
            "free_tier": "Unknown",
            "website": ""
        })
    
    def save_config(self):
        """Lưu cấu hình ra file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Config saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def export_config(self, filepath: str):
        """Xuất cấu hình ra file khác"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Config exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
    
    def import_config(self, filepath: str):
        """Import cấu hình từ file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Merge với config hiện tại
            self.config.update(imported_config)
            self.api_keys = self.config.get("api_keys", {})
            self.default_providers = self.config.get("default_providers", {})
            
            self.save_config()
            logger.info(f"Config imported from {filepath}")
        except Exception as e:
            logger.error(f"Error importing config: {e}")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Lấy tóm tắt trạng thái tất cả providers
        
        Returns:
            Dict: Tóm tắt trạng thái
        """
        summary = {
            "total_providers": 0,
            "available_providers": 0,
            "free_providers": 0,
            "paid_providers": 0,
            "services": {
                "script": {"available": 0, "total": 0},
                "image": {"available": 0, "total": 0},
                "voice": {"available": 0, "total": 0},
                "video": {"available": 0, "total": 0}
            }
        }
        
        all_providers = {
            "script": ["openai", "anthropic", "google"],
            "image": ["pollinations", "openai", "stability", "replicate", "huggingface"],
            "voice": ["edge", "openai", "gtts"],
            "video": ["moviepy", "runwayml", "pika_labs", "leia_pix"]
        }
        
        free_providers = ["pollinations", "edge", "gtts", "moviepy"]
        
        for service_type, providers in all_providers.items():
            summary["services"][service_type]["total"] = len(providers)
            
            for provider in providers:
                summary["total_providers"] += 1
                
                if self.is_provider_available(provider):
                    summary["available_providers"] += 1
                    summary["services"][service_type]["available"] += 1
                
                if provider in free_providers:
                    summary["free_providers"] += 1
                else:
                    summary["paid_providers"] += 1
        
        return summary


# Global instance
api_manager = APIManager()

# Convenience functions
def get_api_key(provider: str) -> Optional[str]:
    """Lấy API key cho provider"""
    return api_manager.get_api_key(provider)

def set_api_key(provider: str, api_key: str):
    """Đặt API key cho provider"""
    api_manager.set_api_key(provider, api_key)

def is_provider_available(provider: str) -> bool:
    """Kiểm tra provider có sẵn không"""
    return api_manager.is_provider_available(provider)

def get_available_providers(service_type: str) -> List[str]:
    """Lấy danh sách provider có sẵn"""
    return api_manager.get_available_providers(service_type)

def get_provider_config(provider: str) -> Dict[str, Any]:
    """Lấy cấu hình provider"""
    return api_manager.get_provider_config(provider)

if __name__ == "__main__":
    # Test API Manager
    manager = APIManager()
    
    print("🔑 API Manager Test")
    print("=" * 30)
    
    # Test status
    status = manager.get_status_summary()
    print(f"Total providers: {status['total_providers']}")
    print(f"Available providers: {status['available_providers']}")
    print(f"Free providers: {status['free_providers']}")
    print(f"Paid providers: {status['paid_providers']}")
    
    # Test available providers
    for service in ["script", "image", "voice", "video"]:
        available = manager.get_available_providers(service)
        print(f"\n{service.title()} providers: {available}")
    
    # Test provider info
    print(f"\nOpenAI info: {manager.get_provider_info('openai')}")
    print(f"Pollinations info: {manager.get_provider_info('pollinations')}")
