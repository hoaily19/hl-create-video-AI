"""
Utils Module
Các hàm phụ trợ, lưu file, convert base64, logs, etc.
"""

import os
import json
import base64
import hashlib
import logging
import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import shutil
import tempfile

# Thiết lập logging
import os
# Tạo thư mục logs nếu chưa tồn tại
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FileManager:
    """Quản lý file và thư mục"""
    
    @staticmethod
    def ensure_dir(path: str) -> str:
        """
        Đảm bảo thư mục tồn tại
        
        Args:
            path: Đường dẫn thư mục
            
        Returns:
            str: Đường dẫn thư mục đã tạo
        """
        os.makedirs(path, exist_ok=True)
        return path
    
    @staticmethod
    def get_unique_filename(base_path: str, extension: str = "") -> str:
        """
        Tạo tên file duy nhất
        
        Args:
            base_path: Đường dẫn cơ sở
            extension: Phần mở rộng file
            
        Returns:
            str: Đường dẫn file duy nhất
        """
        counter = 1
        base_name = base_path
        if extension and not base_path.endswith(extension):
            base_name = f"{base_path}.{extension}"
        
        while os.path.exists(base_name):
            name, ext = os.path.splitext(base_path)
            base_name = f"{name}_{counter}{ext}"
            if extension and not base_name.endswith(extension):
                base_name = f"{name}_{counter}.{extension}"
            counter += 1
        
        return base_name
    
    @staticmethod
    def clean_temp_files(temp_dir: str = "temp", max_age_hours: int = 24):
        """
        Dọn dẹp file tạm cũ
        
        Args:
            temp_dir: Thư mục temp
            max_age_hours: Tuổi tối đa của file (giờ)
        """
        if not os.path.exists(temp_dir):
            return
        
        current_time = datetime.datetime.now()
        max_age = datetime.timedelta(hours=max_age_hours)
        
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                if current_time - file_time > max_age:
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed old temp file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error removing temp file {file_path}: {e}")

class ConfigManager:
    """Quản lý cấu hình"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Tải cấu hình từ file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Cấu hình mặc định
        default_config = {
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
        
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict[str, Any] = None):
        """Lưu cấu hình ra file"""
        if config:
            self.config = config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Config saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Lấy giá trị cấu hình"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Đặt giá trị cấu hình"""
        self.config[key] = value
        self.save_config()

