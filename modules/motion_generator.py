"""
Motion Generator Module
Tạo chuyển động từ ảnh tĩnh sử dụng các API AI
"""

import os
import requests
import base64
import time
import logging
from typing import Optional, List, Dict, Union
from PIL import Image
import io
from .api_manager import api_manager

logger = logging.getLogger(__name__)

class MotionGenerator:
    """
    Tạo chuyển động từ ảnh tĩnh
    """
    
    def __init__(self, provider: str = "google_flow", api_key: Optional[str] = None):
        """
        Khởi tạo Motion Generator
        
        Args:
            provider: Provider để tạo chuyển động (google_flow, runwayml, pika_labs, leia_pix)
            api_key: API key (nếu không có sẽ lấy từ api_manager)
        """
        self.provider = provider.lower()
        self.api_key = api_key or api_manager.get_api_key(self.provider)
        
        if not self.api_key and self.provider not in ["free"]:
            raise ValueError(f"{self.provider.title()} API key is required. Set API key in config or pass api_key parameter.")
    
    def generate_motion(self, image_path: str, output_path: str, 
                       motion_type: str = "subtle", duration: float = 3.0) -> str:
        """
        Tạo chuyển động từ ảnh tĩnh
        
        Args:
            image_path: Đường dẫn ảnh đầu vào
            output_path: Đường dẫn video đầu ra
            motion_type: Loại chuyển động (subtle, medium, strong)
            duration: Thời lượng video (giây)
            
        Returns:
            str: Đường dẫn file video đã tạo
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if self.provider == "google_flow":
            return self._generate_google_flow_motion(image_path, output_path, motion_type, duration)
        elif self.provider == "runwayml":
            return self._generate_runwayml_motion(image_path, output_path, motion_type, duration)
        elif self.provider == "pika_labs":
            return self._generate_pika_motion(image_path, output_path, motion_type, duration)
        elif self.provider == "leia_pix":
            return self._generate_leia_motion(image_path, output_path, motion_type, duration)
        elif self.provider == "free":
            return self._generate_free_motion(image_path, output_path, motion_type, duration)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _generate_google_flow_motion(self, image_path: str, output_path: str, 
                                   motion_type: str, duration: float) -> str:
        """
        Tạo chuyển động bằng Google Flow API
        """
        try:
            # Google Flow API endpoint (giả định - cần cập nhật khi có API chính thức)
            api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent"
            
            # Đọc và encode ảnh
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Tạo prompt cho motion
            motion_prompts = {
                "subtle": "Create a subtle, gentle motion effect",
                "medium": "Create a moderate motion effect with some movement",
                "strong": "Create a strong, dynamic motion effect"
            }
            
            prompt = motion_prompts.get(motion_type, motion_prompts["subtle"])
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"{prompt}. Duration: {duration} seconds. Create smooth, cinematic motion from this static image."
                    }, {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_data
                        }
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1024
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Xử lý response (cần cập nhật theo API thực tế)
            result = response.json()
            
            # Tạm thời tạo placeholder video
            return self._create_placeholder_motion_video(image_path, output_path, duration)
            
        except Exception as e:
            logger.error(f"Error generating Google Flow motion: {e}")
            return self._create_placeholder_motion_video(image_path, output_path, duration)
    
    def _generate_runwayml_motion(self, image_path: str, output_path: str, 
                                motion_type: str, duration: float) -> str:
        """
        Tạo chuyển động bằng RunwayML Gen-3 API (VEO3 style)
        """
        try:
            # RunwayML Gen-3 API endpoint
            api_url = "https://api.runwayml.com/v1/image_to_video"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Đọc ảnh
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Cấu hình motion intensity
            motion_config = {
                "subtle": {"motion_intensity": 0.3, "camera_motion": "subtle"},
                "medium": {"motion_intensity": 0.6, "camera_motion": "medium"},
                "strong": {"motion_intensity": 0.9, "camera_motion": "strong"}
            }
            
            config = motion_config.get(motion_type, motion_config["medium"])
            
            payload = {
                "image": image_data,
                "model": "gen3a_turbo",
                "motion_intensity": config["motion_intensity"],
                "camera_motion": config["camera_motion"],
                "duration": min(duration, 10.0),  # RunwayML giới hạn 10s
                "seed": None,  # Random seed
                "aspect_ratio": "16:9"
            }
            
            logger.info(f"Calling RunwayML API with motion_type: {motion_type}")
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"RunwayML response: {result}")
            
            # Xử lý response
            if 'id' in result:
                # Polling để lấy kết quả
                task_id = result['id']
                return self._poll_runwayml_result(task_id, output_path)
            elif 'video_url' in result:
                # Tải video trực tiếp
                video_response = requests.get(result['video_url'])
                video_response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(video_response.content)
                
                logger.info(f"RunwayML motion video saved to: {output_path}")
                return output_path
            else:
                raise Exception(f"No video URL or task ID in response: {result}")
                
        except Exception as e:
            logger.error(f"Error generating RunwayML motion: {e}")
            return self._create_placeholder_motion_video(image_path, output_path, duration)
    
    def _poll_runwayml_result(self, task_id: str, output_path: str, max_attempts: int = 30) -> str:
        """
        Polling kết quả từ RunwayML API
        """
        api_url = f"https://api.runwayml.com/v1/tasks/{task_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(api_url, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                status = result.get('status', 'unknown')
                
                logger.info(f"RunwayML task {task_id} status: {status} (attempt {attempt + 1})")
                
                if status == 'SUCCEEDED':
                    if 'output' in result and 'video_url' in result['output']:
                        video_url = result['output']['video_url']
                        
                        # Tải video
                        video_response = requests.get(video_url)
                        video_response.raise_for_status()
                        
                        with open(output_path, 'wb') as f:
                            f.write(video_response.content)
                        
                        logger.info(f"RunwayML motion video saved to: {output_path}")
                        return output_path
                    else:
                        raise Exception("No video URL in successful response")
                        
                elif status == 'FAILED':
                    error_msg = result.get('error', 'Unknown error')
                    raise Exception(f"RunwayML task failed: {error_msg}")
                    
                elif status in ['PENDING', 'RUNNING']:
                    time.sleep(5)  # Chờ 5 giây
                    continue
                else:
                    logger.warning(f"Unknown status: {status}")
                    time.sleep(5)
                    continue
                    
            except Exception as e:
                logger.error(f"Error polling RunwayML result: {e}")
                if attempt == max_attempts - 1:
                    raise
                time.sleep(5)
        
        raise Exception("RunwayML task timeout")
    
    def _generate_pika_motion(self, image_path: str, output_path: str, 
                            motion_type: str, duration: float) -> str:
        """
        Tạo chuyển động bằng Pika Labs API (VEO3 style)
        """
        try:
            # Pika Labs API endpoint
            api_url = "https://api.pika.art/v1/generate"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Đọc ảnh
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Cấu hình motion prompts
            motion_prompts = {
                "subtle": "Subtle, gentle movement with soft camera motion",
                "medium": "Moderate movement with smooth camera transitions",
                "strong": "Dynamic movement with dramatic camera motion"
            }
            
            prompt = motion_prompts.get(motion_type, motion_prompts["medium"])
            
            payload = {
                "image": image_data,
                "prompt": prompt,
                "duration": min(duration, 4.0),  # Pika Labs giới hạn 4s
                "style": "cinematic",
                "aspect_ratio": "16:9",
                "motion_intensity": motion_type,
                "seed": None
            }
            
            logger.info(f"Calling Pika Labs API with motion_type: {motion_type}")
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Pika Labs response: {result}")
            
            # Xử lý response
            if 'task_id' in result:
                # Polling để lấy kết quả
                task_id = result['task_id']
                return self._poll_pika_result(task_id, output_path)
            elif 'video_url' in result:
                # Tải video trực tiếp
                video_response = requests.get(result['video_url'])
                video_response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(video_response.content)
                
                logger.info(f"Pika Labs motion video saved to: {output_path}")
                return output_path
            else:
                raise Exception(f"No video URL or task ID in response: {result}")
                
        except Exception as e:
            logger.error(f"Error generating Pika Labs motion: {e}")
            return self._create_placeholder_motion_video(image_path, output_path, duration)
    
    def _poll_pika_result(self, task_id: str, output_path: str, max_attempts: int = 20) -> str:
        """
        Polling kết quả từ Pika Labs API
        """
        api_url = f"https://api.pika.art/v1/tasks/{task_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(api_url, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                status = result.get('status', 'unknown')
                
                logger.info(f"Pika Labs task {task_id} status: {status} (attempt {attempt + 1})")
                
                if status == 'completed':
                    if 'video_url' in result:
                        video_url = result['video_url']
                        
                        # Tải video
                        video_response = requests.get(video_url)
                        video_response.raise_for_status()
                        
                        with open(output_path, 'wb') as f:
                            f.write(video_response.content)
                        
                        logger.info(f"Pika Labs motion video saved to: {output_path}")
                        return output_path
                    else:
                        raise Exception("No video URL in completed response")
                        
                elif status == 'failed':
                    error_msg = result.get('error', 'Unknown error')
                    raise Exception(f"Pika Labs task failed: {error_msg}")
                    
                elif status in ['pending', 'processing']:
                    time.sleep(3)  # Chờ 3 giây
                    continue
                else:
                    logger.warning(f"Unknown status: {status}")
                    time.sleep(3)
                    continue
                    
            except Exception as e:
                logger.error(f"Error polling Pika Labs result: {e}")
                if attempt == max_attempts - 1:
                    raise
                time.sleep(3)
        
        raise Exception("Pika Labs task timeout")
    
    def _generate_leia_motion(self, image_path: str, output_path: str, 
                            motion_type: str, duration: float) -> str:
        """
        Tạo chuyển động bằng LeiaPix API
        """
        try:
            # LeiaPix API endpoint
            api_url = "https://api.leiapix.com/v1/convert"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Đọc ảnh
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            payload = {
                "image": image_data,
                "motion_intensity": motion_type,
                "duration": duration
            }
            
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Tải video kết quả
            if 'video_url' in result:
                video_response = requests.get(result['video_url'])
                video_response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(video_response.content)
                
                logger.info(f"LeiaPix motion video saved to: {output_path}")
                return output_path
            else:
                raise Exception("No video URL in response")
                
        except Exception as e:
            logger.error(f"Error generating LeiaPix motion: {e}")
            return self._create_placeholder_motion_video(image_path, output_path, duration)
    
    def _generate_free_motion(self, image_path: str, output_path: str, 
                            motion_type: str, duration: float) -> str:
        """
        Tạo chuyển động miễn phí (placeholder)
        """
        logger.info("Generating free motion using placeholder")
        return self._create_placeholder_motion_video(image_path, output_path, duration)
    
    def _create_placeholder_motion_video(self, image_path: str, output_path: str, 
                                       duration: float) -> str:
        """
        Tạo video với chuyển động thực tế cho nhân vật
        """
        try:
            from moviepy.editor import ImageClip, CompositeVideoClip
            from moviepy.video.fx.all import resize, fadein, fadeout
            import numpy as np
            
            # Tạo clip từ ảnh
            base_clip = ImageClip(image_path, duration=duration)
            
            # Tạo chuyển động Ken Burns effect (zoom + pan)
            def make_frame(t):
                # Tính toán zoom factor
                zoom_factor = 1.0 + 0.15 * (t / duration)  # Zoom từ 1.0 đến 1.15
                
                # Tính toán pan offset
                pan_x = int(50 * np.sin(2 * np.pi * t / duration))  # Pan ngang
                pan_y = int(30 * np.cos(2 * np.pi * t / duration))  # Pan dọc
                
                # Resize và crop để tạo hiệu ứng zoom + pan
                resized = base_clip.resize(zoom_factor)
                
                # Crop để tạo pan effect
                w, h = base_clip.size
                new_w, new_h = resized.size
                
                # Tính toán crop area
                crop_x = max(0, min(pan_x + (new_w - w) // 2, new_w - w))
                crop_y = max(0, min(pan_y + (new_h - h) // 2, new_h - h))
                
                # Crop frame
                frame = resized.get_frame(t)
                if len(frame.shape) == 3:
                    cropped = frame[crop_y:crop_y+h, crop_x:crop_x+w]
                else:
                    cropped = frame[crop_y:crop_y+h, crop_x:crop_x+w]
                
                return cropped
            
            # Tạo clip với chuyển động
            motion_clip = base_clip.fl(lambda gf, t: make_frame(t))
            
            # Thêm fade in/out
            if duration > 1:
                motion_clip = motion_clip.fadein(0.3).fadeout(0.3)
            
            # Xuất video với chất lượng cao
            motion_clip.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio=False,
                verbose=False,
                logger=None,
                bitrate="2000k"  # Bitrate cao hơn để tránh nhiễu
            )
            
            # Giải phóng memory
            base_clip.close()
            motion_clip.close()
            
            logger.info(f"Motion video created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating motion video: {e}")
            # Fallback: tạo video đơn giản
            return self._create_simple_video_from_image(image_path, output_path, duration)
    
    def _create_simple_video_from_image(self, image_path: str, output_path: str, 
                                      duration: float) -> str:
        """
        Tạo video đơn giản từ ảnh (fallback)
        """
        try:
            from moviepy.editor import ImageClip
            
            clip = ImageClip(image_path, duration=duration)
            clip.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio=False,
                verbose=False,
                logger=None
            )
            
            logger.info(f"Simple video created from image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating simple video: {e}")
            raise
    
    def batch_generate_motion(self, image_paths: List[str], output_dir: str, 
                            motion_type: str = "subtle", duration: float = 3.0) -> List[str]:
        """
        Tạo chuyển động cho nhiều ảnh
        
        Args:
            image_paths: Danh sách đường dẫn ảnh
            output_dir: Thư mục chứa video đầu ra
            motion_type: Loại chuyển động
            duration: Thời lượng mỗi video
            
        Returns:
            List[str]: Danh sách đường dẫn video đã tạo
        """
        os.makedirs(output_dir, exist_ok=True)
        
        video_paths = []
        for i, image_path in enumerate(image_paths):
            try:
                output_path = os.path.join(output_dir, f"motion_{i+1:02d}.mp4")
                result = self.generate_motion(image_path, output_path, motion_type, duration)
                video_paths.append(result)
                logger.info(f"Generated motion video {i+1}/{len(image_paths)}: {result}")
            except Exception as e:
                logger.error(f"Error generating motion for image {i+1}: {e}")
                video_paths.append(None)
        
        return video_paths

# Utility function
def generate_motion(image_path: str, output_path: str, 
                   provider: str = "google_flow", api_key: Optional[str] = None,
                   motion_type: str = "subtle", duration: float = 3.0) -> str:
    """
    Utility function để tạo chuyển động từ ảnh
    
    Args:
        image_path: Đường dẫn ảnh đầu vào
        output_path: Đường dẫn video đầu ra
        provider: Provider để tạo chuyển động
        api_key: API key
        motion_type: Loại chuyển động
        duration: Thời lượng video
        
    Returns:
        str: Đường dẫn video đã tạo
    """
    generator = MotionGenerator(provider, api_key)
    return generator.generate_motion(image_path, output_path, motion_type, duration)
