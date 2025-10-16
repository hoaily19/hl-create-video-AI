"""
Image Generator Module
Tạo ảnh từ prompt sử dụng các API khác nhau (OpenAI, Stability AI, etc.)
"""

import openai
import requests
import base64
import io
import os
import time
from PIL import Image
from typing import Optional, List, Dict, Union
import logging
from .api_manager import api_manager

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self, provider: str = "pollinations", api_key: Optional[str] = None):
        """
        Khởi tạo ImageGenerator
        
        Args:
            provider: Nhà cung cấp API ("openai", "stability", "pollinations", "replicate", "huggingface")
            api_key: API key (tùy chọn, sẽ lấy từ api_manager)
        """
        self.provider = provider.lower()
        self.api_key = api_key or api_manager.get_api_key(self.provider)
        
        # Kiểm tra API key cho các provider trả phí
        if self.provider in ["openai", "stability", "replicate"]:
            if not self.api_key:
                raise ValueError(f"{self.provider.title()} API key is required. Set API key in config or pass api_key parameter.")
        
        # Thiết lập API key
        if self.provider == "openai":
            # OpenAI API key sẽ được sử dụng trong client initialization
            pass
    
    def generate_image(self, prompt: str, output_path: str, 
                      size: str = "1024x1024", quality: str = "standard",
                      style: str = "vivid") -> str:
        """
        Tạo ảnh từ prompt với fallback mechanism
        
        Args:
            prompt: Mô tả ảnh muốn tạo
            output_path: Đường dẫn lưu ảnh
            size: Kích thước ảnh (1024x1024, 1792x1024, 1024x1792)
            quality: Chất lượng (standard, hd)
            style: Phong cách (vivid, natural)
            
        Returns:
            str: Đường dẫn file ảnh đã tạo
        """
        # Đảm bảo thư mục output tồn tại
        output_dir = os.path.dirname(output_path)
        if output_dir:  # Chỉ tạo thư mục nếu có đường dẫn thư mục
            os.makedirs(output_dir, exist_ok=True)
        
        # Danh sách providers để thử (với fallback)
        providers_to_try = []
        
        # Danh sách providers theo thứ tự ưu tiên từ config
        available_providers = []
        
        # Thêm providers có API key trước
        if api_manager.get_api_key("openai"):
            available_providers.append("openai")
        if api_manager.get_api_key("stability"):
            available_providers.append("stability")
        if api_manager.get_api_key("replicate"):
            available_providers.append("replicate")
        if api_manager.get_api_key("huggingface"):
            available_providers.append("huggingface")
        
        # Thêm Pollinations (miễn phí, ưu tiên cao)
        available_providers.append("pollinations")
        
        # Không thêm Picsum - chỉ dùng Pollinations
        
        # Chỉ dùng provider được chọn, không fallback
        if self.provider in available_providers:
            providers_to_try = [self.provider]
        else:
            # Nếu provider không có, dùng Pollinations
            providers_to_try = ["pollinations"]
        
        # Thử từng provider cho đến khi thành công
        last_error = None
        for provider in providers_to_try:
            try:
                logger.info(f"Trying image provider: {provider}")
                
                if provider == "openai":
                    return self._generate_openai_image(prompt, output_path, size, quality, style)
                elif provider == "stability":
                    return self._generate_stability_image(prompt, output_path, size)
                elif provider == "pollinations":
                    return self._generate_pollinations_image(prompt, output_path, size)
                elif provider == "replicate":
                    return self._generate_replicate_image(prompt, output_path, size)
                elif provider == "huggingface":
                    return self._generate_huggingface_image(prompt, output_path, size)
                elif provider == "craiyon":
                    return self._generate_craiyon_image(prompt, output_path, size)
                elif provider == "picsum":
                    return self._generate_picsum_image(prompt, output_path, size)
                    
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}")
                last_error = e
                continue
        
        # Nếu tất cả providers đều thất bại, hiển thị thông báo lỗi
        logger.error(f"All image providers failed. Last error: {last_error}")
        raise Exception(f"❌ Không thể tạo ảnh! Tất cả providers đều lỗi. Lỗi cuối: {last_error}")
    
    def _generate_openai_image(self, prompt: str, output_path: str, 
                              size: str, quality: str, style: str) -> str:
        """Tạo ảnh bằng OpenAI DALL-E"""
        try:
            logger.info(f"Generating image with OpenAI DALL-E: {prompt[:50]}...")
            
            # Lấy cấu hình từ api_manager
            config = api_manager.get_provider_config("openai")
            model = config.get("image_model", "dall-e-3")
            default_size = config.get("image_size", "1024x1024")
            default_quality = config.get("image_quality", "standard")
            default_style = config.get("image_style", "vivid")
            
            # OpenAI DALL-E chỉ hỗ trợ một số kích thước nhất định
            if size not in ["1024x1024", "1024x1792", "1792x1024"]:
                size = default_size  # Sử dụng kích thước mặc định
            
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.images.generate(
                model=model,
                prompt=prompt,
                size=size or default_size,
                quality=quality or default_quality,
                style=style or default_style,
                n=1
            )
            
            image_url = response.data[0].url
            
            # Tải ảnh từ URL
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            
            # Lưu ảnh
            with open(output_path, 'wb') as f:
                f.write(img_response.content)
            
            logger.info(f"Image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating OpenAI image: {e}")
            raise
    
    def _generate_stability_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh bằng Stability AI"""
        try:
            logger.info(f"Generating image with Stability AI: {prompt[:50]}...")
            
            # Map size format
            size_map = {
                "1024x1024": "1024x1024",
                "1792x1024": "1344x768", 
                "1024x1792": "768x1344"
            }
            stability_size = size_map.get(size, "1024x1024")
            
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": int(stability_size.split('x')[1]),
                "width": int(stability_size.split('x')[0]),
                "samples": 1,
                "steps": 30
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            # Lưu ảnh từ base64
            image_data = base64.b64decode(result['artifacts'][0]['base64'])
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating Stability AI image: {e}")
            raise
    
    def _generate_pollinations_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh bằng Pollinations AI (miễn phí) với các model và tùy chọn nâng cao"""
        try:
            logger.info(f"Generating image with Pollinations AI: {prompt[:50]}...")
            
            # Cải thiện prompt với các từ khóa chất lượng cao
            enhanced_prompt = self._enhance_prompt_for_pollinations(prompt)
            
            # Rút ngắn prompt để tránh timeout (giới hạn 500 ký tự)
            if len(enhanced_prompt) > 500:
                enhanced_prompt = enhanced_prompt[:500] + "..."
                logger.info(f"Shortened prompt to avoid timeout: {enhanced_prompt}")
            
            # Map size format
            size_map = {
                "1024x1024": "1024x1024",
                "1792x1024": "1792x1024", 
                "1024x1792": "1024x1792"
            }
            pollinations_size = size_map.get(size, "1024x1024")
            
            # Encode prompt for URL
            import urllib.parse
            encoded_prompt = urllib.parse.quote(enhanced_prompt)
            
            # Sử dụng Pollinations AI với retry mạnh mẽ và kích thước đúng
            # ⚠️ LƯU Ý: Từ đầu tháng 10/2025, Pollinations.ai tự động thêm watermark vào tất cả ảnh từ API công khai
            # Chỉ có API nội bộ hoặc tài khoản Pro mới được ảnh không watermark
            urls_to_try = [
                # URL với kích thước đúng
                f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={pollinations_size.split('x')[0]}&height={pollinations_size.split('x')[1]}",
                # Backup URL với model khác
                f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width={pollinations_size.split('x')[0]}&height={pollinations_size.split('x')[1]}",
                # URL với seed random
                f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={hash(prompt) % 1000000}&width={pollinations_size.split('x')[0]}&height={pollinations_size.split('x')[1]}",
                # URL với model SDXL
                f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=sdxl&width={pollinations_size.split('x')[0]}&height={pollinations_size.split('x')[1]}",
                # URL với model SD 1.5
                f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=sd15&width={pollinations_size.split('x')[0]}&height={pollinations_size.split('x')[1]}"
            ]
            
            for attempt, url in enumerate(urls_to_try):
                logger.info(f"Pollinations attempt {attempt + 1}/{len(urls_to_try)}: {url[:100]}...")
                
                # Retry 3 lần cho mỗi URL
                for retry in range(3):
                    try:
                        logger.info(f"  Retry {retry + 1}/3...")
                        
                        response = requests.get(url, timeout=60)  # Timeout 60s
                        
                        # Kiểm tra status code
                        if response.status_code in [500, 502, 503, 504]:
                            logger.warning(f"  ⚠️ Pollinations server error {response.status_code}")
                            if retry < 2:  # Chưa hết retry
                                time.sleep(10)  # Chờ 10 giây
                                continue
                            else:
                                break  # Hết retry, thử URL khác
                        
                        response.raise_for_status()
                        
                        # Kiểm tra content type
                        content_type = response.headers.get('content-type', '')
                        if 'image' not in content_type:
                            logger.warning(f"  ⚠️ Invalid content type: {content_type}")
                            break  # Thử URL khác
                        
                        # Lưu ảnh
                        with open(output_path, 'wb') as f:
                            f.write(response.content)
                        
                        # Kiểm tra file size
                        file_size = os.path.getsize(output_path)
                        if file_size < 1000:  # File quá nhỏ
                            logger.warning(f"  ⚠️ Image file too small: {file_size} bytes")
                            break  # Thử URL khác
                        
                        logger.info(f"✅ Pollinations image generated successfully: {output_path} (size: {file_size} bytes)")
                        
                        # Thử xóa logo nếu có
                        try:
                            self._remove_pollinations_logo(output_path)
                        except Exception as e:
                            logger.warning(f"⚠️ Không thể xóa logo: {e}")
                        
                        return output_path
                        
                    except requests.exceptions.Timeout:
                        logger.warning(f"  ⚠️ Pollinations timeout on retry {retry + 1}/3")
                        if retry < 2:
                            time.sleep(5)
                            continue
                        else:
                            break
                    except requests.exceptions.RequestException as e:
                        logger.warning(f"  ⚠️ Pollinations request error on retry {retry + 1}/3: {e}")
                        if retry < 2:
                            time.sleep(5)
                            continue
                        else:
                            break
                    except Exception as e:
                        logger.warning(f"  ⚠️ Pollinations error on retry {retry + 1}/3: {e}")
                        break
            
            # Nếu tất cả URL đều thất bại
            logger.error("❌ Tất cả Pollinations URLs và retry đều thất bại")
            raise Exception("❌ Pollinations AI: Tất cả URLs và retry đều thất bại. Server có thể đang quá tải.")
            
        except Exception as e:
            logger.error(f"❌ Error generating Pollinations AI image: {e}")
            # Không fallback, chỉ raise exception
            raise e
    
    def _remove_pollinations_logo(self, image_path):
        """
        Thử xóa logo pollinations.ai từ ảnh bằng cách crop phần dưới bên phải
        """
        try:
            from PIL import Image
            
            # Mở ảnh
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Logo thường ở góc dưới bên phải, crop bỏ 10% cuối
                new_height = int(height * 0.9)  # Bỏ 10% cuối
                new_width = int(width * 0.95)   # Bỏ 5% bên phải
                
                # Crop ảnh
                cropped_img = img.crop((0, 0, new_width, new_height))
                
                # Lưu lại
                cropped_img.save(image_path, quality=95)
                
                logger.info(f"✅ Đã crop ảnh để loại bỏ logo: {width}x{height} -> {new_width}x{new_height}")
                
        except Exception as e:
            logger.warning(f"⚠️ Không thể xóa logo: {e}")
            # Không raise exception, chỉ log warning
    
    def _enhance_prompt_for_pollinations(self, prompt: str) -> str:
        """Cải thiện prompt để tạo ảnh đẹp hơn với Pollinations AI"""
        # Thêm các từ khóa chất lượng cao
        quality_keywords = [
            "high quality", "detailed", "sharp focus", "cinematic lighting",
            "professional photography", "4k", "ultra realistic", "photorealistic"
        ]
        
        # Thêm style keywords dựa trên nội dung
        if any(word in prompt.lower() for word in ["deity", "god", "cosmic", "nebula", "asteroid"]):
            quality_keywords.extend(["epic", "dramatic", "cosmic horror", "ethereal lighting", "divine power"])
        elif any(word in prompt.lower() for word in ["battle", "war", "epic", "clash"]):
            quality_keywords.extend(["epic", "dramatic", "dynamic composition", "explosive energy"])
        elif any(word in prompt.lower() for word in ["city", "metropolis", "futuristic"]):
            quality_keywords.extend(["futuristic", "sci-fi", "neon lighting", "urban decay"])
        elif any(word in prompt.lower() for word in ["village", "countryside", "rural"]):
            quality_keywords.extend(["rustic", "natural lighting", "golden hour"])
        elif any(word in prompt.lower() for word in ["dog", "animal", "pet"]):
            quality_keywords.extend(["animal photography", "portrait", "soft lighting"])
        
        # Kết hợp prompt gốc với quality keywords
        enhanced_prompt = prompt
        for keyword in quality_keywords[:4]:  # Thêm 4 keywords để tăng chất lượng
            if keyword not in enhanced_prompt.lower():
                enhanced_prompt += f", {keyword}"
        
        return enhanced_prompt
    
    def _create_quick_placeholder(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh placeholder nhanh chóng với thông tin chi tiết"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Parse size
            width, height = 1024, 1024
            if 'x' in size:
                try:
                    width, height = map(int, size.split('x'))
                except:
                    width, height = 1024, 1024
            
            # Tạo ảnh gradient đẹp hơn
            img = Image.new('RGB', (width, height), color='#2c3e50')
            draw = ImageDraw.Draw(img)
            
            # Vẽ gradient background
            for y in range(height):
                color_value = int(255 * (y / height) * 0.3)  # Gradient nhẹ
                color = (color_value // 3 + 44, color_value // 2 + 62, color_value + 80)  # Từ #2c3e50 đến #4a6741
                draw.line([(0, y), (width, y)], fill=color)
            
            # Thêm text với font mặc định
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            # Text chính
            main_text = "AI Image Generation"
            text_width = draw.textlength(main_text, font=font) if font else len(main_text) * 10
            text_x = (width - text_width) // 2
            text_y = height // 2 - 40
            
            draw.text((text_x, text_y), main_text, fill='white', font=font)
            
            # Text phụ
            sub_text = "Service temporarily unavailable"
            sub_text_width = draw.textlength(sub_text, font=font) if font else len(sub_text) * 8
            sub_text_x = (width - sub_text_width) // 2
            sub_text_y = height // 2 - 10
            
            draw.text((sub_text_x, sub_text_y), sub_text, fill='#bdc3c7', font=font)
            
            # Text prompt (rút ngắn)
            prompt_text = f"Prompt: {prompt[:30]}..." if len(prompt) > 30 else f"Prompt: {prompt}"
            prompt_width = draw.textlength(prompt_text, font=font) if font else len(prompt_text) * 6
            prompt_x = (width - prompt_width) // 2
            prompt_y = height // 2 + 20
            
            draw.text((prompt_x, prompt_y), prompt_text, fill='#95a5a6', font=font)
            
            # Thêm border
            draw.rectangle([10, 10, width-10, height-10], outline='#34495e', width=2)
            
            # Lưu ảnh
            img.save(output_path, 'PNG')
            logger.info(f"Created informative placeholder image: {output_path}")
            return output_path
            
        except Exception as e:
            # Fallback cuối cùng
            img = Image.new('RGB', (1024, 1024), color='#34495e')
            img.save(output_path, 'PNG')
            return output_path
    
    def _create_placeholder_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh placeholder khi tất cả providers đều thất bại"""
        try:
            logger.info(f"Creating placeholder image for: {prompt[:50]}...")
            
            # Parse size
            width, height = 1024, 1024
            if 'x' in size:
                try:
                    width, height = map(int, size.split('x'))
                except:
                    width, height = 1024, 1024
            
            # Tạo ảnh gradient đơn giản
            from PIL import Image, ImageDraw, ImageFont
            
            # Tạo ảnh với gradient
            img = Image.new('RGB', (width, height), color='#2c3e50')
            draw = ImageDraw.Draw(img)
            
            # Vẽ gradient
            for y in range(height):
                color_value = int(255 * (y / height))
                color = (color_value // 3, color_value // 2, color_value)
                draw.line([(0, y), (width, y)], fill=color)
            
            # Thêm text
            try:
                # Thử sử dụng font mặc định
                font_size = min(width, height) // 20
                font = ImageFont.load_default()
            except:
                font = None
            
            # Text chính
            main_text = "Image Generation Failed"
            text_width = draw.textlength(main_text, font=font) if font else len(main_text) * 10
            text_x = (width - text_width) // 2
            text_y = height // 2 - 30
            
            draw.text((text_x, text_y), main_text, fill='white', font=font)
            
            # Text phụ
            sub_text = f"Prompt: {prompt[:50]}..."
            sub_text_width = draw.textlength(sub_text, font=font) if font else len(sub_text) * 8
            sub_text_x = (width - sub_text_width) // 2
            sub_text_y = height // 2 + 10
            
            draw.text((sub_text_x, sub_text_y), sub_text, fill='#bdc3c7', font=font)
            
            # Lưu ảnh
            img.save(output_path, 'PNG')
            logger.info(f"Placeholder image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating placeholder image: {e}")
            # Tạo ảnh đơn giản nhất
            try:
                img = Image.new('RGB', (1024, 1024), color='#34495e')
                img.save(output_path, 'PNG')
                return output_path
            except:
                raise Exception(f"Failed to create any image. Original error: {e}")
    
    def _generate_replicate_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh bằng Replicate (có thể miễn phí với giới hạn)"""
        try:
            logger.info(f"Generating image with Replicate: {prompt[:50]}...")
            
            # Replicate API call (cần cài đặt replicate package)
            try:
                import replicate
                
                # Sử dụng Stable Diffusion model miễn phí
                output = replicate.run(
                    "stability-ai/stable-diffusion:db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf",
                    input={
                        "prompt": prompt,
                        "width": 1024,
                        "height": 1024,
                        "num_inference_steps": 20,
                        "guidance_scale": 7.5
                    }
                )
                
                # Tải ảnh từ URL
                img_response = requests.get(output[0], timeout=30)
                img_response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                
                logger.info(f"Image saved to: {output_path}")
                return output_path
                
            except ImportError:
                logger.error("Replicate package not installed. Run: pip install replicate")
                raise
                
        except Exception as e:
            logger.error(f"Error generating Replicate image: {e}")
            raise
    
    def _generate_huggingface_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh bằng HuggingFace (miễn phí, không cần API key)"""
        try:
            logger.info(f"Generating image with HuggingFace: {prompt[:50]}...")
            
            # Sử dụng HuggingFace Inference API miễn phí (không cần API key)
            model_id = "stabilityai/stable-diffusion-2-1"
            api_url = f"https://api-inference.huggingface.co/models/{model_id}"
            
            # Rút ngắn prompt để tránh lỗi
            if len(prompt) > 200:
                prompt = prompt[:200]
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5
                }
            }
            
            # Thử không có API key trước
            response = requests.post(api_url, json=payload, timeout=30)
            
            # Nếu cần API key, thử với key nếu có
            if response.status_code == 401 and self.api_key:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            
            response.raise_for_status()
            
            # Kiểm tra content type
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                raise Exception(f"Invalid content type: {content_type}")
            
            # Lưu ảnh
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            # Kiểm tra file size
            if os.path.getsize(output_path) < 1000:
                raise Exception("Generated image file too small")
            
            logger.info(f"Image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating HuggingFace image: {e}")
            raise
    
    def _generate_craiyon_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh bằng Craiyon (DALL-E Mini) - miễn phí"""
        try:
            logger.info(f"Generating image with Craiyon: {prompt[:50]}...")
            
            # Rút ngắn prompt
            if len(prompt) > 100:
                prompt = prompt[:100]
            
            # Craiyon API
            api_url = "https://api.craiyon.com/v3"
            
            payload = {
                "prompt": prompt,
                "model": "art",
                "negative_prompt": "",
                "token": None
            }
            
            response = requests.post(api_url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # Craiyon trả về 9 ảnh, lấy ảnh đầu tiên
            if 'images' in result and len(result['images']) > 0:
                import base64
                image_data = base64.b64decode(result['images'][0])
                
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"Image saved to: {output_path}")
                return output_path
            else:
                raise Exception("No images returned from Craiyon")
            
        except Exception as e:
            logger.error(f"Error generating Craiyon image: {e}")
            raise
    
    def _generate_gemini_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh bằng Google Gemini API"""
        try:
            logger.info(f"Generating image with Gemini: {prompt[:50]}...")
            
            import google.generativeai as genai
            
            # Cấu hình API key
            api_key = self.api_manager.get_api_key("google")
            if not api_key:
                raise Exception("Google API key not found")
            
            genai.configure(api_key=api_key)
            
            # Sử dụng Gemini 1.5 Flash
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            # Tạo prompt cho Gemini
            enhanced_prompt = f"Create a high-quality, detailed image: {prompt}. Style: cinematic, professional, high resolution."
            
            # Generate content
            response = model.generate_content(enhanced_prompt)
            
            # Gemini có thể trả về text hoặc image data
            if hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Lưu ảnh từ inline data
                        import base64
                        image_data = base64.b64decode(part.inline_data.data)
                        with open(output_path, 'wb') as f:
                            f.write(image_data)
                        logger.info(f"Image saved to: {output_path}")
                        return output_path
            
            # Fallback: tạo ảnh placeholder đẹp
            logger.warning("Gemini did not return image data, creating enhanced placeholder")
            return self._create_enhanced_placeholder(prompt, output_path, size)
            
        except Exception as e:
            logger.error(f"Error generating Gemini image: {e}")
            raise

    def _create_enhanced_placeholder(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo placeholder đẹp hơn với gradient và text"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import textwrap
            
            # Parse size
            width, height = 1024, 1024
            if 'x' in size:
                try:
                    width, height = map(int, size.split('x'))
                except:
                    width, height = 1024, 1024
            
            # Tạo ảnh với gradient
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)
            
            # Vẽ gradient
            for y in range(height):
                color_value = int(26 + (y / height) * 50)  # Gradient từ #1a1a2e đến #16213e
                color = (color_value, color_value, color_value + 20)
                draw.line([(0, y), (width, y)], fill=color)
            
            # Thêm text
            try:
                # Thử dùng font mặc định
                font_large = ImageFont.truetype("arial.ttf", 48)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except:
                # Fallback font
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Text chính
            main_text = "AI Generated Image"
            text_bbox = draw.textbbox((0, 0), main_text, font=font_large)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = (width - text_width) // 2
            text_y = height // 2 - 60
            
            draw.text((text_x, text_y), main_text, fill='#ffffff', font=font_large)
            
            # Prompt text (wrapped)
            wrapped_prompt = textwrap.fill(prompt, width=50)
            prompt_bbox = draw.textbbox((0, 0), wrapped_prompt, font=font_small)
            prompt_width = prompt_bbox[2] - prompt_bbox[0]
            prompt_x = (width - prompt_width) // 2
            prompt_y = text_y + 80
            
            draw.text((prompt_x, prompt_y), wrapped_prompt, fill='#cccccc', font=font_small)
            
            # Lưu ảnh
            img.save(output_path, 'PNG')
            logger.info(f"Enhanced placeholder saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating enhanced placeholder: {e}")
            # Fallback cuối cùng
            from PIL import Image
            img = Image.new('RGB', (1024, 1024), color='#34495e')
            img.save(output_path, 'PNG')
            return output_path

    def _generate_huggingface_space_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh bằng Hugging Face Space API miễn phí"""
        try:
            logger.info(f"Generating image with Hugging Face Space: {prompt[:50]}...")
            
            # Sử dụng Stable Diffusion Space
            url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}" if self.api_key else None
            }
            
            # Payload
            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5
                }
            }
            
            # Gửi request
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                # Lưu ảnh
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Image saved to: {output_path}")
                return output_path
            else:
                raise Exception(f"Hugging Face API error: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error generating Hugging Face Space image: {e}")
            raise

    def _generate_picsum_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh placeholder đẹp bằng Picsum Photos API"""
        try:
            logger.info(f"Generating placeholder image with Picsum: {prompt[:50]}...")
            
            # Parse size
            width, height = 1024, 1024
            if 'x' in size:
                try:
                    width, height = map(int, size.split('x'))
                except:
                    width, height = 1024, 1024
            
            # Tạo seed từ prompt để có ảnh nhất quán
            import hashlib
            seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16) % 1000
            
            # Picsum API với seed để có ảnh nhất quán
            url = f"https://picsum.photos/seed/{seed}/{width}/{height}"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # Lưu ảnh
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Placeholder image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating Picsum image: {e}")
            raise
    
    def _generate_leonardo_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh bằng Leonardo AI (miễn phí với giới hạn)"""
        try:
            logger.info(f"Generating image with Leonardo AI: {prompt[:50]}...")
            
            # Leonardo AI API (miễn phí với giới hạn)
            api_url = "https://cloud.leonardo.ai/api/rest/v1/generations"
            
            # Rút ngắn prompt
            if len(prompt) > 200:
                prompt = prompt[:200]
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
            }
            
            payload = {
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, distorted",
                "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",  # Leonardo Diffusion XL
                "width": 1024,
                "height": 1024,
                "num_images": 1,
                "guidance_scale": 7,
                "steps": 20
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if 'sdGenerationJob' in result and 'generationId' in result['sdGenerationJob']:
                generation_id = result['sdGenerationJob']['generationId']
                
                # Chờ ảnh được tạo
                import time
                for _ in range(30):  # Chờ tối đa 30 lần (khoảng 2-3 phút)
                    time.sleep(5)
                    
                    check_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
                    check_response = requests.get(check_url, headers=headers, timeout=30)
                    check_response.raise_for_status()
                    
                    check_result = check_response.json()
                    
                    if check_result.get('generations_by_pk', {}).get('status') == 'COMPLETE':
                        images = check_result.get('generations_by_pk', {}).get('generated_images', [])
                        if images:
                            image_url = images[0].get('url')
                            if image_url:
                                # Tải ảnh
                                img_response = requests.get(image_url, timeout=30)
                                img_response.raise_for_status()
                                
                                with open(output_path, 'wb') as f:
                                    f.write(img_response.content)
                                
                                logger.info(f"Image saved to: {output_path}")
                                return output_path
                        break
                    elif check_result.get('generations_by_pk', {}).get('status') == 'FAILED':
                        raise Exception("Leonardo AI generation failed")
                
                raise Exception("Leonardo AI generation timeout")
            else:
                raise Exception("No generation ID returned from Leonardo AI")
            
        except Exception as e:
            logger.error(f"Error generating Leonardo AI image: {e}")
            raise
    
    def _generate_playground_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh bằng Playground AI (miễn phí)"""
        try:
            logger.info(f"Generating image with Playground AI: {prompt[:50]}...")
            
            # Playground AI API (miễn phí)
            api_url = "https://api.playgroundai.com/v1/images/generations"
            
            # Rút ngắn prompt
            if len(prompt) > 200:
                prompt = prompt[:200]
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
            }
            
            payload = {
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, distorted",
                "model": "playground-v2.5-1024px-aesthetic",
                "width": 1024,
                "height": 1024,
                "num_images": 1,
                "guidance_scale": 3.5,
                "steps": 20,
                "seed": None
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if 'data' in result and len(result['data']) > 0:
                image_url = result['data'][0].get('url')
                if image_url:
                    # Tải ảnh
                    img_response = requests.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    logger.info(f"Image saved to: {output_path}")
                    return output_path
                else:
                    raise Exception("No image URL returned from Playground AI")
            else:
                raise Exception("No images returned from Playground AI")
            
        except Exception as e:
            logger.error(f"Error generating Playground AI image: {e}")
            raise
    
    def _generate_local_sd_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh bằng Local Stable Diffusion WebUI API"""
        try:
            logger.info(f"Generating image with Local Stable Diffusion: {prompt[:50]}...")
            
            # Local Stable Diffusion WebUI API
            api_url = "http://127.0.0.1:7860/sdapi/v1/txt2img"
            
            # Parse size
            width, height = 1024, 1024
            if 'x' in size:
                try:
                    width, height = map(int, size.split('x'))
                except:
                    width, height = 1024, 1024
            
            payload = {
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, distorted, bad anatomy",
                "width": width,
                "height": height,
                "steps": 20,
                "cfg_scale": 7,
                "sampler_name": "DPM++ 2M Karras",
                "batch_size": 1,
                "n_iter": 1
            }
            
            response = requests.post(api_url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            
            if 'images' in result and len(result['images']) > 0:
                import base64
                image_data = base64.b64decode(result['images'][0])
                
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"Image saved to: {output_path}")
                return output_path
            else:
                raise Exception("No images returned from Local Stable Diffusion")
            
        except Exception as e:
            logger.error(f"Error generating Local Stable Diffusion image: {e}")
            raise
    
    def _generate_huggingface_space_image(self, prompt: str, output_path: str, size: str) -> str:
        """Tạo ảnh bằng Hugging Face Space API (miễn phí)"""
        try:
            logger.info(f"Generating image with Hugging Face Space: {prompt[:50]}...")
            
            # Hugging Face Space API endpoints (miễn phí)
            space_urls = [
                "https://huggingface.co/spaces/stabilityai/stable-diffusion",
                "https://huggingface.co/spaces/runwayml/stable-diffusion-v1-5",
                "https://huggingface.co/spaces/CompVis/stable-diffusion-v1-4"
            ]
            
            # Rút ngắn prompt
            if len(prompt) > 200:
                prompt = prompt[:200]
            
            for space_url in space_urls:
                try:
                    # Thử với API endpoint của space
                    api_url = f"{space_url}/api/predict"
                    
                    payload = {
                        "data": [
                            prompt,
                            20,  # steps
                            7.5,  # guidance_scale
                            1024,  # width
                            1024,  # height
                            "DPMSolverMultistepScheduler"  # scheduler
                        ]
                    }
                    
                    response = requests.post(api_url, json=payload, timeout=60)
                    response.raise_for_status()
                    
                    result = response.json()
                    
                    if 'data' in result and len(result['data']) > 0:
                        # Lấy ảnh từ base64
                        import base64
                        image_data = base64.b64decode(result['data'][0])
                        
                        with open(output_path, 'wb') as f:
                            f.write(image_data)
                        
                        logger.info(f"Image saved to: {output_path}")
                        return output_path
                    
                except Exception as space_error:
                    logger.warning(f"Hugging Face Space {space_url} failed: {space_error}")
                    continue
            
            raise Exception("All Hugging Face Spaces failed")
            
        except Exception as e:
            logger.error(f"Error generating Hugging Face Space image: {e}")
            raise
    
    def generate_batch_images(self, prompts: List[str], output_dir: str = "outputs/images",
                            prefix: str = "scene", **kwargs) -> List[str]:
        """
        Tạo nhiều ảnh cùng lúc
        
        Args:
            prompts: Danh sách các prompt
            output_dir: Thư mục lưu ảnh
            prefix: Tiền tố tên file
            **kwargs: Các tham số khác cho generate_image
            
        Returns:
            List[str]: Danh sách đường dẫn các ảnh đã tạo
        """
        os.makedirs(output_dir, exist_ok=True)
        image_paths = []
        
        for i, prompt in enumerate(prompts):
            output_path = os.path.join(output_dir, f"{prefix}_{i+1:02d}.png")
            
            try:
                path = self.generate_image(prompt, output_path, **kwargs)
                image_paths.append(path)
                logger.info(f"Generated image {i+1}/{len(prompts)}")
                
                # Nghỉ giữa các request để tránh rate limit và quá tải
                if i < len(prompts) - 1:
                    time.sleep(3)  # Tăng delay lên 3s
                    
            except Exception as e:
                logger.error(f"Failed to generate image {i+1}: {e}")
                # Tạo ảnh placeholder
                try:
                    self._create_placeholder_image(prompt, output_path, "1024x1024")
                    image_paths.append(output_path)
                    logger.info(f"Created placeholder image {i+1}")
                except Exception as placeholder_error:
                    logger.error(f"Failed to create placeholder image {i+1}: {placeholder_error}")
                    # Tạo ảnh đơn giản nhất
                    try:
                        from PIL import Image
                        img = Image.new('RGB', (1024, 1024), color='#34495e')
                        img.save(output_path, 'PNG')
                        image_paths.append(output_path)
                        logger.info(f"Created simple fallback image {i+1}")
                    except Exception as final_error:
                        logger.error(f"Failed to create any image {i+1}: {final_error}")
                        # Bỏ qua ảnh này
                        continue
        
        return image_paths
    
    
    def resize_image(self, image_path: str, target_size: tuple = (1024, 1024)) -> str:
        """
        Resize ảnh về kích thước chuẩn
        
        Args:
            image_path: Đường dẫn ảnh gốc
            target_size: Kích thước mới (width, height)
            
        Returns:
            str: Đường dẫn ảnh đã resize
        """
        try:
            with Image.open(image_path) as img:
                # Resize với aspect ratio
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Tạo ảnh mới với background trắng
                new_img = Image.new('RGB', target_size, 'white')
                
                # Paste ảnh vào giữa
                x = (target_size[0] - img.width) // 2
                y = (target_size[1] - img.height) // 2
                new_img.paste(img, (x, y))
                
                # Lưu ảnh mới
                base, ext = os.path.splitext(image_path)
                new_path = f"{base}_resized{ext}"
                new_img.save(new_path)
                
                return new_path
                
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            return image_path


# Hàm tiện ích
def generate_image(prompt: str, output_path: str, provider: str = "pollinations", 
                  api_key: str = None, **kwargs) -> str:
    """
    Hàm tiện ích để tạo ảnh nhanh
    
    Args:
        prompt: Mô tả ảnh
        output_path: Đường dẫn lưu ảnh
        provider: Nhà cung cấp API
        api_key: API key
        **kwargs: Các tham số khác
        
    Returns:
        str: Đường dẫn ảnh đã tạo
    """
    generator = ImageGenerator(provider, api_key)
    return generator.generate_image(prompt, output_path, **kwargs)


if __name__ == "__main__":
    # Test image generator
    import os
    
    # Test với Pollinations (miễn phí)
    generator = ImageGenerator("pollinations")
    
    test_prompt = "A beautiful sunset over mountains, cinematic style, high quality"
    output_path = "test_image.png"
    
    try:
        result = generator.generate_image(test_prompt, output_path)
        print(f"Image generated successfully: {result}")
    except Exception as e:
        print(f"Error: {e}")


# ==================== BASE64 UTILITIES ====================

def image_to_base64(image_path: str) -> str:
    """
    Chuyển đổi ảnh thành Base64 string
    
    Args:
        image_path: Đường dẫn file ảnh
        
    Returns:
        str: Chuỗi Base64 của ảnh
    """
    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        logger.info(f"Image converted to Base64: {image_path}")
        return encoded
    except Exception as e:
        logger.error(f"Error converting image to Base64: {e}")
        raise


def base64_to_image(b64_string: str, output_path: str) -> str:
    """
    Chuyển đổi Base64 string thành ảnh
    
    Args:
        b64_string: Chuỗi Base64
        output_path: Đường dẫn lưu ảnh
        
    Returns:
        str: Đường dẫn file ảnh đã tạo
    """
    try:
        data = base64.b64decode(b64_string)
        with open(output_path, "wb") as f:
            f.write(data)
        logger.info(f"Base64 converted to image: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error converting Base64 to image: {e}")
        raise


def get_image_base64_info(image_path: str) -> Dict:
    """
    Lấy thông tin chi tiết về ảnh Base64
    
    Args:
        image_path: Đường dẫn file ảnh
        
    Returns:
        Dict: Thông tin về ảnh và Base64
    """
    try:
        # Lấy thông tin file
        file_size = os.path.getsize(image_path)
        
        # Lấy thông tin ảnh
        with Image.open(image_path) as img:
            width, height = img.size
            format_name = img.format
            mode = img.mode
        
        # Chuyển đổi Base64
        b64_string = image_to_base64(image_path)
        b64_size = len(b64_string)
        
        return {
            "file_path": image_path,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "image_width": width,
            "image_height": height,
            "image_format": format_name,
            "image_mode": mode,
            "base64_size": b64_size,
            "base64_size_mb": round(b64_size / (1024 * 1024), 2),
            "base64_preview": b64_string[:100] + "..." if len(b64_string) > 100 else b64_string
        }
    except Exception as e:
        logger.error(f"Error getting image Base64 info: {e}")
        return {"error": str(e)}


def save_base64_to_file(b64_string: str, output_file: str) -> str:
    """
    Lưu chuỗi Base64 vào file text
    
    Args:
        b64_string: Chuỗi Base64
        output_file: Đường dẫn file text
        
    Returns:
        str: Đường dẫn file đã lưu
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(b64_string)
        logger.info(f"Base64 saved to file: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error saving Base64 to file: {e}")
        raise


def load_base64_from_file(file_path: str) -> str:
    """
    Đọc chuỗi Base64 từ file text
    
    Args:
        file_path: Đường dẫn file text
        
    Returns:
        str: Chuỗi Base64
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            b64_string = f.read().strip()
        logger.info(f"Base64 loaded from file: {file_path}")
        return b64_string
    except Exception as e:
        logger.error(f"Error loading Base64 from file: {e}")
        raise


def batch_images_to_base64(image_paths: List[str], output_dir: str = "outputs/base64") -> List[Dict]:
    """
    Chuyển đổi nhiều ảnh thành Base64 cùng lúc
    
    Args:
        image_paths: Danh sách đường dẫn ảnh
        output_dir: Thư mục lưu file Base64
        
    Returns:
        List[Dict]: Danh sách thông tin Base64 của các ảnh
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []
    
    for i, image_path in enumerate(image_paths):
        try:
            # Lấy thông tin ảnh
            info = get_image_base64_info(image_path)
            
            if "error" not in info:
                # Lưu Base64 vào file
                base64_filename = f"image_{i+1:02d}_base64.txt"
                base64_filepath = os.path.join(output_dir, base64_filename)
                save_base64_to_file(info["base64_preview"], base64_filepath)
                
                info["base64_file"] = base64_filepath
                results.append(info)
                logger.info(f"Processed image {i+1}/{len(image_paths)}: {image_path}")
            else:
                results.append({"error": f"Failed to process {image_path}: {info['error']}"})
                
        except Exception as e:
            logger.error(f"Error processing image {i+1}: {e}")
            results.append({"error": f"Image {i+1} error: {str(e)}"})
    
    return results


# ==================== ENHANCED IMAGE GENERATOR WITH BASE64 ====================

class EnhancedImageGenerator(ImageGenerator):
    """Image Generator với hỗ trợ Base64"""
    
    def generate_image_with_base64(self, prompt: str, output_path: str, 
                                 save_base64: bool = True, **kwargs) -> Dict:
        """
        Tạo ảnh và trả về thông tin bao gồm Base64
        
        Args:
            prompt: Mô tả ảnh
            output_path: Đường dẫn lưu ảnh
            save_base64: Có lưu Base64 vào file không
            **kwargs: Các tham số khác
            
        Returns:
            Dict: Thông tin ảnh bao gồm Base64
        """
        try:
            # Tạo ảnh
            image_path = self.generate_image(prompt, output_path, **kwargs)
            
            # Lấy thông tin Base64
            base64_info = get_image_base64_info(image_path)
            
            # Lưu Base64 nếu cần
            if save_base64:
                base64_dir = os.path.join(os.path.dirname(output_path), "base64")
                os.makedirs(base64_dir, exist_ok=True)
                
                base64_filename = os.path.splitext(os.path.basename(output_path))[0] + "_base64.txt"
                base64_filepath = os.path.join(base64_dir, base64_filename)
                save_base64_to_file(base64_info["base64_preview"], base64_filepath)
                
                base64_info["base64_file"] = base64_filepath
            
            return base64_info
            
        except Exception as e:
            logger.error(f"Error generating image with Base64: {e}")
            return {"error": str(e)}
    
    def generate_batch_images_with_base64(self, prompts: List[str], output_dir: str = "outputs/images",
                                        prefix: str = "scene", **kwargs) -> List[Dict]:
        """
        Tạo nhiều ảnh với Base64 cùng lúc
        
        Args:
            prompts: Danh sách prompt
            output_dir: Thư mục lưu ảnh
            prefix: Tiền tố tên file
            **kwargs: Các tham số khác
            
        Returns:
            List[Dict]: Danh sách thông tin ảnh bao gồm Base64
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, prompt in enumerate(prompts):
            try:
                output_path = os.path.join(output_dir, f"{prefix}_{i+1:02d}.png")
                result = self.generate_image_with_base64(prompt, output_path, **kwargs)
                results.append(result)
                logger.info(f"Generated image with Base64 {i+1}/{len(prompts)}")
                
                # Nghỉ giữa các request để tránh quá tải
                if i < len(prompts) - 1:
                    time.sleep(3)  # Tăng delay lên 3s
                    
            except Exception as e:
                logger.error(f"Failed to generate image with Base64 {i+1}: {e}")
                results.append({"error": f"Image {i+1} error: {str(e)}"})
        
        return results
