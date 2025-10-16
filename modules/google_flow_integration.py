#!/usr/bin/env python3
"""
Google Flow Integration Module
Tích hợp với Google Flow API để tạo video từ ảnh
"""

import requests
import base64
import json
import time
import logging
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class GoogleFlowIntegration:
    """Google Flow API Integration"""
    
    def __init__(self, bearer_token: str):
        """
        Initialize Google Flow integration
        
        Args:
            bearer_token: Bearer token từ cookie
        """
        self.bearer_token = bearer_token
        self.base_url = "https://aisandbox-pa.googleapis.com"
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
    def validate_token(self) -> bool:
        """
        Validate Bearer token
        
        Returns:
            bool: True if token is valid
        """
        try:
            # Test với endpoint credits để kiểm tra token
            response = requests.get(
                f"{self.base_url}/v1/credits",
                headers=self.headers,
                timeout=10
            )
            
            logger.info(f"Token validation response: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"Credits response: {result}")
                    logger.info("Google Flow token is valid")
                    return True
                except:
                    logger.info("Google Flow token is valid (200 response)")
                    return True
            elif response.status_code == 401:
                logger.warning("Google Flow token is invalid or expired")
                return False
            elif response.status_code == 403:
                logger.warning("Google Flow token is valid but no permission")
                return True  # Token valid nhưng không có quyền
            else:
                logger.warning(f"Unexpected response: {response.status_code}")
                # Thử endpoint khác
                try:
                    response2 = requests.get(
                        f"{self.base_url}/v1/uploadUserImage",
                        headers=self.headers,
                        timeout=10
                    )
                    if response2.status_code in [200, 400, 405]:  # 405 = Method Not Allowed cũng OK
                        logger.info("Google Flow token is valid (alternative endpoint)")
                        return True
                except:
                    pass
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating Google Flow token: {e}")
            return False
    
    def upload_image_to_flow(self, image_path: str, session_id: str = None) -> Dict:
        """
        Upload image to Google Flow
        
        Args:
            image_path: Path to image file
            session_id: Session ID (optional)
            
        Returns:
            Dict: Response from Google Flow API
        """
        try:
            # Đọc và encode ảnh thành Base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Lấy thông tin ảnh
            from PIL import Image
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format.lower()
            
            # Xác định mime type
            mime_type = f"image/{format_name}" if format_name else "image/jpeg"
            
            # Xác định aspect ratio
            aspect_ratio = "IMAGE_ASPECT_RATIO_LANDSCAPE" if width > height else "IMAGE_ASPECT_RATIO_PORTRAIT"
            
            # Tạo session ID nếu chưa có
            if not session_id:
                session_id = f";{int(time.time() * 1000)}"
            
            # Payload cho Google Flow
            payload = {
                "imageInput": {
                    "rawImageBytes": base64_image,
                    "mimeType": mime_type,
                    "isUserUploaded": True,
                    "aspectRatio": aspect_ratio
                },
                "clientContext": {
                    "sessionId": session_id,
                    "tool": "ASSET_MANAGER"
                }
            }
            
            logger.info(f"Uploading image to Google Flow: {image_path}")
            logger.info(f"Image size: {width}x{height}, Format: {format_name}")
            
            # Gửi request
            response = requests.post(
                f"{self.base_url}/v1:uploadUserImage",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"✅ Image uploaded successfully to Google Flow")
            logger.info(f"Media Generation ID: {result.get('mediaGenerationId', {}).get('mediaGenerationId', 'N/A')}")
            
            return {
                "success": True,
                "media_generation_id": result.get('mediaGenerationId', {}).get('mediaGenerationId'),
                "width": result.get('width'),
                "height": result.get('height'),
                "response": result
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error uploading image to Google Flow: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "request_error"
            }
        except Exception as e:
            logger.error(f"Unexpected error uploading image to Google Flow: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected_error"
            }
    
    def batch_upload_images(self, image_paths: List[str], session_id: str = None) -> List[Dict]:
        """
        Upload multiple images to Google Flow
        
        Args:
            image_paths: List of image file paths
            session_id: Session ID (optional)
            
        Returns:
            List[Dict]: Results for each image upload
        """
        results = []
        
        for i, image_path in enumerate(image_paths):
            try:
                logger.info(f"Uploading image {i+1}/{len(image_paths)}: {image_path}")
                
                result = self.upload_image_to_flow(image_path, session_id)
                result["image_path"] = image_path
                result["index"] = i + 1
                results.append(result)
                
                # Nghỉ giữa các upload để tránh rate limit
                if i < len(image_paths) - 1:
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Error uploading image {i+1}: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "image_path": image_path,
                    "index": i + 1
                })
        
        return results
    
    def create_video_from_script_and_images(self, script_data: Dict, 
                                          image_paths: List[str],
                                          session_id: str = None) -> Dict:
        """
        Tạo video từ kịch bản và ảnh đã tạo
        
        Args:
            script_data: Dữ liệu kịch bản từ script generator
            image_paths: Danh sách đường dẫn ảnh
            session_id: Session ID
            
        Returns:
            Dict: Kết quả tạo video
        """
        try:
            # Upload ảnh trước
            logger.info("🔄 Uploading images to Google Flow...")
            upload_results = self.batch_upload_images(image_paths, session_id)
            
            successful_uploads = [r for r in upload_results if r.get("success")]
            if not successful_uploads:
                return {
                    "success": False,
                    "error": "No images uploaded successfully",
                    "error_type": "upload_error"
                }
            
            # Lấy media generation ID của ảnh đầu tiên
            start_image_id = successful_uploads[0]["media_generation_id"]
            
            # Tạo prompt từ kịch bản
            video_prompt = self._create_prompt_from_script(script_data)
            
            # Tạo video
            return self.create_video_from_images([start_image_id], video_prompt, session_id)
            
        except Exception as e:
            logger.error(f"Error creating video from script and images: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected_error"
            }
    
    def _create_prompt_from_script(self, script_data: Dict) -> str:
        """
        Tạo prompt video từ dữ liệu kịch bản
        
        Args:
            script_data: Dữ liệu kịch bản
            
        Returns:
            str: Prompt cho video generation
        """
        try:
            scenes = script_data.get('scenes', [])
            if not scenes:
                return "Create a cinematic video with smooth transitions"
            
            # Tạo prompt từ các scene
            prompt_parts = []
            
            # Thêm thông tin tổng quan
            title = script_data.get('title', 'Video')
            prompt_parts.append(f"Title: {title}")
            
            # Thêm từng scene
            for i, scene in enumerate(scenes[:5]):  # Chỉ lấy 5 scene đầu để tránh prompt quá dài
                scene_prompt = scene.get('image_prompt', scene.get('description', ''))
                if scene_prompt:
                    prompt_parts.append(f"Scene {i+1}: {scene_prompt}")
            
            # Thêm hướng dẫn chuyển động
            prompt_parts.append("Create smooth cinematic transitions between scenes with appropriate camera movements and lighting effects")
            
            final_prompt = "\n".join(prompt_parts)
            
            # Giới hạn độ dài prompt
            if len(final_prompt) > 1000:
                final_prompt = final_prompt[:1000] + "..."
            
            logger.info(f"Created video prompt from script: {len(final_prompt)} characters")
            return final_prompt
            
        except Exception as e:
            logger.error(f"Error creating prompt from script: {e}")
            return "Create a cinematic video with smooth transitions between the provided images"

    def create_video_from_images(self, media_generation_ids: List[str], 
                                video_prompt: str = None, 
                                session_id: str = None) -> Dict:
        """
        Create video from uploaded images using Google Flow API
        
        Args:
            media_generation_ids: List of media generation IDs
            video_prompt: Prompt for video generation
            session_id: Session ID
            
        Returns:
            Dict: Video creation result
        """
        try:
            if not session_id:
                session_id = f";{int(time.time() * 1000)}"
            
            # Sử dụng media_generation_id đầu tiên làm start image
            start_image_id = media_generation_ids[0] if media_generation_ids else None
            
            if not start_image_id:
                return {
                    "success": False,
                    "error": "No media generation ID provided",
                    "error_type": "validation_error"
                }
            
            # Payload theo format Google Flow API
            payload = {
                "operations": [
                    {
                        "operation": {
                            "name": f"{int(time.time())}",  # Unique operation name
                            "metadata": {
                                "@type": "type.googleapis.com/google.internal.labs.aisandbox.v1.Media",
                                "video": {
                                    "seed": int(time.time()) % 100000,  # Random seed
                                    "prompt": video_prompt or "Create a smooth cinematic video with transitions between these images",
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
                                                "mediaGenerationId": start_image_id,
                                                "imageUsageType": "IMAGE_USAGE_TYPE_START_IMAGE"
                                            }
                                        ],
                                        "isJumpTo": [False]
                                    },
                                    "promptInputs": [
                                        {
                                            "textInput": video_prompt or "Create a smooth cinematic video with transitions between these images"
                                        }
                                    ]
                                }
                            }
                        },
                        "sceneId": f"scene-{int(time.time())}",  # Unique scene ID
                    }
                ]
            }
            
            logger.info(f"Creating video from image: {start_image_id}")
            logger.info(f"Prompt: {video_prompt[:100]}...")
            
            response = requests.post(
                f"{self.base_url}/v1:generateVideo",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info("✅ Video creation initiated successfully")
            logger.info(f"Response: {result}")
            
            # Extract media generation ID from response
            operations = result.get('operations', [])
            if operations:
                operation = operations[0]
                media_generation_id = operation.get('mediaGenerationId')
                status = operation.get('status')
                
                return {
                    "success": True,
                    "media_generation_id": media_generation_id,
                    "status": status,
                    "remaining_credits": result.get('remainingCredits'),
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": "No operations in response",
                    "response": result
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating video: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "request_error"
            }
        except Exception as e:
            logger.error(f"Unexpected error creating video: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected_error"
            }
    
    def check_video_status(self, media_generation_id: str) -> Dict:
        """
        Check video generation status
        
        Args:
            media_generation_id: Media generation ID
            
        Returns:
            Dict: Status information
        """
        try:
            # Sử dụng endpoint check status với media generation ID
            response = requests.get(
                f"{self.base_url}/v1/operations/{media_generation_id}",
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Status check response: {result}")
            
            # Parse response theo format Google Flow
            operations = result.get('operations', [])
            if operations:
                operation = operations[0]
                status = operation.get('status')
                
                # Extract video URL nếu có
                video_url = None
                fife_url = None
                
                if status == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                    # Tìm video URL trong metadata
                    operation_data = operation.get('operation', {})
                    metadata = operation_data.get('metadata', {})
                    video_data = metadata.get('video', {})
                    
                    fife_url = video_data.get('fifeUrl')
                    video_url = fife_url  # Sử dụng fifeUrl làm video URL
                
                return {
                    "success": True,
                    "status": status,
                    "video_url": video_url,
                    "fife_url": fife_url,
                    "remaining_credits": result.get('remainingCredits'),
                    "response": result
                }
            else:
                return {
                    "success": False,
                    "error": "No operations in status response",
                    "response": result
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking video status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def download_video(self, video_url: str, output_path: str) -> bool:
        """
        Download generated video
        
        Args:
            video_url: URL of the generated video
            output_path: Path to save the video
            
        Returns:
            bool: True if download successful
        """
        try:
            logger.info(f"Downloading video from: {video_url}")
            
            response = requests.get(video_url, stream=True, timeout=120)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Video downloaded successfully: {output_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading video: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading video: {e}")
            return False


def extract_bearer_token_from_cookie(cookie_string: str) -> str:
    """
    Extract Bearer token from cookie string
    
    Args:
        cookie_string: Raw cookie string
        
    Returns:
        str: Cleaned Bearer token
    """
    if not cookie_string:
        return ""
    
    # Remove "Bearer " prefix if present
    if cookie_string.startswith("Bearer "):
        cookie_string = cookie_string[7:]
    
    # Remove any extra whitespace
    cookie_string = cookie_string.strip()
    
    return cookie_string


# Test function
def test_google_flow_integration():
    """Test Google Flow integration"""
    # Test token (replace with actual token)
    test_token = "TOKEN"
    
    try:
        flow = GoogleFlowIntegration(test_token)
        
        # Test token validation
        if flow.validate_token():
            print("✅ Google Flow token is valid")
        else:
            print("❌ Google Flow token is invalid")
            return
        
        # Test with existing image
        test_image = "outputs/images/scene_01.png"
        if os.path.exists(test_image):
            result = flow.upload_image_to_flow(test_image)
            if result["success"]:
                print(f"✅ Image uploaded successfully")
                print(f"Media Generation ID: {result['media_generation_id']}")
            else:
                print(f"❌ Image upload failed: {result['error']}")
        else:
            print(f"❌ Test image not found: {test_image}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_google_flow_integration()
