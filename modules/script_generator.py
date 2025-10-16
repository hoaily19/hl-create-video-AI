"""
Script Generator Module
Tạo kịch bản và prompt cho từng cảnh bằng GPT
"""

import openai
import json
import os
from typing import List, Dict, Optional
import logging
from .api_manager import api_manager

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScriptGenerator:
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        Khởi tạo ScriptGenerator
        
        Args:
            provider: Provider để tạo script (openai, anthropic, google)
            api_key: API key. Nếu None, sẽ lấy từ api_manager
        """
        self.provider = provider.lower()
        self.api_key = api_key or api_manager.get_api_key(self.provider)
        
        if not self.api_key and self.provider != "free":
            raise ValueError(f"{self.provider.title()} API key is required. Set API key in config or pass api_key parameter.")
        
        if self.provider == "openai":
            # OpenAI API key sẽ được sử dụng trong client initialization
            pass
    
    def generate_script(self, prompt: str, num_scenes: int = 3, style: str = "cinematic", 
                       include_dialogue: bool = True, script_length: str = "medium") -> List[Dict]:
        """
        Tạo kịch bản từ prompt tổng
        
        Args:
            prompt: ý tưởng video tổng
            num_scenes: số lượng cảnh muốn tạo
            style: phong cách video (cinematic, documentary, animation, etc.)
            include_dialogue: có bao gồm lời thoại nhân vật không
            script_length: độ dài kịch bản (short, medium, long, very_long, ultra_long)
            
        Returns:
            List[Dict]: Danh sách các cảnh với title, description, image_prompt, dialogue
        """
        if self.provider == "openai":
            return self._generate_openai_script(prompt, num_scenes, style, include_dialogue, script_length)
        elif self.provider == "anthropic":
            return self._generate_anthropic_script(prompt, num_scenes, style, include_dialogue, script_length)
        elif self.provider == "google":
            return self._generate_google_script(prompt, num_scenes, style, include_dialogue, script_length)
        elif self.provider == "free":
            return self._generate_free_script(prompt, num_scenes, style, include_dialogue, script_length)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _generate_openai_script(self, prompt: str, num_scenes: int, style: str, include_dialogue: bool = True, script_length: str = "medium") -> List[Dict]:
        """Tạo script bằng OpenAI"""
        # Lấy cấu hình từ api_manager
        config = api_manager.get_provider_config("openai")
        model = config.get("model", "gpt-4o-mini")
        temperature = config.get("temperature", 0.8)
        max_tokens = config.get("max_tokens", 2000)
        
        system_prompt = """You are a professional movie script writer and storyboard artist. 
        Your task is to create engaging, cinematic scenes that tell a compelling story.
        Always respond with valid JSON format only, no additional text."""
        
        dialogue_instruction = ""
        if include_dialogue:
            dialogue_instruction = """
        - dialogue: If there are characters speaking, include dialogue with character names and their lines. If it's narration, include narrator text.
        - dialogue_type: Type of dialogue ("character" for character dialogue, "narration" for storytelling, "none" for no dialogue)
        """
        
        user_prompt = f"""
        Create {num_scenes} short cinematic scenes from this idea: "{prompt}".
        
        Style: {style}
        
        For each scene, provide:
        - title: A brief, engaging title for the scene
        - description: 1-2 sentences describing what happens in the scene
        - image_prompt: A detailed prompt for generating a realistic, cinematic image that captures the scene's mood and key elements
        - duration: Suggested duration in seconds (2-5 seconds)
        - transition: Type of transition to next scene (fade, cut, zoom, pan){dialogue_instruction}
        
        Make the scenes flow naturally and tell a cohesive story.
        Focus on visual storytelling with strong imagery.
        {f"Include character dialogue when appropriate, with clear character names and emotional context." if include_dialogue else ""}
        
        Output JSON format:
        {{
            "scenes": [
                {{
                    "title": "Scene Title",
                    "description": "What happens in this scene",
                    "image_prompt": "Detailed prompt for image generation",
                    "duration": 3,
                    "transition": "fade"{f',\n                    "dialogue": "Character dialogue or narration text",\n                    "dialogue_type": "character|narration|none"' if include_dialogue else ""}
                }}
            ]
        }}
        """
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"Generated script content: {content[:200]}...")
            
            return self._parse_script_response(content, prompt, num_scenes)
                
        except Exception as e:
            logger.error(f"Error generating OpenAI script: {e}")
            return self._create_fallback_scenes(prompt, num_scenes)
    
    def _generate_anthropic_script(self, prompt: str, num_scenes: int, style: str, include_dialogue: bool = True, script_length: str = "medium") -> List[Dict]:
        """Tạo script bằng Anthropic Claude (tương lai)"""
        logger.warning("Anthropic provider not implemented yet, using fallback")
        return self._create_fallback_scenes(prompt, num_scenes)
    
    def _generate_google_script(self, prompt: str, num_scenes: int, style: str, include_dialogue: bool = True, script_length: str = "medium") -> List[Dict]:
        """Tạo script bằng Google Gemini"""
        try:
            import google.generativeai as genai
            
            # Cấu hình Gemini
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            system_prompt = """You are a professional movie script writer and storyboard artist. 
            Your task is to create engaging, cinematic scenes that tell a compelling story.
            Always respond with valid JSON format only, no additional text."""
            
            dialogue_instruction = ""
            if include_dialogue:
                dialogue_instruction = """
            - dialogue: If there are characters speaking, include dialogue with character names and their lines. If it's narration, include narrator text.
            - dialogue_type: Type of dialogue ("character" for character dialogue, "narration" for storytelling, "none" for no dialogue)
            """
            
            # Tạo prompt dựa trên độ dài kịch bản
            length_instructions = {
                "short": "Keep descriptions brief and concise (1 sentence each).",
                "medium": "Provide moderate detail in descriptions (1-2 sentences each).",
                "long": "Include detailed descriptions (2-3 sentences each) with rich imagery.",
                "very_long": "Create very detailed, immersive descriptions (3-4 sentences each) with extensive visual details.",
                "ultra_long": "Create extremely detailed, immersive descriptions (4-6 sentences each) with extensive visual details, character development, and storytelling elements. Each scene should be rich enough for 2 minutes of content."
            }
            
            length_instruction = length_instructions.get(script_length, length_instructions["medium"])
            
            user_prompt = f"""
            Create {num_scenes} cinematic scenes from this idea: "{prompt}".
            
            Style: {style}
            Script Length: {script_length} - {length_instruction}
            
            For each scene, provide:
            - title: A brief, engaging title for the scene
            - description: {length_instruction}
            - image_prompt: A detailed prompt for generating a realistic, cinematic image that captures the scene's mood and key elements
            - duration: Suggested duration in seconds ({'120 seconds (2 minutes)' if script_length == 'ultra_long' else '2-5 seconds'})
            - transition: Type of transition to next scene (fade, cut, zoom, pan){dialogue_instruction}
            
            Make the scenes flow naturally and tell a cohesive story.
            Focus on visual storytelling with strong imagery.
            {f"Include character dialogue when appropriate, with clear character names and emotional context." if include_dialogue else ""}
            {f"Each scene should be detailed enough to support 2 minutes of content with rich storytelling, character development, and visual elements." if script_length == 'ultra_long' else ""}
            
            Output JSON format:
            {{
                "scenes": [
                    {{
                        "title": "Scene Title",
                        "description": "What happens in this scene",
                        "image_prompt": "Detailed prompt for image generation",
                        "duration": 3,
                        "transition": "fade"{f',\n                        "dialogue": "Character dialogue or narration text",\n                        "dialogue_type": "character|narration|none"' if include_dialogue else ""}
                    }}
                ]
            }}
            """
            
            # Tạo response
            response = model.generate_content(user_prompt)
            content = response.text.strip()
            
            # Xử lý markdown code block nếu có
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            if content.startswith('```'):
                content = content[3:]   # Remove ```
            if content.endswith('```'):
                content = content[:-3]  # Remove trailing ```
            
            content = content.strip()
            
            logger.info(f"Generated Gemini script content: {content[:200]}...")
            
            return self._parse_script_response(content, prompt, num_scenes)
            
        except Exception as e:
            logger.error(f"Error generating Google Gemini script: {e}")
            return self._create_fallback_scenes(prompt, num_scenes)
    
    def _generate_free_script(self, prompt: str, num_scenes: int, style: str, include_dialogue: bool = True, script_length: str = "medium") -> List[Dict]:
        """Tạo script miễn phí (template-based)"""
        logger.info("Generating free script using templates")
        return self._create_fallback_scenes(prompt, num_scenes)
    
    def _parse_script_response(self, content: str, prompt: str, num_scenes: int) -> List[Dict]:
        """Parse response từ API"""
        try:
            data = json.loads(content)
            scenes = data.get("scenes", [])
            
            # Validate scenes
            for i, scene in enumerate(scenes):
                required_fields = ["title", "description", "image_prompt"]
                for field in required_fields:
                    if field not in scene:
                        logger.warning(f"Scene {i} missing required field: {field}")
                        scene[field] = f"Missing {field}"
                
                # Set defaults
                scene.setdefault("duration", 3)
                scene.setdefault("transition", "fade")
                scene.setdefault("dialogue", "")
                scene.setdefault("dialogue_type", "none")
            
            logger.info(f"Successfully generated {len(scenes)} scenes")
            return scenes
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {content}")
            return self._create_fallback_scenes(prompt, num_scenes)
    
    def _create_fallback_scenes(self, prompt: str, num_scenes: int) -> List[Dict]:
        """
        Tạo scenes dự phòng khi API thất bại
        """
        logger.info("Creating fallback scenes")
        scenes = []
        
        for i in range(num_scenes):
            scene = {
                "title": f"Scene {i+1}",
                "description": f"A scene related to: {prompt}",
                "image_prompt": f"Cinematic scene related to {prompt}, professional photography, high quality",
                "duration": 3,
                "transition": "fade"
            }
            scenes.append(scene)
        
        return scenes
    
    def save_script(self, scenes: List[Dict], filename: str = None, save_directory: str = None) -> str:
        """
        Lưu kịch bản ra file JSON
        
        Args:
            scenes: Danh sách các cảnh
            filename: Tên file (tùy chọn)
            save_directory: Thư mục lưu file (tùy chọn)
            
        Returns:
            str: Đường dẫn file đã lưu
        """
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"script_{timestamp}.json"
        
        # Xác định thư mục lưu
        if save_directory:
            os.makedirs(save_directory, exist_ok=True)
            filepath = os.path.join(save_directory, filename)
        else:
            # Đảm bảo thư mục outputs/scripts tồn tại
            os.makedirs("outputs/scripts", exist_ok=True)
            filepath = os.path.join("outputs/scripts", filename)
        
        script_data = {
            "generated_at": datetime.datetime.now().isoformat(),
            "total_scenes": len(scenes),
            "scenes": scenes
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Script saved to: {filepath}")
        return filepath
    
    def save_script_as_text(self, scenes: List[Dict], filename: str = None, 
                           include_prompts: bool = True, include_metadata: bool = True,
                           save_directory: str = None) -> str:
        """
        Lưu kịch bản ra file text dễ đọc
        
        Args:
            scenes: Danh sách các cảnh
            filename: Tên file (tùy chọn)
            include_prompts: Có bao gồm image prompts không
            include_metadata: Có bao gồm thông tin metadata không
            save_directory: Thư mục lưu file (tùy chọn)
            
        Returns:
            str: Đường dẫn file đã lưu
        """
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"script_{timestamp}.txt"
        
        # Xác định thư mục lưu
        if save_directory:
            os.makedirs(save_directory, exist_ok=True)
            filepath = os.path.join(save_directory, filename)
        else:
            # Đảm bảo thư mục outputs/scripts tồn tại
            os.makedirs("outputs/scripts", exist_ok=True)
            filepath = os.path.join("outputs/scripts", filename)
        
        # Tạo nội dung text
        content_lines = []
        
        if include_metadata:
            content_lines.extend([
                "=" * 60,
                "KỊCH BẢN VIDEO AI",
                "=" * 60,
                f"Ngày tạo: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                f"Tổng số cảnh: {len(scenes)}",
                f"Tổng thời lượng: {sum(scene.get('duration', 3) for scene in scenes)} giây",
                "",
                ""
            ])
        
        # Thêm từng cảnh
        for i, scene in enumerate(scenes, 1):
            content_lines.extend([
                f"🎬 CẢNH {i}: {scene.get('title', f'Scene {i}')}",
                "-" * 50,
                f"📝 Mô tả: {scene.get('description', 'Không có mô tả')}",
                f"⏱️  Thời lượng: {scene.get('duration', 3)} giây",
                f"🔄 Chuyển cảnh: {scene.get('transition', 'fade')}",
            ])
            
            # Thêm dialogue nếu có
            dialogue = scene.get('dialogue', '')
            dialogue_type = scene.get('dialogue_type', 'none')
            
            if dialogue and dialogue_type != 'none':
                if dialogue_type == 'character':
                    content_lines.extend([
                        f"💬 Lời thoại nhân vật:",
                        f"   {dialogue}",
                    ])
                elif dialogue_type == 'narration':
                    content_lines.extend([
                        f"📖 Lời kể chuyện:",
                        f"   {dialogue}",
                    ])
            
            if include_prompts:
                content_lines.extend([
                    f"🎨 Prompt ảnh:",
                    f"   {scene.get('image_prompt', 'Không có prompt')}",
                ])
            
            content_lines.extend(["", ""])
        
        # Thêm thông tin tổng kết
        if include_metadata:
            content_lines.extend([
                "=" * 60,
                "THÔNG TIN TỔNG KẾT",
                "=" * 60,
                f"📊 Tổng số cảnh: {len(scenes)}",
                f"⏱️  Tổng thời lượng: {sum(scene.get('duration', 3) for scene in scenes)} giây",
                f"📈 Thời lượng trung bình: {sum(scene.get('duration', 3) for scene in scenes) / len(scenes):.1f} giây/cảnh",
                "",
                "🎯 Các loại chuyển cảnh sử dụng:",
            ])
            
            # Thống kê transitions
            transitions = {}
            for scene in scenes:
                transition = scene.get('transition', 'fade')
                transitions[transition] = transitions.get(transition, 0) + 1
            
            for transition, count in transitions.items():
                content_lines.append(f"   - {transition}: {count} cảnh")
            
            content_lines.extend([
                "",
                "📝 Ghi chú:",
                "- Kịch bản này được tạo tự động bởi AI Video Generator",
                "- Có thể chỉnh sửa thời lượng và chuyển cảnh theo ý muốn",
                "- Image prompts có thể được sử dụng để tạo ảnh cho từng cảnh",
                "",
                "=" * 60
            ])
        
        # Ghi file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))
        
        logger.info(f"Script saved as text to: {filepath}")
        return filepath
    
    def load_script(self, filepath: str) -> List[Dict]:
        """
        Tải kịch bản từ file JSON
        
        Args:
            filepath: Đường dẫn file script
            
        Returns:
            List[Dict]: Danh sách các cảnh
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            scenes = data.get("scenes", [])
            logger.info(f"Loaded {len(scenes)} scenes from {filepath}")
            return scenes
            
        except Exception as e:
            logger.error(f"Error loading script: {e}")
            return []