class Base64Converter:
    """Chuyển đổi base64"""
    
    @staticmethod
    def image_to_base64(image_path: str) -> str:
        """
        Chuyển ảnh thành base64
        
        Args:
            image_path: Đường dẫn ảnh
            
        Returns:
            str: Base64 string
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_string = base64.b64encode(image_data).decode('utf-8')
                return base64_string
        except Exception as e:
            logger.error(f"Error converting image to base64: {e}")
            return ""
    
    @staticmethod
    def base64_to_image(base64_string: str, output_path: str) -> bool:
        """
        Chuyển base64 thành ảnh
        
        Args:
            base64_string: Base64 string
            output_path: Đường dẫn lưu ảnh
            
        Returns:
            bool: True nếu thành công
        """
        try:
            image_data = base64.b64decode(base64_string)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            return True
        except Exception as e:
            logger.error(f"Error converting base64 to image: {e}")
            return False

class ProgressTracker:
    """Theo dõi tiến trình"""
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = datetime.datetime.now()
    
    def update(self, step: int = None, message: str = ""):
        """Cập nhật tiến trình"""
        if step is not None:
            self.current_step = step
        else:
            self.current_step += 1
        
        percentage = (self.current_step / self.total_steps) * 100
        elapsed = datetime.datetime.now() - self.start_time
        
        if message:
            logger.info(f"Progress: {percentage:.1f}% - {message}")
        else:
            logger.info(f"Progress: {percentage:.1f}% ({self.current_step}/{self.total_steps})")
    
    def complete(self, message: str = "Completed"):
        """Hoàn thành"""
        total_time = datetime.datetime.now() - self.start_time
        logger.info(f"{message} in {total_time.total_seconds():.2f} seconds")

class DataValidator:
    """Kiểm tra dữ liệu"""
    
    @staticmethod
    def validate_scenes(scenes: List[Dict]) -> bool:
        """
        Kiểm tra tính hợp lệ của scenes
        
        Args:
            scenes: Danh sách scenes
            
        Returns:
            bool: True nếu hợp lệ
        """
        if not scenes or not isinstance(scenes, list):
            return False
        
        required_fields = ["title", "description", "image_prompt"]
        
        for i, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                logger.error(f"Scene {i} is not a dictionary")
                return False
            
            for field in required_fields:
                if field not in scene or not scene[field]:
                    logger.error(f"Scene {i} missing required field: {field}")
                    return False
        
        return True
    
    @staticmethod
    def validate_image_paths(image_paths: List[str]) -> List[str]:
        """
        Kiểm tra và lọc các đường dẫn ảnh hợp lệ
        
        Args:
            image_paths: Danh sách đường dẫn ảnh
            
        Returns:
            List[str]: Danh sách đường dẫn hợp lệ
        """
        valid_paths = []
        
        for path in image_paths:
            if os.path.exists(path) and os.path.isfile(path):
                # Kiểm tra extension
                ext = os.path.splitext(path)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                    valid_paths.append(path)
                else:
                    logger.warning(f"Invalid image format: {path}")
            else:
                logger.warning(f"Image file not found: {path}")
        
        return valid_paths

class ProjectManager:
    """Quản lý dự án"""
    
    def __init__(self, project_name: str = None):
        self.project_name = project_name or f"project_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.project_dir = f"outputs/projects/{self.project_name}"
        self.ensure_project_structure()
    
    def ensure_project_structure(self):
        """Tạo cấu trúc thư mục dự án"""
        dirs = [
            self.project_dir,
            f"{self.project_dir}/images",
            f"{self.project_dir}/videos", 
            f"{self.project_dir}/audio",
            f"{self.project_dir}/scripts",
            f"{self.project_dir}/temp"
        ]
        
        for dir_path in dirs:
            FileManager.ensure_dir(dir_path)
    
    def save_project_info(self, info: Dict[str, Any]):
        """Lưu thông tin dự án"""
        info_file = f"{self.project_dir}/project_info.json"
        info["created_at"] = datetime.datetime.now().isoformat()
        info["project_name"] = self.project_name
        
        try:
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
            logger.info(f"Project info saved: {info_file}")
        except Exception as e:
            logger.error(f"Error saving project info: {e}")
    
    def get_project_info(self) -> Dict[str, Any]:
        """Lấy thông tin dự án"""
        info_file = f"{self.project_dir}/project_info.json"
        
        if os.path.exists(info_file):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading project info: {e}")
        
        return {"project_name": self.project_name}
    
    def cleanup_project(self):
        """Dọn dẹp dự án"""
        try:
            shutil.rmtree(self.project_dir)
            logger.info(f"Project cleaned up: {self.project_name}")
        except Exception as e:
            logger.error(f"Error cleaning up project: {e}")

class ErrorHandler:
    """Xử lý lỗi"""
    
    @staticmethod
    def handle_api_error(error: Exception, provider: str) -> str:
        """
        Xử lý lỗi API
        
        Args:
            error: Exception object
            provider: Tên provider
            
        Returns:
            str: Thông báo lỗi thân thiện
        """
        error_msg = str(error).lower()
        
        if "rate limit" in error_msg or "quota" in error_msg:
            return f"Đã vượt quá giới hạn API của {provider}. Vui lòng thử lại sau."
        elif "invalid api key" in error_msg or "unauthorized" in error_msg:
            return f"API key không hợp lệ cho {provider}. Vui lòng kiểm tra lại."
        elif "network" in error_msg or "connection" in error_msg:
            return f"Lỗi kết nối mạng. Vui lòng kiểm tra internet và thử lại."
        elif "timeout" in error_msg:
            return f"Request quá lâu. Vui lòng thử lại."
        else:
            return f"Lỗi không xác định từ {provider}: {str(error)}"
    
    @staticmethod
    def log_error(error: Exception, context: str = ""):
        """Ghi log lỗi"""
        logger.error(f"Error in {context}: {str(error)}", exc_info=True)

# Hàm tiện ích
def setup_logging(log_level: str = "INFO", log_file: str = "logs/app.log"):
    """Thiết lập logging"""
    FileManager.ensure_dir("logs")
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def get_file_hash(file_path: str) -> str:
    """Tính hash của file"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return ""

def format_duration(seconds: float) -> str:
    """Format thời lượng thành string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def format_file_size(bytes_size: int) -> str:
    """Format kích thước file"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

if __name__ == "__main__":
    # Test utils
    setup_logging()
    
    # Test FileManager
    FileManager.ensure_dir("test_dir")
    unique_file = FileManager.get_unique_filename("test_file.txt")
    print(f"Unique filename: {unique_file}")
    
    # Test ConfigManager
    config = ConfigManager("test_config.json")
    config.set("test_key", "test_value")
    print(f"Config value: {config.get('test_key')}")
    
    # Test ProgressTracker
    tracker = ProgressTracker(5)
    for i in range(5):
        tracker.update(message=f"Step {i+1}")
    tracker.complete("Test completed")
    
    # Cleanup
    os.remove("test_config.json")
    shutil.rmtree("test_dir")
    print("Test completed successfully")
