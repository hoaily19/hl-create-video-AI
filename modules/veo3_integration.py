"""
VEO3 Integration Module
Tích hợp VEO3 để tạo video chuyển động từ ảnh
"""

import requests
import json
import time
import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import base64
from PIL import Image
import io

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VEO3Integration:
    def __init__(self, cookie: str = None):
        """
        Khởi tạo VEO3 Integration
        
        Args:
            cookie: Cookie string từ VEO3 website
        """
        self.cookie = cookie
        self.base_url = "https://veo3.com"
        self.api_url = "https://api.veo3.com"
        self.session = requests.Session()
        
        if self.cookie:
            self.session.headers.update({
                'Cookie': self.cookie,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/json'
            })
    
    def set_cookie(self, cookie: str):
        """Cập nhật cookie"""
        self.cookie = cookie
        self.session.headers.update({'Cookie': cookie})
        logger.info("VEO3 cookie updated")
    
    def validate_cookie(self) -> bool:
        """Kiểm tra cookie có hợp lệ không"""
        try:
            response = self.session.get(f"{self.api_url}/user/profile", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Cookie validation failed: {e}")
            return False
    
    def generate_video_from_image(self, image_path: str, prompt: str, 
                                duration: int = 5, style: str = "cinematic") -> Dict:
        """
        Tạo video từ ảnh sử dụng VEO3
        
        Args:
            image_path: Đường dẫn ảnh input
            prompt: Mô tả chuyển động muốn tạo
            duration: Thời lượng video (giây)
            style: Phong cách video
            
        Returns:
            Dict: Thông tin video đã tạo
        """
        try:
            logger.info(f"Generating VEO3 video from image: {image_path}")
            
            # Đọc và encode ảnh
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Resize ảnh nếu cần (VEO3 thường yêu cầu ảnh nhỏ hơn)
            image = Image.open(io.BytesIO(image_data))
            if image.size[0] > 1024 or image.size[1] > 1024:
                image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                image_data = buffer.getvalue()
            
            # Encode ảnh thành base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Chuẩn bị payload
            payload = {
                "image": image_base64,
                "prompt": prompt,
                "duration": duration,
                "style": style,
                "quality": "high",
                "fps": 24,
                "resolution": "1024x1024"
            }
            
            # Gửi request tạo video
            response = self.session.post(
                f"{self.api_url}/generate/video",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Video generation started: {result.get('job_id')}")
                return result
            else:
                logger.error(f"VEO3 API error: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error generating VEO3 video: {e}")
            return {"error": str(e)}
    
    def check_video_status(self, job_id: str) -> Dict:
        """Kiểm tra trạng thái video đang được tạo"""
        try:
            response = self.session.get(
                f"{self.api_url}/status/{job_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status check failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error checking video status: {e}")
            return {"error": str(e)}
    
    def download_video(self, video_url: str, output_path: str) -> bool:
        """Tải video về máy"""
        try:
            logger.info(f"Downloading video: {video_url}")
            
            response = self.session.get(video_url, timeout=60)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Video downloaded: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return False
    
    def generate_batch_videos(self, image_paths: List[str], prompts: List[str], 
                            output_dir: str = "outputs/videos") -> List[Dict]:
        """
        Tạo nhiều video cùng lúc
        
        Args:
            image_paths: Danh sách đường dẫn ảnh
            prompts: Danh sách prompt cho từng ảnh
            output_dir: Thư mục lưu video
            
        Returns:
            List[Dict]: Danh sách thông tin video đã tạo
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, (image_path, prompt) in enumerate(zip(image_paths, prompts)):
            try:
                logger.info(f"Generating video {i+1}/{len(image_paths)}")
                
                # Tạo video
                result = self.generate_video_from_image(image_path, prompt)
                
                if "error" not in result:
                    # Chờ video hoàn thành
                    job_id = result.get("job_id")
                    if job_id:
                        video_info = self.wait_for_video_completion(job_id)
                        if video_info and "video_url" in video_info:
                            # Tải video
                            video_filename = f"video_{i+1:02d}.mp4"
                            video_path = os.path.join(output_dir, video_filename)
                            
                            if self.download_video(video_info["video_url"], video_path):
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
                
                # Nghỉ giữa các request để tránh rate limit
                if i < len(image_paths) - 1:
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Error generating video {i+1}: {e}")
                results.append({"error": f"Video {i+1} error: {str(e)}"})
        
        return results
    
    def wait_for_video_completion(self, job_id: str, max_wait: int = 300) -> Optional[Dict]:
        """
        Chờ video hoàn thành
        
        Args:
            job_id: ID của job tạo video
            max_wait: Thời gian chờ tối đa (giây)
            
        Returns:
            Dict: Thông tin video hoàn thành hoặc None
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = self.check_video_status(job_id)
            
            if "error" in status:
                logger.error(f"Status check error: {status['error']}")
                return None
            
            if status.get("status") == "completed":
                logger.info(f"Video completed: {job_id}")
                return status
            elif status.get("status") == "failed":
                logger.error(f"Video generation failed: {job_id}")
                return None
            else:
                logger.info(f"Video status: {status.get('status', 'unknown')}")
                time.sleep(10)  # Chờ 10 giây trước khi kiểm tra lại
        
        logger.warning(f"Video generation timeout: {job_id}")
        return None
    
    def get_video_list(self) -> List[Dict]:
        """Lấy danh sách video đã tạo"""
        try:
            response = self.session.get(f"{self.api_url}/videos", timeout=10)
            
            if response.status_code == 200:
                return response.json().get("videos", [])
            else:
                logger.error(f"Failed to get video list: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting video list: {e}")
            return []
    
    def delete_video(self, video_id: str) -> bool:
        """Xóa video"""
        try:
            response = self.session.delete(f"{self.api_url}/videos/{video_id}", timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error deleting video: {e}")
            return False


# Hàm tiện ích
def create_veo3_integration(cookie: str = None) -> VEO3Integration:
    """Tạo instance VEO3Integration"""
    return VEO3Integration(cookie)


def extract_cookie_from_browser(cookie_string: str) -> str:
    """
    Trích xuất cookie từ browser string
    
    Args:
        cookie_string: Cookie string từ browser
        
    Returns:
        str: Cookie đã được format
    """
    # Xử lý cookie string từ browser
    if "Cookie:" in cookie_string:
        cookie_string = cookie_string.split("Cookie:")[1].strip()
    
    # Loại bỏ các ký tự không cần thiết
    cookie_string = cookie_string.replace("\\n", "").replace("\\r", "")
    
    return cookie_string


if __name__ == "__main__":
    # Test VEO3 integration
    cookie = "your_veo3_cookie_here"
    veo3 = VEO3Integration(cookie)
    
    if veo3.validate_cookie():
        print("✅ VEO3 cookie is valid")
        
        # Test tạo video
        image_path = "outputs/images/scene_01.png"
        if os.path.exists(image_path):
            result = veo3.generate_video_from_image(
                image_path, 
                "A peaceful village scene with gentle camera movement",
                duration=5
            )
            print(f"Video generation result: {result}")
    else:
        print("❌ VEO3 cookie is invalid")