# Hàm tiện ích để sử dụng trực tiếp
def generate_script(prompt: str, num_scenes: int = 3, style: str = "cinematic", 
                   provider: str = "openai", api_key: str = None) -> List[Dict]:
    """
    Hàm tiện ích để tạo kịch bản nhanh
    
    Args:
        prompt: ý tưởng video
        num_scenes: số lượng cảnh
        style: phong cách
        provider: Provider để tạo script
        api_key: API key
        
    Returns:
        List[Dict]: Danh sách các cảnh
    """
    generator = ScriptGenerator(provider, api_key)
    return generator.generate_script(prompt, num_scenes, style)


def add_narrator_to_scenes(scenes: List[Dict], narrator_style: str = "cinematic") -> List[Dict]:
    """
    Thêm lời dẫn chuyện vào các scene
    
    Args:
        scenes: Danh sách các scene
        narrator_style: Phong cách dẫn chuyện (cinematic, documentary, educational, storytelling)
        
    Returns:
        List[Dict]: Danh sách scenes với narrator
    """
    try:
        logger.info(f"Adding narrator to {len(scenes)} scenes with style: {narrator_style}")
        
        for i, scene in enumerate(scenes):
            title = scene.get('title', f'Scene {i+1}')
            description = scene.get('description', '')
            
            # Tạo narrator text dựa trên style
            if narrator_style == "cinematic":
                narrator_text = f"Trong cảnh này, {description.lower()}"
            elif narrator_style == "documentary":
                narrator_text = f"Chúng ta thấy {description.lower()}"
            elif narrator_style == "educational":
                narrator_text = f"Hãy quan sát {description.lower()}"
            elif narrator_style == "storytelling":
                narrator_text = f"Và rồi, {description.lower()}"
            else:
                narrator_text = f"{title}. {description}"
            
            # Thêm narrator vào scene
            scene['narrator'] = narrator_text
            scene['narrator_type'] = 'narration'
            
            # Nếu không có dialogue, sử dụng narrator làm dialogue chính
            if not scene.get('dialogue') or scene.get('dialogue_type') == 'none':
                scene['dialogue'] = narrator_text
                scene['dialogue_type'] = 'narration'
        
        logger.info(f"Successfully added narrator to {len(scenes)} scenes")
        return scenes
        
    except Exception as e:
        logger.error(f"Error adding narrator to scenes: {e}")
        return scenes


if __name__ == "__main__":
    # Test script generator
    import os
    
    # Kiểm tra API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Vui lòng set biến môi trường OPENAI_API_KEY")
        exit(1)
    
    # Test
    generator = ScriptGenerator()
    test_prompt = "A magical forest adventure with talking animals"
    scenes = generator.generate_script(test_prompt, num_scenes=3)
    
    print("Generated scenes:")
    for i, scene in enumerate(scenes):
        print(f"\nScene {i+1}: {scene['title']}")
        print(f"Description: {scene['description']}")
        print(f"Image prompt: {scene['image_prompt']}")
        print(f"Duration: {scene['duration']}s")
        print(f"Transition: {scene['transition']}")
    
    # Lưu script
    script_path = generator.save_script(scenes)
    print(f"\nScript saved to: {script_path}")
