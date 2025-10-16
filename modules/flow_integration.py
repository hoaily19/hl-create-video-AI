"""
Google Flow Integration Module
Tích hợp với Google Flow để tạo video từ hình ảnh
"""

import streamlit as st
import json
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class FlowIntegration:
    """Class để tích hợp với Google Flow"""
    
    def __init__(self):
        self.flow_url = "https://labs.google/fx/vi/tools/flow"
        self.project_data = {}
    
    def prepare_flow_data(self, scenes: List[Dict], image_paths: List[str]) -> Dict:
        """
        Chuẩn bị dữ liệu để gửi đến Google Flow
        
        Args:
            scenes: Danh sách các cảnh từ script
            image_paths: Đường dẫn đến các ảnh đã tạo
            
        Returns:
            Dict chứa dữ liệu đã chuẩn bị
        """
        try:
            flow_data = {
                "project_name": "AI Generated Video",
                "scenes": [],
                "total_scenes": len(scenes),
                "created_by": "AI Video Generator"
            }
            
            for i, (scene, image_path) in enumerate(zip(scenes, image_paths)):
                scene_data = {
                    "scene_number": i + 1,
                    "title": scene.get('title', f'Scene {i+1}'),
                    "description": scene.get('description', ''),
                    "image_prompt": scene.get('image_prompt', ''),
                    "duration": scene.get('duration', 3),
                    "transition": scene.get('transition', 'fade'),
                    "image_path": image_path,
                    "image_exists": os.path.exists(image_path) if image_path else False
                }
                flow_data["scenes"].append(scene_data)
            
            self.project_data = flow_data
            return flow_data
            
        except Exception as e:
            logger.error(f"Error preparing Flow data: {e}")
            return {}
    
    def create_flow_instructions(self, flow_data: Dict) -> str:
        """
        Tạo hướng dẫn sử dụng Google Flow
        
        Args:
            flow_data: Dữ liệu đã chuẩn bị
            
        Returns:
            String chứa hướng dẫn
        """
        instructions = f"""
# 🎬 Hướng dẫn sử dụng Google Flow

## 📋 Thông tin dự án:
- **Tên dự án:** {flow_data.get('project_name', 'AI Generated Video')}
- **Số cảnh:** {flow_data.get('total_scenes', 0)}
- **Tạo bởi:** AI Video Generator

## 🖼️ Danh sách cảnh và ảnh:

"""
        
        for scene in flow_data.get('scenes', []):
            instructions += f"""
### Cảnh {scene['scene_number']}: {scene['title']}
- **Mô tả:** {scene['description']}
- **Prompt ảnh:** {scene['image_prompt']}
- **Thời lượng:** {scene['duration']} giây
- **Chuyển cảnh:** {scene['transition']}
- **Ảnh:** {'✅ Có sẵn' if scene['image_exists'] else '❌ Không tìm thấy'}

"""
        
        instructions += """
## 🚀 Các bước thực hiện:

1. **Truy cập Google Flow:** Nhấn nút "Mở Google Flow" bên dưới
2. **Upload ảnh:** Tải lên từng ảnh theo thứ tự cảnh
3. **Tạo chuyển động:** Sử dụng công cụ Flow để tạo chuyển động cho từng ảnh
4. **Ghép video:** Kết hợp các cảnh thành video hoàn chỉnh
5. **Xuất video:** Tải xuống video cuối cùng

## 💡 Lưu ý:
- Google Flow hiện tại chỉ hỗ trợ qua giao diện web
- Bạn cần tải ảnh lên thủ công
- Sử dụng prompt ảnh để tạo chuyển động phù hợp
- Có thể điều chỉnh thời lượng và hiệu ứng chuyển cảnh

## 📁 Files cần upload:
"""
        
        for scene in flow_data.get('scenes', []):
            if scene['image_exists']:
                instructions += f"- `{os.path.basename(scene['image_path'])}` - {scene['title']}\n"
        
        return instructions
    
    def create_download_links(self, image_paths: List[str]) -> List[Dict]:
        """
        Tạo danh sách link download cho các ảnh
        
        Args:
            image_paths: Danh sách đường dẫn ảnh
            
        Returns:
            List chứa thông tin download
        """
        download_links = []
        
        for i, image_path in enumerate(image_paths):
            if os.path.exists(image_path):
                download_info = {
                    "filename": os.path.basename(image_path),
                    "path": image_path,
                    "scene_number": i + 1,
                    "size": os.path.getsize(image_path) / (1024 * 1024)  # MB
                }
                download_links.append(download_info)
        
        return download_links
    
    def generate_flow_script(self, scenes: List[Dict]) -> str:
        """
        Tạo script tổng hợp cho Google Flow
        
        Args:
            scenes: Danh sách các cảnh
            
        Returns:
            Script tổng hợp
        """
        script = "# AI Generated Video Script\n\n"
        script += "## Tổng quan dự án\n"
        script += f"Số cảnh: {len(scenes)}\n"
        script += "Phong cách: Cinematic\n\n"
        
        script += "## Chi tiết từng cảnh\n\n"
        
        for i, scene in enumerate(scenes):
            script += f"### Cảnh {i+1}: {scene.get('title', f'Scene {i+1}')}\n"
            script += f"**Mô tả:** {scene.get('description', '')}\n"
            script += f"**Prompt ảnh:** {scene.get('image_prompt', '')}\n"
            script += f"**Thời lượng:** {scene.get('duration', 3)} giây\n"
            script += f"**Chuyển cảnh:** {scene.get('transition', 'fade')}\n\n"
        
        script += "## Hướng dẫn tạo video\n"
        script += "1. Upload từng ảnh vào Google Flow\n"
        script += "2. Tạo chuyển động cho từng ảnh\n"
        script += "3. Ghép các cảnh thành video\n"
        script += "4. Thêm hiệu ứng chuyển cảnh\n"
        script += "5. Xuất video cuối cùng\n"
        
        return script
    
    def save_flow_project(self, flow_data: Dict, output_dir: str = "outputs/flow_projects") -> str:
        """
        Lưu dự án Flow vào file JSON
        
        Args:
            flow_data: Dữ liệu dự án
            output_dir: Thư mục lưu trữ
            
        Returns:
            Đường dẫn file đã lưu
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            project_name = flow_data.get('project_name', 'ai_video_project')
            safe_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            
            project_file = os.path.join(output_dir, f"{safe_name}_flow_data.json")
            
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(flow_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Flow project saved: {project_file}")
            return project_file
            
        except Exception as e:
            logger.error(f"Error saving Flow project: {e}")
            return ""
    
    def create_flow_ui(self, flow_data: Dict, image_paths: List[str]) -> None:
        """
        Tạo giao diện Streamlit cho Google Flow integration
        
        Args:
            flow_data: Dữ liệu dự án
            image_paths: Danh sách đường dẫn ảnh
        """
        st.markdown("## 🎬 Tích hợp Google Flow")
        
        # Hiển thị thông tin dự án
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📋 Thông tin dự án")
            st.info(f"**Tên dự án:** {flow_data.get('project_name', 'AI Generated Video')}")
            st.info(f"**Số cảnh:** {flow_data.get('total_scenes', 0)}")
        
        with col2:
            st.markdown("### 🚀 Hành động")
            if st.button("🌐 Mở Google Flow", type="primary"):
                st.markdown(f'<meta http-equiv="refresh" content="0; url={self.flow_url}">', unsafe_allow_html=True)
                st.markdown(f"[🔗 Truy cập Google Flow]({self.flow_url})")
        
        # Hiển thị danh sách cảnh
        st.markdown("### 🎭 Danh sách cảnh")
        
        for i, scene in enumerate(flow_data.get('scenes', [])):
            with st.expander(f"🎬 Cảnh {scene['scene_number']}: {scene['title']}"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write(f"**Mô tả:** {scene['description']}")
                    st.write(f"**Prompt ảnh:** {scene['image_prompt']}")
                    st.write(f"**Thời lượng:** {scene['duration']} giây")
                    st.write(f"**Chuyển cảnh:** {scene['transition']}")
                
                with col2:
                    if scene['image_exists']:
                        st.image(scene['image_path'], caption=f"Cảnh {scene['scene_number']}", width='stretch')
                        
                        # Download button
                        with open(scene['image_path'], 'rb') as f:
                            st.download_button(
                                label=f"📥 Tải ảnh {scene['scene_number']}",
                                data=f.read(),
                                file_name=os.path.basename(scene['image_path']),
                                mime="image/png"
                            )
                    else:
                        st.error("❌ Ảnh không tồn tại")
        
        # Tạo script tổng hợp
        st.markdown("### 📝 Script tổng hợp")
        script = self.generate_flow_script(flow_data.get('scenes', []))
        st.text_area("Script cho Google Flow:", script, height=300)
        
        # Download script
        st.download_button(
            label="📥 Tải script",
            data=script,
            file_name="flow_script.md",
            mime="text/markdown"
        )
        
        # Hướng dẫn sử dụng
        st.markdown("### 📖 Hướng dẫn sử dụng")
        instructions = self.create_flow_instructions(flow_data)
        st.markdown(instructions)
        
        # Lưu dự án
        if st.button("💾 Lưu dự án Flow"):
            project_file = self.save_flow_project(flow_data)
            if project_file:
                st.success(f"✅ Đã lưu dự án: {project_file}")
            else:
                st.error("❌ Lỗi lưu dự án")
