"""
File Manager Module
Quản lý việc lưu và tải file với giao diện chọn thư mục
"""

import os
import shutil
import streamlit as st
import datetime
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class FileManager:
    """Class quản lý file và thư mục"""
    
    def __init__(self):
        self.default_save_dir = "outputs"
    
    def get_save_directory_ui(self, title: str = "Chọn thư mục lưu", 
                            default_path: str = None) -> Optional[str]:
        """
        Hiển thị giao diện chọn thư mục lưu
        
        Args:
            title: Tiêu đề dialog
            default_path: Đường dẫn mặc định
            
        Returns:
            str: Đường dẫn thư mục đã chọn hoặc None
        """
        st.markdown(f"### 📁 {title}")
        
        # Tùy chọn lưu
        save_option = st.radio(
            "Chọn cách lưu:",
            ["Lưu vào thư mục mặc định", "Chọn thư mục khác"],
            horizontal=True,
            key=f"save_option_{title.replace(' ', '_')}"
        )
        
        if save_option == "Lưu vào thư mục mặc định":
            return self.default_save_dir
        
        # Chọn thư mục khác
        st.markdown("**Chọn thư mục lưu:**")
        
        # Hiển thị các ổ đĩa và thư mục phổ biến
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Ổ đĩa:**")
            drives = self._get_available_drives()
            selected_drive = st.selectbox("Chọn ổ đĩa:", drives, key=f"drive_selector_{title.replace(' ', '_')}")
        
        with col2:
            st.markdown("**Thư mục phổ biến:**")
            common_dirs = self._get_common_directories(selected_drive)
            selected_dir = st.selectbox("Chọn thư mục:", common_dirs, key=f"dir_selector_{title.replace(' ', '_')}")
        
        # Nhập đường dẫn tùy chỉnh
        st.markdown("**Hoặc nhập đường dẫn tùy chỉnh:**")
        custom_path = st.text_input(
            "Đường dẫn thư mục:",
            value=selected_dir,
            placeholder=f"Ví dụ: {selected_drive}\\MyProject\\Videos",
            help="Nhập đường dẫn đầy đủ đến thư mục muốn lưu",
            key=f"custom_path_{title.replace(' ', '_')}"
        )
        
        # Xác nhận
        if st.button("✅ Xác nhận thư mục", key=f"confirm_dir_{title.replace(' ', '_')}"):
            if custom_path and os.path.exists(os.path.dirname(custom_path)):
                return custom_path
            elif custom_path:
                # Tạo thư mục mới nếu chưa tồn tại
                try:
                    os.makedirs(custom_path, exist_ok=True)
                    st.success(f"✅ Đã tạo thư mục: {custom_path}")
                    return custom_path
                except Exception as e:
                    st.error(f"❌ Không thể tạo thư mục: {e}")
                    return None
            else:
                st.warning("⚠️ Vui lòng nhập đường dẫn thư mục")
                return None
        
        return None
    
    def _get_available_drives(self) -> List[str]:
        """Lấy danh sách các ổ đĩa có sẵn"""
        drives = []
        try:
            # Sử dụng psutil để lấy danh sách ổ đĩa chính xác hơn
            import psutil
            partitions = psutil.disk_partitions()
            for partition in partitions:
                if partition.device and os.path.exists(partition.device):
                    drives.append(partition.device)
        except ImportError:
            # Fallback: kiểm tra từng ổ đĩa
            import subprocess
            try:
                # Sử dụng wmic để lấy danh sách ổ đĩa trên Windows
                result = subprocess.run(['wmic', 'logicaldisk', 'get', 'size,freespace,caption'], 
                                      capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # Bỏ header
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 1:
                                drive = parts[0].strip()
                                if drive and os.path.exists(drive):
                                    drives.append(drive)
            except:
                # Fallback cuối cùng: kiểm tra từng ổ đĩa
                for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    drive_path = f"{drive}:\\"
                    try:
                        if os.path.exists(drive_path):
                            drives.append(drive_path)
                    except:
                        continue
        
        # Nếu không tìm thấy ổ đĩa nào, thêm C: mặc định
        if not drives:
            drives = ["C:\\"]
        
        return drives
    
    def _get_common_directories(self, drive: str) -> List[str]:
        """Lấy danh sách thư mục phổ biến"""
        common_dirs = [
            f"{drive}Users\\{os.getenv('USERNAME', 'User')}\\Desktop",
            f"{drive}Users\\{os.getenv('USERNAME', 'User')}\\Documents",
            f"{drive}Users\\{os.getenv('USERNAME', 'User')}\\Downloads",
            f"{drive}Users\\{os.getenv('USERNAME', 'User')}\\Videos",
            f"{drive}Users\\{os.getenv('USERNAME', 'User')}\\Pictures",
            f"{drive}Projects",
            f"{drive}MyProject",
            f"{drive}Videos",
            f"{drive}AI_Videos"
        ]
        
        # Lọc chỉ những thư mục tồn tại
        existing_dirs = []
        for dir_path in common_dirs:
            if os.path.exists(dir_path):
                existing_dirs.append(dir_path)
        
        return existing_dirs if existing_dirs else [f"{drive}"]
    
    def save_project_with_images(self, scenes: List[Dict], image_paths: List[str], 
                               save_directory: str, project_name: str = None,
                               separate_files: bool = True) -> Dict[str, str]:
        """
        Lưu toàn bộ dự án (script + ảnh) vào thư mục đã chọn
        
        Args:
            scenes: Danh sách các cảnh
            image_paths: Danh sách đường dẫn ảnh
            save_directory: Thư mục lưu
            project_name: Tên dự án
            separate_files: Tách các file riêng biệt (script, dialogue, prompts)
            
        Returns:
            Dict: Thông tin các file đã lưu
        """
        if not project_name:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = f"AI_Video_Project_{timestamp}"
        
        # Tạo thư mục dự án
        project_dir = os.path.join(save_directory, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Tạo các thư mục con
        scripts_dir = os.path.join(project_dir, "scripts")
        images_dir = os.path.join(project_dir, "images")
        dialogues_dir = os.path.join(project_dir, "dialogues")
        prompts_dir = os.path.join(project_dir, "prompts")
        
        os.makedirs(scripts_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        if separate_files:
            os.makedirs(dialogues_dir, exist_ok=True)
            os.makedirs(prompts_dir, exist_ok=True)
        
        saved_files = {
            "project_dir": project_dir,
            "scripts_dir": scripts_dir,
            "images_dir": images_dir,
            "dialogues_dir": dialogues_dir if separate_files else None,
            "prompts_dir": prompts_dir if separate_files else None
        }
        
        try:
            # Lưu script JSON
            from .script_generator import ScriptGenerator
            script_gen = ScriptGenerator()
            
            json_path = script_gen.save_script(
                scenes, 
                filename=f"{project_name}.json",
                save_directory=scripts_dir
            )
            saved_files["script_json"] = json_path
            
            # Lưu script Text
            text_path = script_gen.save_script_as_text(
                scenes,
                filename=f"{project_name}.txt",
                save_directory=scripts_dir
            )
            saved_files["script_text"] = text_path
            
            # Copy ảnh
            copied_images = []
            for i, image_path in enumerate(image_paths):
                if os.path.exists(image_path):
                    filename = f"scene_{i+1:02d}.png"
                    dest_path = os.path.join(images_dir, filename)
                    shutil.copy2(image_path, dest_path)
                    copied_images.append(dest_path)
            
            saved_files["images"] = copied_images
            
            # Tách file riêng biệt nếu được yêu cầu
            if separate_files:
                # Tách dialogue
                dialogue_files = self._save_dialogues_separately(scenes, dialogues_dir, project_name)
                saved_files["dialogues"] = dialogue_files
                
                # Tách image prompts
                prompt_files = self._save_prompts_separately(scenes, prompts_dir, project_name)
                saved_files["prompts"] = prompt_files
            
            # Tạo file README
            readme_path = self._create_project_readme(project_dir, project_name, scenes, copied_images)
            saved_files["readme"] = readme_path
            
            logger.info(f"Project saved to: {project_dir}")
            return saved_files
            
        except Exception as e:
            logger.error(f"Error saving project: {e}")
            raise
    
    def _create_project_readme(self, project_dir: str, project_name: str, 
                             scenes: List[Dict], image_paths: List[str]) -> str:
        """Tạo file README cho dự án"""
        readme_path = os.path.join(project_dir, "README.md")
        
        # Kiểm tra xem có tách file riêng không
        has_separate_files = any(scene.get('dialogue') for scene in scenes)
        
        content = f"""# {project_name}

## 📋 Thông tin dự án
- **Ngày tạo:** {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
- **Tổng số cảnh:** {len(scenes)}
- **Tổng thời lượng:** {sum(scene.get('duration', 3) for scene in scenes)} giây

## 📁 Cấu trúc thư mục
```
{project_name}/
├── scripts/
│   ├── {project_name}.json    # Script định dạng JSON
│   └── {project_name}.txt     # Script định dạng text
├── images/
│   ├── scene_01.png           # Ảnh cảnh 1
│   ├── scene_02.png           # Ảnh cảnh 2
│   └── ...                    # Các ảnh khác"""
        
        if has_separate_files:
            content += f"""
├── dialogues/
│   ├── {project_name}_dialogues.txt  # Tất cả dialogue
│   ├── scene_01_dialogue.txt         # Dialogue cảnh 1
│   └── ...                           # Dialogue các cảnh khác
├── prompts/
│   ├── {project_name}_prompts.txt    # Tất cả image prompts
│   ├── scene_01_prompt.txt           # Prompt cảnh 1
│   └── ...                           # Prompt các cảnh khác"""
        
        content += f"""
└── README.md                  # File này
```

## 🎬 Danh sách cảnh
"""
        
        for i, scene in enumerate(scenes, 1):
            content += f"""
### Cảnh {i}: {scene.get('title', f'Scene {i}')}
- **Mô tả:** {scene.get('description', 'Không có mô tả')}
- **Thời lượng:** {scene.get('duration', 3)} giây
- **Chuyển cảnh:** {scene.get('transition', 'fade')}
- **Ảnh:** scene_{i:02d}.png
"""
        
        content += f"""
## 🚀 Cách sử dụng

1. **Xem script:** Mở file `{project_name}.txt` để xem kịch bản chi tiết
2. **Tạo video:** Sử dụng các ảnh trong thư mục `images/` để tạo video
3. **Chỉnh sửa:** Có thể chỉnh sửa script và ảnh theo ý muốn"""
        
        if has_separate_files:
            content += f"""
4. **Sử dụng dialogue:** Mở file trong thư mục `dialogues/` để xem lời thoại
5. **Sử dụng prompts:** Mở file trong thư mục `prompts/` để xem image prompts
6. **Tạo voice-over:** Sử dụng dialogue để tạo giọng đọc cho video"""
        
        content += f"""

## 📝 Ghi chú
- Dự án được tạo bởi AI Video Generator
- Có thể sử dụng với Google Flow hoặc các công cụ tạo video khác
- Ảnh có thể được thay thế hoặc chỉnh sửa"""
        
        if has_separate_files:
            content += f"""
- Dialogue và prompts được tách riêng để dễ sử dụng
- Có thể chỉnh sửa dialogue và prompts theo ý muốn"""
        
        content += f"""
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return readme_path
    
    def _save_dialogues_separately(self, scenes: List[Dict], dialogues_dir: str, project_name: str) -> List[str]:
        """Tách dialogue thành file riêng biệt"""
        dialogue_files = []
        
        # Tạo file dialogue tổng hợp
        all_dialogues = []
        for i, scene in enumerate(scenes, 1):
            dialogue = scene.get('dialogue', '')
            dialogue_type = scene.get('dialogue_type', 'none')
            
            if dialogue and dialogue_type != 'none':
                all_dialogues.append(f"🎬 CẢNH {i}: {scene.get('title', f'Scene {i}')}")
                all_dialogues.append("-" * 50)
                
                if dialogue_type == 'character':
                    all_dialogues.append(f"💬 Lời thoại nhân vật:")
                    all_dialogues.append(f"   {dialogue}")
                elif dialogue_type == 'narration':
                    all_dialogues.append(f"📖 Lời kể chuyện:")
                    all_dialogues.append(f"   {dialogue}")
                
                all_dialogues.append("")
        
        # Lưu file dialogue tổng hợp
        if all_dialogues:
            dialogue_file = os.path.join(dialogues_dir, f"{project_name}_dialogues.txt")
            with open(dialogue_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_dialogues))
            dialogue_files.append(dialogue_file)
        
        # Tạo file dialogue cho từng cảnh
        for i, scene in enumerate(scenes, 1):
            dialogue = scene.get('dialogue', '')
            dialogue_type = scene.get('dialogue_type', 'none')
            
            if dialogue and dialogue_type != 'none':
                scene_dialogue_file = os.path.join(dialogues_dir, f"scene_{i:02d}_dialogue.txt")
                with open(scene_dialogue_file, 'w', encoding='utf-8') as f:
                    f.write(f"🎬 CẢNH {i}: {scene.get('title', f'Scene {i}')}\n")
                    f.write("-" * 50 + "\n")
                    
                    if dialogue_type == 'character':
                        f.write(f"💬 Lời thoại nhân vật:\n")
                        f.write(f"   {dialogue}\n")
                    elif dialogue_type == 'narration':
                        f.write(f"📖 Lời kể chuyện:\n")
                        f.write(f"   {dialogue}\n")
                
                dialogue_files.append(scene_dialogue_file)
        
        return dialogue_files
    
    def _save_prompts_separately(self, scenes: List[Dict], prompts_dir: str, project_name: str) -> List[str]:
        """Tách image prompts thành file riêng biệt"""
        prompt_files = []
        
        # Tạo file prompts tổng hợp
        all_prompts = []
        for i, scene in enumerate(scenes, 1):
            all_prompts.append(f"🎬 CẢNH {i}: {scene.get('title', f'Scene {i}')}")
            all_prompts.append("-" * 50)
            all_prompts.append(f"🎨 Image Prompt:")
            all_prompts.append(f"   {scene.get('image_prompt', 'Không có prompt')}")
            all_prompts.append("")
        
        # Lưu file prompts tổng hợp
        if all_prompts:
            prompts_file = os.path.join(prompts_dir, f"{project_name}_prompts.txt")
            with open(prompts_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_prompts))
            prompt_files.append(prompts_file)
        
        # Tạo file prompt cho từng cảnh
        for i, scene in enumerate(scenes, 1):
            scene_prompt_file = os.path.join(prompts_dir, f"scene_{i:02d}_prompt.txt")
            with open(scene_prompt_file, 'w', encoding='utf-8') as f:
                f.write(f"🎬 CẢNH {i}: {scene.get('title', f'Scene {i}')}\n")
                f.write("-" * 50 + "\n")
                f.write(f"🎨 Image Prompt:\n")
                f.write(f"   {scene.get('image_prompt', 'Không có prompt')}\n")
            
            prompt_files.append(scene_prompt_file)
        
        return prompt_files
    
    def get_download_links_ui(self, saved_files: Dict[str, str]) -> None:
        """
        Hiển thị giao diện download các file đã lưu
        
        Args:
            saved_files: Thông tin các file đã lưu
        """
        st.markdown("### 📥 Tải xuống files")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 Script files:**")
            
            # Script JSON
            if "script_json" in saved_files:
                with open(saved_files["script_json"], 'rb') as f:
                    st.download_button(
                        label="📄 Tải Script JSON",
                        data=f.read(),
                        file_name=os.path.basename(saved_files["script_json"]),
                        mime="application/json"
                    )
            
            # Script Text
            if "script_text" in saved_files:
                with open(saved_files["script_text"], 'rb') as f:
                    st.download_button(
                        label="📝 Tải Script Text",
                        data=f.read(),
                        file_name=os.path.basename(saved_files["script_text"]),
                        mime="text/plain"
                    )
        
        with col2:
            st.markdown("**🖼️ Ảnh files:**")
            
            if "images" in saved_files:
                for i, image_path in enumerate(saved_files["images"]):
                    with open(image_path, 'rb') as f:
                        st.download_button(
                            label=f"🖼️ Tải ảnh {i+1}",
                            data=f.read(),
                            file_name=os.path.basename(image_path),
                            mime="image/png",
                            key=f"download_image_{i}"
                        )
        
        # Hiển thị dialogue và prompts nếu có
        if "dialogues" in saved_files and saved_files["dialogues"]:
            st.markdown("**💬 Dialogue files:**")
            for i, dialogue_path in enumerate(saved_files["dialogues"]):
                with open(dialogue_path, 'rb') as f:
                    st.download_button(
                        label=f"💬 Tải dialogue {i+1}",
                        data=f.read(),
                        file_name=os.path.basename(dialogue_path),
                        mime="text/plain",
                        key=f"download_dialogue_{i}"
                    )
        
        if "prompts" in saved_files and saved_files["prompts"]:
            st.markdown("**🎨 Prompt files:**")
            for i, prompt_path in enumerate(saved_files["prompts"]):
                with open(prompt_path, 'rb') as f:
                    st.download_button(
                        label=f"🎨 Tải prompt {i+1}",
                        data=f.read(),
                        file_name=os.path.basename(prompt_path),
                        mime="text/plain",
                        key=f"download_prompt_{i}"
                    )
        
        # Tải toàn bộ dự án
        st.markdown("**📦 Tải toàn bộ dự án:**")
        if st.button("📦 Tạo file ZIP dự án"):
            try:
                import zipfile
                project_dir = saved_files["project_dir"]
                zip_path = f"{project_dir}.zip"
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(project_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, project_dir)
                            zipf.write(file_path, arcname)
                
                with open(zip_path, 'rb') as f:
                    st.download_button(
                        label="📦 Tải file ZIP",
                        data=f.read(),
                        file_name=os.path.basename(zip_path),
                        mime="application/zip"
                    )
                
                # Xóa file zip tạm
                os.remove(zip_path)
                
            except Exception as e:
                st.error(f"❌ Lỗi tạo file ZIP: {e}")


# Hàm tiện ích
def get_save_directory(title: str = "Chọn thư mục lưu") -> Optional[str]:
    """Hàm tiện ích để lấy thư mục lưu"""
    file_manager = FileManager()
    return file_manager.get_save_directory_ui(title)
