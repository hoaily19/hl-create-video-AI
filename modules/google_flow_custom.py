"""
Google Flow Custom Integration
Tích hợp Google Flow dựa trên guide.txt để tạo video từ ảnh
"""

import requests
import json
import base64
import time
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class GoogleFlowCustom:
    """Google Flow Custom Integration"""
    
    def __init__(self, cookie: str, project_uid: str):
        """
        Khởi tạo Google Flow Custom
        
        Args:
            cookie: Bearer token từ cookie người dùng
            project_uid: UID của project Flow (ví dụ: 386f8d1d-e4f7-4ab8-a085-da6632c72539)
        """
        self.cookie = cookie
        self.project_uid = project_uid
        self.base_url = "https://aisandbox-pa.googleapis.com"
        self.headers = {
            "Authorization": f"Bearer {cookie}",
            "Content-Type": "application/json"
        }
        
    def upload_image(self, image_path: str) -> Optional[str]:
        """
        Upload ảnh lên Google Flow
        
        Args:
            image_path: Đường dẫn đến file ảnh
            
        Returns:
            mediaGenerationId nếu thành công, None nếu thất bại
        """
        try:
            # Đọc và encode ảnh thành base64
            with open(image_path, "rb") as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Xác định MIME type
            file_ext = Path(image_path).suffix.lower()
            mime_type = "image/jpeg" if file_ext in ['.jpg', '.jpeg'] else "image/png"
            
            # Payload cho upload
            payload = {
                "imageInput": {
                    "rawImageBytes": base64_image,
                    "mimeType": mime_type,
                    "isUserUploaded": True,
                    "aspectRatio": "IMAGE_ASPECT_RATIO_LANDSCAPE"
                },
                "clientContext": {
                    "sessionId": f";{int(time.time() * 1000)}",
                    "tool": "ASSET_MANAGER"
                }
            }
            
            # Upload ảnh
            response = requests.post(
                f"{self.base_url}/v1:uploadUserImage",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                media_id = result.get("mediaGenerationId", {}).get("mediaGenerationId")
                if media_id:
                    logger.info(f"✅ Ảnh đã upload thành công: {media_id}")
                    return media_id
                else:
                    logger.error("❌ Không tìm thấy mediaGenerationId trong response")
                    return None
            else:
                logger.error(f"❌ Upload ảnh thất bại: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Lỗi upload ảnh: {e}")
            return None
    
    def create_video(self, media_id: str, prompt: str) -> Optional[str]:
        """
        Tạo video từ ảnh và prompt
        
        Args:
            media_id: ID của ảnh đã upload
            prompt: Prompt để tạo video
            
        Returns:
            operation_id nếu thành công, None nếu thất bại
        """
        try:
            # Payload để tạo video
            payload = {
                "operations": [
                    {
                        "operation": {
                            "name": f"{int(time.time() * 1000)}",  # Tạo tên unique
                            "metadata": {
                                "@type": "type.googleapis.com/google.internal.labs.aisandbox.v1.Media",
                                "name": f"video_{int(time.time() * 1000)}",
                                "video": {
                                    "seed": int(time.time() * 1000) % 1000000,  # Random seed
                                    "mediaGenerationId": media_id,
                                    "prompt": prompt,
                                    "mediaVisibility": "PRIVATE",
                                    "model": "veo_3_1_i2v_s_fast",
                                    "isLooped": False,
                                    "aspectRatio": "VIDEO_ASPECT_RATIO_LANDSCAPE"
                                },
                                "requestData": {
                                    "videoGenerationImageInputs": [
                                        {
                                            "imageUsageType": "IMAGE_USAGE_TYPE_START_IMAGE"
                                        }
                                    ],
                                    "videoGenerationRequestData": {
                                        "videoModelControlInput": {
                                            "videoModelName": "veo_3_1_i2v_s_fast",
                                            "videoGenerationMode": "VIDEO_GENERATION_MODE_IMAGE_TO_VIDEO",
                                            "videoModelCapabilities": [
                                                "VIDEO_MODEL_CAPABILITY_START_IMAGE"
                                            ],
                                            "videoAspectRatio": "VIDEO_ASPECT_RATIO_LANDSCAPE"
                                        },
                                        "videoGenerationImageInputs": [
                                            {
                                                "mediaGenerationId": media_id,
                                                "imageUsageType": "IMAGE_USAGE_TYPE_START_IMAGE"
                                            }
                                        ],
                                        "isJumpTo": [False]
                                    },
                                    "promptInputs": [
                                        {
                                            "textInput": prompt
                                        }
                                    ]
                                }
                            }
                        },
                        "sceneId": f"scene_{int(time.time() * 1000)}",
                        "mediaGenerationId": media_id,
                        "status": "MEDIA_GENERATION_STATUS_ACTIVE"
                    }
                ]
            }
            
            # Gửi request tạo video
            response = requests.post(
                f"{self.base_url}/v1/projects/{self.project_uid}/operations",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                operations = result.get("operations", [])
                if operations:
                    operation_id = operations[0].get("operation", {}).get("name")
                    if operation_id:
                        logger.info(f"✅ Video đang được tạo: {operation_id}")
                        return operation_id
                logger.error("❌ Không tìm thấy operation_id trong response")
                return None
            else:
                logger.error(f"❌ Tạo video thất bại: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Lỗi tạo video: {e}")
            return None
    
    def check_video_status(self, operation_id: str) -> Tuple[str, Optional[str]]:
        """
        Kiểm tra trạng thái video
        
        Args:
            operation_id: ID của operation
            
        Returns:
            Tuple (status, video_url) - status và URL video nếu hoàn thành
        """
        try:
            response = requests.get(
                f"{self.base_url}/v1/projects/{self.project_uid}/operations/{operation_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                operations = result.get("operations", [])
                if operations:
                    operation = operations[0]
                    status = operation.get("status", "UNKNOWN")
                    
                    if status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                        # Lấy URL video
                        metadata = operation.get("operation", {}).get("metadata", {})
                        video_data = metadata.get("video", {})
                        video_url = video_data.get("fifeUrl")
                        
                        if video_url:
                            logger.info(f"✅ Video đã hoàn thành: {video_url}")
                            return "SUCCESS", video_url
                        else:
                            logger.warning("⚠️ Video hoàn thành nhưng không có URL")
                            return "SUCCESS", None
                    elif status == "MEDIA_GENERATION_STATUS_ACTIVE":
                        logger.info("⏳ Video đang được tạo...")
                        return "PROCESSING", None
                    else:
                        logger.warning(f"⚠️ Trạng thái video: {status}")
                        return status, None
                else:
                    logger.error("❌ Không tìm thấy operations trong response")
                    return "ERROR", None
            else:
                logger.error(f"❌ Kiểm tra trạng thái thất bại: {response.status_code}")
                return "ERROR", None
                
        except Exception as e:
            logger.error(f"❌ Lỗi kiểm tra trạng thái: {e}")
            return "ERROR", None
    
    def download_video(self, video_url: str, output_path: str) -> bool:
        """
        Tải video về
        
        Args:
            video_url: URL của video
            output_path: Đường dẫn lưu video
            
        Returns:
            True nếu thành công, False nếu thất bại
        """
        try:
            response = requests.get(video_url, timeout=300)  # 5 phút timeout
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"✅ Video đã tải về: {output_path}")
                return True
            else:
                logger.error(f"❌ Tải video thất bại: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Lỗi tải video: {e}")
            return False
    
    def create_video_from_images(self, image_paths: List[str], prompts: List[str], output_dir: str) -> List[str]:
        """
        Tạo video từ nhiều ảnh
        
        Args:
            image_paths: Danh sách đường dẫn ảnh
            prompts: Danh sách prompt tương ứng
            output_dir: Thư mục lưu video
            
        Returns:
            Danh sách đường dẫn video đã tạo
        """
        created_videos = []
        
        # Tạo thư mục output
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for i, (image_path, prompt) in enumerate(zip(image_paths, prompts)):
            try:
                logger.info(f"🎬 Tạo video {i+1}/{len(image_paths)}: {Path(image_path).name}")
                
                # 1. Upload ảnh
                media_id = self.upload_image(image_path)
                if not media_id:
                    logger.error(f"❌ Không thể upload ảnh: {image_path}")
                    continue
                
                # 2. Tạo video
                operation_id = self.create_video(media_id, prompt)
                if not operation_id:
                    logger.error(f"❌ Không thể tạo video cho ảnh: {image_path}")
                    continue
                
                # 3. Chờ video hoàn thành
                max_wait = 300  # 5 phút
                wait_time = 0
                video_url = None
                
                while wait_time < max_wait:
                    status, video_url = self.check_video_status(operation_id)
                    
                    if status == "SUCCESS":
                        break
                    elif status == "ERROR":
                        logger.error(f"❌ Lỗi tạo video: {image_path}")
                        break
                    
                    time.sleep(10)  # Chờ 10 giây
                    wait_time += 10
                    logger.info(f"⏳ Chờ video hoàn thành... ({wait_time}s/{max_wait}s)")
                
                # 4. Tải video về
                if video_url:
                    video_filename = f"video_{i+1:02d}_{int(time.time())}.mp4"
                    video_path = Path(output_dir) / video_filename
                    
                    if self.download_video(video_url, str(video_path)):
                        created_videos.append(str(video_path))
                        logger.info(f"✅ Video {i+1} hoàn thành: {video_path}")
                    else:
                        logger.error(f"❌ Không thể tải video: {image_path}")
                else:
                    logger.error(f"❌ Không có URL video: {image_path}")
                
                # Nghỉ giữa các request
                if i < len(image_paths) - 1:
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"❌ Lỗi xử lý ảnh {i+1}: {e}")
                continue
        
        return created_videos

def extract_cookie_from_guide(cookie_string: str) -> str:
    """
    Trích xuất Bearer token từ cookie string
    
    Args:
        cookie_string: Chuỗi cookie từ guide
        
    Returns:
        Bearer token
    """
    # Loại bỏ "Bearer " nếu có
    if cookie_string.startswith("Bearer "):
        return cookie_string[7:]
    return cookie_string
