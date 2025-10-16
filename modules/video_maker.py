"""
Video Maker Module
Tạo video từ ảnh với các hiệu ứng chuyển động (Ken Burns, zoom, fade, pan)
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip, concatenate_videoclips
from moviepy.audio.AudioClip import CompositeAudioClip, concatenate_audioclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.fx.FadeIn import FadeIn
from moviepy.video.fx.FadeOut import FadeOut
from moviepy.video.fx.Resize import Resize
import numpy as np

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoMaker:
    def __init__(self, fps: int = 24, resolution: Tuple[int, int] = (1920, 1080)):
        """
        Khởi tạo VideoMaker
        
        Args:
            fps: Frames per second
            resolution: Độ phân giải video (width, height)
        """
        self.fps = fps
        self.resolution = resolution
        self.temp_dir = "temp"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def create_video_from_images(self, image_paths: List[str], output_path: str,
                               scene_durations: List[float] = None,
                               transitions: List[str] = None,
                               effects: List[str] = None,
                               background_music: str = None,
                               voice_over: str = None,
                               scene_texts: List[str] = None,
                               voice_settings: Dict = None) -> str:
        """
        Tạo video từ danh sách ảnh với TTS cho từng scene
        
        Args:
            image_paths: Danh sách đường dẫn ảnh
            output_path: Đường dẫn lưu video
            scene_durations: Thời lượng từng cảnh (giây)
            transitions: Loại chuyển cảnh (fade, cut, zoom, pan)
            effects: Hiệu ứng cho từng cảnh (ken_burns, zoom_in, zoom_out, pan_left, pan_right)
            background_music: Đường dẫn file nhạc nền
            voice_over: Đường dẫn file voice over
            scene_texts: Danh sách text cho từng scene (để tạo TTS)
            voice_settings: Cài đặt giọng nói cho TTS
            
        Returns:
            str: Đường dẫn video đã tạo
        """
        try:
            logger.info(f"Creating video from {len(image_paths)} images")
            
            # Đảm bảo thư mục output tồn tại
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Set defaults
            if scene_durations is None:
                scene_durations = [3.0] * len(image_paths)
            if transitions is None:
                transitions = ["fade"] * len(image_paths)
            if effects is None:
                effects = ["ken_burns"] * len(image_paths)
            if scene_texts is None:
                scene_texts = [""] * len(image_paths)
            if voice_settings is None:
                voice_settings = {"provider": "edge", "voice": "vi-VN-HoaiMyNeural"}
            
            # Tạo clips từ ảnh với TTS
            clips = []
            scene_audio_paths = []
            
            for i, (img_path, duration, effect, text) in enumerate(zip(image_paths, scene_durations, effects, scene_texts)):
                # Tạo clip ảnh
                clip = self._create_image_clip(img_path, duration, effect)
                
                # Tạo TTS cho scene nếu có text
                if text and text.strip():
                    audio_path = self._generate_scene_tts(text, i, voice_settings)
                    if audio_path:
                        scene_audio_paths.append(audio_path)
                        # Thêm audio vào clip
                        clip = self._add_audio_to_clip(clip, audio_path)
                    else:
                        scene_audio_paths.append(None)
                else:
                    scene_audio_paths.append(None)
                
                clips.append(clip)
            
            # Ghép clips với transitions
            final_clip = self._concatenate_with_transitions(clips, transitions)
            
            # Thêm background music nếu có
            if background_music:
                final_clip = self._add_background_music(final_clip, background_music)
            
            # Xuất video
            final_clip.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac' if (background_music or any(scene_audio_paths)) else None,
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Cleanup
            final_clip.close()
            for clip in clips:
                clip.close()
            
            logger.info(f"Video created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            raise
    
    def _create_image_clip(self, image_path: str, duration: float, effect: str) -> ImageClip:
        """
        Tạo clip từ ảnh với hiệu ứng
        
        Args:
            image_path: Đường dẫn ảnh
            duration: Thời lượng clip
            effect: Hiệu ứng áp dụng
            
        Returns:
            ImageClip: Clip đã được xử lý
        """
        try:
            # Tạo clip cơ bản
            clip = ImageClip(image_path, duration=duration)
            
            # Resize về resolution
            clip = clip.with_effects([Resize(newsize=self.resolution)])
            
            # Áp dụng hiệu ứng
            if effect == "ken_burns":
                clip = self._apply_ken_burns_effect(clip)
            elif effect == "zoom_in":
                clip = self._apply_zoom_in_effect(clip)
            elif effect == "zoom_out":
                clip = self._apply_zoom_out_effect(clip)
            elif effect == "pan_left":
                clip = self._apply_pan_left_effect(clip)
            elif effect == "pan_right":
                clip = self._apply_pan_right_effect(clip)
            elif effect == "static":
                # Không có hiệu ứng
                pass
            else:
                # Default: ken burns
                clip = self._apply_ken_burns_effect(clip)
            
            return clip
            
        except Exception as e:
            logger.error(f"Error creating image clip: {e}")
            # Tạo clip đơn giản nếu có lỗi
            return ImageClip(image_path, duration=duration).with_effects([Resize(newsize=self.resolution)])
    
    def _apply_ken_burns_effect(self, clip: ImageClip) -> ImageClip:
        """Áp dụng hiệu ứng Ken Burns (zoom + pan) với tốc độ phù hợp với âm thanh"""
        try:
            duration = clip.duration
            
            # Điều chỉnh tốc độ hiệu ứng dựa trên thời lượng
            if duration < 2.0:
                # Scene ngắn: hiệu ứng nhanh
                zoom_speed = 0.8
                pan_speed = 0.6
                zoom_factor = 0.3
            elif duration < 5.0:
                # Scene trung bình: hiệu ứng vừa phải
                zoom_speed = 1.0
                pan_speed = 0.8
                zoom_factor = 0.2
            else:
                # Scene dài: hiệu ứng chậm, mượt mà
                zoom_speed = 1.2
                pan_speed = 1.0
                zoom_factor = 0.15
            
            # Zoom từ 1.0 đến 1.0 + zoom_factor
            def zoom_func(t):
                progress = t / duration if duration > 0 else 0
                adjusted_progress = min(1.0, progress * zoom_speed)
                return 1.0 + zoom_factor * adjusted_progress
            
            # Pan với tốc độ phù hợp
            def x_func(t):
                progress = t / duration if duration > 0 else 0
                adjusted_progress = min(1.0, progress * pan_speed)
                return -50 * adjusted_progress
            
            def y_func(t):
                progress = t / duration if duration > 0 else 0
                adjusted_progress = min(1.0, progress * pan_speed)
                return -30 * adjusted_progress
            
            # Tạo clip với hiệu ứng
            clip = clip.resize(zoom_func).set_position((x_func, y_func))
            
            return clip
            
        except Exception as e:
            logger.error(f"Error applying Ken Burns effect: {e}")
            return clip
    
    def _apply_zoom_in_effect(self, clip: ImageClip) -> ImageClip:
        """Áp dụng hiệu ứng zoom in"""
        try:
            def zoom_func(t):
                return 1.0 + 0.3 * (t / clip.duration)
            
            clip = clip.resize(zoom_func)
            return clip
            
        except Exception as e:
            logger.error(f"Error applying zoom in effect: {e}")
            return clip
    
    def _apply_zoom_out_effect(self, clip: ImageClip) -> ImageClip:
        """Áp dụng hiệu ứng zoom out"""
        try:
            def zoom_func(t):
                return 1.3 - 0.3 * (t / clip.duration)
            
            clip = clip.resize(zoom_func)
            return clip
            
        except Exception as e:
            logger.error(f"Error applying zoom out effect: {e}")
            return clip
    
    def _apply_pan_effect(self, clip: ImageClip, direction: str) -> ImageClip:
        """Áp dụng hiệu ứng pan theo hướng"""
        try:
            duration = clip.duration
            
            if direction == "left":
                def x_func(t):
                    progress = t / duration if duration > 0 else 0
                    return -100 * progress  # Pan sang trái
                def y_func(t):
                    return 0
            elif direction == "right":
                def x_func(t):
                    progress = t / duration if duration > 0 else 0
                    return 100 * progress  # Pan sang phải
                def y_func(t):
                    return 0
            else:
                # Default: no pan
                def x_func(t):
                    return 0
                def y_func(t):
                    return 0
            
            clip = clip.set_position((x_func, y_func))
            return clip
            
        except Exception as e:
            logger.error(f"Error applying pan effect: {e}")
            return clip
    
    def _apply_pan_left_effect(self, clip: ImageClip) -> ImageClip:
        """Áp dụng hiệu ứng pan từ phải sang trái"""
        try:
            def x_func(t):
                return 100 - 200 * (t / clip.duration)
            
            clip = clip.set_position((x_func, 'center'))
            return clip
            
        except Exception as e:
            logger.error(f"Error applying pan left effect: {e}")
            return clip
    
    def _apply_pan_right_effect(self, clip: ImageClip) -> ImageClip:
        """Áp dụng hiệu ứng pan từ trái sang phải"""
        try:
            def x_func(t):
                return -100 + 200 * (t / clip.duration)
            
            clip = clip.set_position((x_func, 'center'))
            return clip
            
        except Exception as e:
            logger.error(f"Error applying pan right effect: {e}")
            return clip
    
    def _concatenate_with_transitions(self, clips: List[ImageClip], transitions: List[str]) -> CompositeVideoClip:
        """
        Ghép clips với transitions
        
        Args:
            clips: Danh sách clips
            transitions: Danh sách loại transition
            
        Returns:
            CompositeVideoClip: Video đã ghép
        """
        try:
            if len(clips) == 1:
                return clips[0]
            
            # Thêm fade in/out cho từng clip
            processed_clips = []
            for i, (clip, transition) in enumerate(zip(clips, transitions)):
                # Fade in cho clip đầu tiên
                if i == 0:
                    clip = clip.with_effects([FadeIn(duration=0.5)])
                
                # Fade out cho clip cuối cùng
                if i == len(clips) - 1:
                    clip = clip.with_effects([FadeOut(duration=0.5)])
                else:
                    # Fade out cho tất cả clips trừ clip cuối
                    clip = clip.with_effects([FadeOut(duration=0.5)])
                
                processed_clips.append(clip)
            
            # Ghép clips
            final_clip = concatenate_videoclips(processed_clips, method="compose")
            
            return final_clip
            
        except Exception as e:
            logger.error(f"Error concatenating clips: {e}")
            # Fallback: ghép đơn giản
            return concatenate_videoclips(clips)
    
    def _add_audio(self, video_clip, background_music: str = None, voice_over: str = None) -> CompositeVideoClip:
        """
        Thêm audio vào video
        
        Args:
            video_clip: Video clip gốc
            background_music: Đường dẫn nhạc nền
            voice_over: Đường dẫn voice over
            
        Returns:
            CompositeVideoClip: Video với audio
        """
        try:
            audio_clips = []
            
            # Thêm voice over
            if voice_over and os.path.exists(voice_over):
                voice_clip = AudioFileClip(voice_over)
                # Điều chỉnh thời lượng voice cho khớp với video
                if voice_clip.duration > video_clip.duration:
                    voice_clip = voice_clip.subclip(0, video_clip.duration)
                audio_clips.append(voice_clip)
            
            # Thêm background music
            if background_music and os.path.exists(background_music):
                music_clip = AudioFileClip(background_music)
                
                # Loop nhạc nền nếu cần
                if music_clip.duration < video_clip.duration:
                    loops_needed = int(video_clip.duration / music_clip.duration) + 1
                    music_clip = concatenate_videoclips([music_clip] * loops_needed)
                
                # Cắt nhạc cho khớp với video
                music_clip = music_clip.subclip(0, video_clip.duration)
                
                # Giảm volume nhạc nền nếu có voice over
                if voice_over:
                    music_clip = music_clip.volumex(0.3)
                
                audio_clips.append(music_clip)
            
            # Ghép audio
            if audio_clips:
                if len(audio_clips) == 1:
                    final_audio = audio_clips[0]
                else:
                    final_audio = CompositeAudioClip(audio_clips)
                
                video_clip = video_clip.set_audio(final_audio)
            
            return video_clip
            
        except Exception as e:
            logger.error(f"Error adding audio: {e}")
            return video_clip
    
    def add_subtitles(self, video_path: str, subtitles: List[Dict], output_path: str) -> str:
        """
        Thêm subtitle vào video
        
        Args:
            video_path: Đường dẫn video gốc
            subtitles: Danh sách subtitle [{"start": 0, "end": 3, "text": "Hello"}]
            output_path: Đường dẫn video với subtitle
            
        Returns:
            str: Đường dẫn video đã có subtitle
        """
        try:
            from moviepy.video.io.VideoFileClip import VideoFileClip
            
            video = VideoFileClip(video_path)
            subtitle_clips = []
            
            for subtitle in subtitles:
                text_clip = TextClip(
                    subtitle["text"],
                    fontsize=50,
                    color='white',
                    stroke_color='black',
                    stroke_width=2
                ).set_position(('center', 'bottom')).set_duration(
                    subtitle["end"] - subtitle["start"]
                ).set_start(subtitle["start"])
                
                subtitle_clips.append(text_clip)
            
            final_video = CompositeVideoClip([video] + subtitle_clips)
            final_video.write_videofile(output_path, fps=self.fps, codec='libx264')
            
            # Cleanup
            video.close()
            final_video.close()
            for clip in subtitle_clips:
                clip.close()
            
            logger.info(f"Video with subtitles created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding subtitles: {e}")
            return video_path
    
    def create_slideshow(self, image_paths: List[str], output_path: str,
                        duration_per_image: float = 3.0,
                        transition_duration: float = 0.5) -> str:
        """
        Tạo slideshow đơn giản từ ảnh
        
        Args:
            image_paths: Danh sách ảnh
            output_path: Đường dẫn lưu video
            duration_per_image: Thời lượng mỗi ảnh
            transition_duration: Thời lượng transition
            
        Returns:
            str: Đường dẫn video slideshow
        """
        try:
            clips = []
            
            for i, img_path in enumerate(image_paths):
                clip = ImageClip(img_path, duration=duration_per_image)
                clip = clip.with_effects([Resize(newsize=self.resolution)])
                
                # Fade in/out
                if i == 0:
                    clip = clip.with_effects([FadeIn(duration=transition_duration)])
                if i == len(image_paths) - 1:
                    clip = clip.with_effects([FadeOut(duration=transition_duration)])
                else:
                    clip = clip.with_effects([FadeOut(duration=transition_duration)])
                
                clips.append(clip)
            
            final_video = concatenate_videoclips(clips)
            final_video.write_videofile(output_path, fps=self.fps, codec='libx264')
            
            # Cleanup
            final_video.close()
            for clip in clips:
                clip.close()
            
            logger.info(f"Slideshow created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating slideshow: {e}")
            raise
    
    def add_audio_to_video(self, video_path: str, audio_path: str, 
                          output_path: str) -> str:
        """
        Thêm audio vào video
        
        Args:
            video_path: Đường dẫn video gốc
            audio_path: Đường dẫn audio
            output_path: Đường dẫn video đầu ra
            
        Returns:
            str: Đường dẫn video đã có audio
        """
        try:
            from moviepy.video.io.VideoFileClip import VideoFileClip
            
            # Tải video và audio
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            
            # Điều chỉnh độ dài audio cho phù hợp với video
            if audio_clip.duration > video_clip.duration:
                audio_clip = audio_clip.subclip(0, video_clip.duration)
            elif audio_clip.duration < video_clip.duration:
                # Lặp audio nếu ngắn hơn video
                loops_needed = int(video_clip.duration / audio_clip.duration) + 1
                from moviepy.editor import concatenate_audioclips
                audio_clips = [audio_clip] * loops_needed
                audio_clip = concatenate_audioclips(audio_clips).subclip(0, video_clip.duration)
            
            # Ghép video với audio
            final_clip = video_clip.set_audio(audio_clip)
            
            # Xuất video
            final_clip.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Giải phóng memory
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
            logger.info(f"Video with audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding audio to video: {e}")
            raise
    
    def combine_videos(self, video_paths: List[str], output_path: str, 
                      transition_duration: float = 0.5) -> str:
        """
        Ghép nhiều video thành một video
        
        Args:
            video_paths: Danh sách đường dẫn video
            output_path: Đường dẫn video đầu ra
            transition_duration: Thời lượng chuyển cảnh
            
        Returns:
            str: Đường dẫn video đã ghép
        """
        try:
            from moviepy.video.io.VideoFileClip import VideoFileClip
            
            # Tải các video clips
            clips = []
            for video_path in video_paths:
                if os.path.exists(video_path):
                    clip = VideoFileClip(video_path)
                    clips.append(clip)
            
            if not clips:
                raise Exception("No valid video clips found")
            
            # Ghép các clips
            final_video = concatenate_videoclips(clips)
            
            # Xuất video
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Giải phóng memory
            final_video.close()
            for clip in clips:
                clip.close()
            
            logger.info(f"Combined video saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error combining videos: {e}")
            raise
    
    def _generate_scene_tts(self, text: str, scene_index: int, voice_settings: Dict) -> Optional[str]:
        """
        Tạo TTS cho một scene
        
        Args:
            text: Text cần chuyển thành giọng nói
            scene_index: Index của scene
            voice_settings: Cài đặt giọng nói
            
        Returns:
            str: Đường dẫn file audio hoặc None nếu lỗi
        """
        try:
            from .voice_generator import VoiceGenerator
            
            # Tạo VoiceGenerator
            voice_gen = VoiceGenerator(
                provider=voice_settings.get("provider", "edge"),
                api_key=voice_settings.get("api_key")
            )
            
            # Đường dẫn file audio
            audio_path = os.path.join(self.temp_dir, f"scene_{scene_index}_tts.mp3")
            
            # Tạo TTS
            result = voice_gen.generate_voice(
                text=text,
                output_path=audio_path,
                voice=voice_settings.get("voice", "vi-VN-HoaiMyNeural"),
                rate=voice_settings.get("rate", "+0%"),
                pitch=voice_settings.get("pitch", "+0Hz")
            )
            
            logger.info(f"TTS generated for scene {scene_index}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating TTS for scene {scene_index}: {e}")
            return None
    
    def _add_audio_to_clip(self, clip, audio_path: str):
        """
        Thêm audio vào một clip
        
        Args:
            clip: Video clip
            audio_path: Đường dẫn file audio
            
        Returns:
            Video clip với audio
        """
        try:
            from moviepy.editor import AudioFileClip
            
            # Tải audio
            audio_clip = AudioFileClip(audio_path)
            
            # Điều chỉnh độ dài audio cho phù hợp với video
            if audio_clip.duration > clip.duration:
                audio_clip = audio_clip.subclip(0, clip.duration)
            elif audio_clip.duration < clip.duration:
                # Lặp audio nếu ngắn hơn video
                loops_needed = int(clip.duration / audio_clip.duration) + 1
                from moviepy.editor import concatenate_audioclips
                audio_clips = [audio_clip] * loops_needed
                audio_clip = concatenate_audioclips(audio_clips).subclip(0, clip.duration)
            
            # Ghép video với audio
            final_clip = clip.set_audio(audio_clip)
            
            # Giải phóng memory
            audio_clip.close()
            
            return final_clip
            
        except Exception as e:
            logger.error(f"Error adding audio to clip: {e}")
            return clip
    
    def _add_background_music(self, clip, music_path: str):
        """
        Thêm nhạc nền vào video
        
        Args:
            clip: Video clip
            music_path: Đường dẫn file nhạc nền
            
        Returns:
            Video clip với nhạc nền
        """
        try:
            from moviepy.editor import AudioFileClip, CompositeAudioClip
            
            # Tải nhạc nền
            music_clip = AudioFileClip(music_path)
            
            # Điều chỉnh độ dài nhạc cho phù hợp với video
            if music_clip.duration > clip.duration:
                music_clip = music_clip.subclip(0, clip.duration)
            elif music_clip.duration < clip.duration:
                # Lặp nhạc nếu ngắn hơn video
                loops_needed = int(clip.duration / music_clip.duration) + 1
                from moviepy.editor import concatenate_audioclips
                music_clips = [music_clip] * loops_needed
                music_clip = concatenate_audioclips(music_clips).subclip(0, clip.duration)
            
            # Giảm volume nhạc nền (50%)
            music_clip = music_clip.volumex(0.5)
            
            # Ghép audio hiện tại với nhạc nền
            if clip.audio:
                final_audio = CompositeAudioClip([clip.audio, music_clip])
            else:
                final_audio = music_clip
            
            # Ghép video với audio mới
            final_clip = clip.set_audio(final_audio)
            
            # Giải phóng memory
            music_clip.close()
            
            return final_clip
            
        except Exception as e:
            logger.error(f"Error adding background music: {e}")
            return clip
    
    def create_complete_video(self, scenes: List[Dict], image_paths: List[str], 
                            output_path: str, voice_settings: Dict = None,
                            background_music: str = None, scene_duration: float = 3.0) -> str:
        """
        Tạo video hoàn chỉnh từ script, ảnh và TTS
        
        Args:
            scenes: Danh sách các scene từ script
            image_paths: Danh sách đường dẫn ảnh
            output_path: Đường dẫn lưu video
            voice_settings: Cài đặt giọng nói
            background_music: Đường dẫn nhạc nền
            
        Returns:
            str: Đường dẫn video đã tạo
        """
        try:
            logger.info(f"Creating complete video from {len(scenes)} scenes")
            
            # Set defaults
            if voice_settings is None:
                voice_settings = {"provider": "edge", "voice": "vi-VN-HoaiMyNeural"}
            
            # Chuẩn bị dữ liệu
            scene_durations = []
            scene_texts = []
            transitions = []
            effects = []
            
            for scene in scenes:
                # Sử dụng thời lượng được truyền vào
                scene_durations.append(scene_duration)
                
                # Text cho TTS (dialogue, narrator hoặc description)
                dialogue = scene.get('dialogue', '')
                dialogue_type = scene.get('dialogue_type', 'none')
                narrator = scene.get('narrator', '')
                narrator_type = scene.get('narrator_type', 'none')
                
                # Ưu tiên dialogue, sau đó narrator, cuối cùng là description
                if dialogue and dialogue_type != 'none':
                    scene_texts.append(dialogue)
                elif narrator and narrator_type != 'none':
                    scene_texts.append(narrator)
                else:
                    # Sử dụng description nếu không có dialogue hoặc narrator
                    description = scene.get('description', '')
                    scene_texts.append(description)
                
                # Transition và effect
                transition = scene.get('transition', 'fade')
                transitions.append(transition)
                effects.append('ken_burns')  # Default effect
            
            # Tạo video với TTS
            result = self._create_video_with_tts(
                image_paths=image_paths,
                output_path=output_path,
                scene_durations=scene_durations,
                transitions=transitions,
                effects=effects,
                scene_texts=scene_texts,
                voice_settings=voice_settings,
                background_music=background_music
            )
            
            logger.info(f"Complete video created: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating complete video: {e}")
            raise
    
    def _create_video_with_tts(self, image_paths: List[str], output_path: str,
                              scene_durations: List[float], transitions: List[str],
                              effects: List[str], scene_texts: List[str],
                              voice_settings: Dict, background_music: str = None) -> str:
        """
        Tạo video với TTS audio
        """
        try:
            logger.info(f"Creating video with TTS from {len(image_paths)} images")
            
            # Tạo TTS audio cho từng scene
            tts_files = []
            if voice_settings and voice_settings.get("provider") != "none":
                try:
                    from .voice_generator import VoiceGenerator
                    
                    voice_gen = VoiceGenerator(
                        provider=voice_settings.get("provider", "edge"),
                        api_key=voice_settings.get("api_key")
                    )
                    
                    for i, text in enumerate(scene_texts):
                        if text and text.strip():
                            tts_path = f"temp/scene_{i+1}_tts.mp3"
                            os.makedirs("temp", exist_ok=True)
                            
                            try:
                                tts_result = voice_gen.generate_voice(
                                    text=text,
                                    output_path=tts_path,
                                    voice=voice_settings.get("voice", "vi-VN-HoaiMyNeural"),
                                    rate=voice_settings.get("rate", "+0%"),
                                    pitch=voice_settings.get("pitch", "+0Hz")
                                )
                                tts_files.append(tts_result)
                                logger.info(f"Generated TTS for scene {i+1}")
                            except Exception as e:
                                logger.warning(f"Failed to generate TTS for scene {i+1}: {e}")
                                tts_files.append(None)
                        else:
                            tts_files.append(None)
                            
                except Exception as e:
                    logger.warning(f"TTS generation failed: {e}")
                    tts_files = [None] * len(scene_texts)
            else:
                tts_files = [None] * len(scene_texts)
            
            # Tạo video clips từ ảnh
            video_clips = []
            for i, (img_path, duration, effect) in enumerate(zip(image_paths, scene_durations, effects)):
                try:
                    # Tạo clip từ ảnh
                    clip = ImageClip(img_path, duration=duration)
                    
                    # Resize clip
                    clip = clip.with_effects([Resize(newsize=self.resolution)])
                    
                    # Apply effect dựa trên nội dung âm thanh
                    selected_effect = self._select_effect_for_scene(effect, scene_texts[i] if i < len(scene_texts) else "")
                    if selected_effect == "ken_burns":
                        clip = self._apply_ken_burns_effect(clip)
                    elif selected_effect == "zoom_in":
                        clip = self._apply_zoom_effect(clip, "in")
                    elif selected_effect == "zoom_out":
                        clip = self._apply_zoom_effect(clip, "out")
                    elif selected_effect == "pan_left":
                        clip = self._apply_pan_effect(clip, "left")
                    elif selected_effect == "pan_right":
                        clip = self._apply_pan_effect(clip, "right")
                    
                    # Add fade effects
                    if i > 0:
                        clip = clip.with_effects([FadeIn(duration=0.5)])
                    if i < len(image_paths) - 1:
                        clip = clip.with_effects([FadeOut(duration=0.5)])
                    
                    video_clips.append(clip)
                    
                except Exception as e:
                    logger.warning(f"Failed to create clip for image {i+1}: {e}")
                    continue
            
            if not video_clips:
                raise Exception("No valid video clips created")
            
            # Concatenate video clips
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Add TTS audio if available và đồng bộ với hình ảnh
            if any(tts_files):
                try:
                    # Tạo audio clips từ TTS files và điều chỉnh thời lượng scene
                    audio_clips = []
                    adjusted_scene_durations = []
                    current_time = 0
                    
                    for i, tts_file in enumerate(tts_files):
                        if tts_file and os.path.exists(tts_file):
                            try:
                                audio_clip = AudioFileClip(tts_file)
                                actual_audio_duration = audio_clip.duration
                                
                                # Điều chỉnh thời lượng scene để khớp với âm thanh
                                if actual_audio_duration > 0:
                                    # Sử dụng thời lượng âm thanh thực tế + buffer
                                    adjusted_duration = actual_audio_duration + 0.5  # Thêm 0.5s buffer
                                    adjusted_scene_durations.append(adjusted_duration)
                                    
                                    # Set start time
                                    audio_clip = audio_clip.set_start(current_time)
                                    audio_clips.append(audio_clip)
                                    
                                    logger.info(f"Scene {i+1}: Audio duration {actual_audio_duration:.2f}s, adjusted scene duration {adjusted_duration:.2f}s")
                                else:
                                    # Fallback to original duration
                                    adjusted_scene_durations.append(scene_durations[i])
                                    logger.warning(f"Scene {i+1}: Invalid audio duration, using original duration {scene_durations[i]}s")
                                
                            except Exception as e:
                                logger.warning(f"Failed to load TTS audio for scene {i+1}: {e}")
                                adjusted_scene_durations.append(scene_durations[i])
                        else:
                            # No audio for this scene
                            adjusted_scene_durations.append(scene_durations[i])
                        
                        # Move to next scene time
                        current_time += adjusted_scene_durations[-1]
                    
                    # Tạo lại video clips với thời lượng đã điều chỉnh
                    if adjusted_scene_durations != scene_durations:
                        logger.info("Recreating video clips with adjusted durations to match audio")
                        
                        # Clear existing video clips
                        for clip in video_clips:
                            clip.close()
                        video_clips = []
                        
                        # Tạo lại video clips với thời lượng mới
                        for i, (img_path, duration, effect) in enumerate(zip(image_paths, adjusted_scene_durations, effects)):
                            try:
                                # Tạo clip từ ảnh với thời lượng đã điều chỉnh
                                clip = ImageClip(img_path, duration=duration)
                                
                                # Resize clip
                                clip = clip.with_effects([Resize(newsize=self.resolution)])
                                
                                # Apply effect dựa trên nội dung âm thanh
                                selected_effect = self._select_effect_for_scene(effect, scene_texts[i] if i < len(scene_texts) else "")
                                if selected_effect == "ken_burns":
                                    clip = self._apply_ken_burns_effect(clip)
                                elif selected_effect == "zoom_in":
                                    clip = self._apply_zoom_effect(clip, "in")
                                elif selected_effect == "zoom_out":
                                    clip = self._apply_zoom_effect(clip, "out")
                                elif selected_effect == "pan_left":
                                    clip = self._apply_pan_effect(clip, "left")
                                elif selected_effect == "pan_right":
                                    clip = self._apply_pan_effect(clip, "right")
                                
                                # Add fade effects
                                if i > 0:
                                    clip = clip.with_effects([FadeIn(duration=0.5)])
                                if i < len(image_paths) - 1:
                                    clip = clip.with_effects([FadeOut(duration=0.5)])
                                
                                video_clips.append(clip)
                                
                            except Exception as e:
                                logger.warning(f"Failed to recreate clip for image {i+1}: {e}")
                                continue
                        
                        # Recreate final video with adjusted clips
                        if video_clips:
                            final_video.close()  # Close old video
                            final_video = concatenate_videoclips(video_clips, method="compose")
                    
                    if audio_clips:
                        # Concatenate all audio clips
                        combined_audio = concatenate_audioclips(audio_clips)
                        
                        # Set audio to video
                        final_video = final_video.set_audio(combined_audio)
                        logger.info("TTS audio synchronized with video scenes")
                        
                except Exception as e:
                    logger.warning(f"Failed to add TTS audio: {e}")
            
            # Add background music if provided
            if background_music and os.path.exists(background_music):
                try:
                    music_clip = AudioFileClip(background_music)
                    # Loop music to match video duration
                    if music_clip.duration < final_video.duration:
                        loops_needed = int(final_video.duration / music_clip.duration) + 1
                        music_clip = concatenate_audioclips([music_clip] * loops_needed)
                    
                    # Trim to video duration
                    music_clip = music_clip.subclip(0, final_video.duration)
                    
                    # Lower volume for background music
                    music_clip = music_clip.volumex(0.3)
                    
                    if final_video.audio:
                        # Mix with existing audio
                        final_audio = CompositeAudioClip([final_video.audio, music_clip])
                        final_video = final_video.set_audio(final_audio)
                    else:
                        # Set as main audio
                        final_video = final_video.set_audio(music_clip)
                    
                    logger.info("Background music added to video")
                    
                except Exception as e:
                    logger.warning(f"Failed to add background music: {e}")
            
            # Write video file
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Clean up
            final_video.close()
            
            logger.info(f"Video with TTS created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating video with TTS: {e}")
            raise
    
    def _select_effect_for_scene(self, default_effect: str, scene_text: str) -> str:
        """
        Chọn hiệu ứng hình ảnh phù hợp với nội dung âm thanh của scene
        
        Args:
            default_effect: Hiệu ứng mặc định
            scene_text: Nội dung text của scene
            
        Returns:
            str: Hiệu ứng được chọn
        """
        if not scene_text:
            return default_effect
        
        scene_text_lower = scene_text.lower()
        
        # Phân tích nội dung để chọn hiệu ứng phù hợp
        if any(word in scene_text_lower for word in ['zoom', 'phóng to', 'lớn lên', 'tăng', 'mở rộng']):
            return "zoom_in"
        elif any(word in scene_text_lower for word in ['thu nhỏ', 'nhỏ lại', 'giảm', 'co lại']):
            return "zoom_out"
        elif any(word in scene_text_lower for word in ['trái', 'bên trái', 'sang trái', 'left']):
            return "pan_left"
        elif any(word in scene_text_lower for word in ['phải', 'bên phải', 'sang phải', 'right']):
            return "pan_right"
        elif any(word in scene_text_lower for word in ['chuyển động', 'di chuyển', 'di chuyển', 'motion', 'movement']):
            return "ken_burns"
        elif any(word in scene_text_lower for word in ['tĩnh', 'đứng yên', 'không động', 'static']):
            return "static"
        else:
            # Mặc định sử dụng ken_burns cho hiệu ứng tự nhiên
            return "ken_burns" if default_effect == "ken_burns" else default_effect
    
    def _create_simple_video(self, image_paths: List[str], output_path: str,
                           scene_durations: List[float], transitions: List[str],
                           effects: List[str]) -> str:
        """
        Tạo video đơn giản từ ảnh (không có TTS để tránh lỗi MoviePy)
        """
        try:
            logger.info(f"Creating simple video from {len(image_paths)} images")
            
            # Đảm bảo thư mục output tồn tại
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Tạo clips từ ảnh
            clips = []
            for i, (img_path, duration, effect) in enumerate(zip(image_paths, scene_durations, effects)):
                clip = self._create_image_clip(img_path, duration, effect)
                clips.append(clip)
            
            # Ghép clips với transitions
            final_clip = self._concatenate_with_transitions(clips, transitions)
            
            # Xuất video đơn giản
            final_clip.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio=False,  # Không có audio để tránh lỗi
                verbose=False,
                logger=None
            )
            
            # Cleanup
            final_clip.close()
            for clip in clips:
                clip.close()
            
            logger.info(f"Simple video created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating simple video: {e}")
            raise


# Hàm tiện ích
def create_video_from_images(image_paths: List[str], output_path: str, **kwargs) -> str:
    """
    Hàm tiện ích để tạo video nhanh
    
    Args:
        image_paths: Danh sách ảnh
        output_path: Đường dẫn lưu video
        **kwargs: Các tham số khác
        
    Returns:
        str: Đường dẫn video đã tạo
    """
    maker = VideoMaker()
    return maker.create_video_from_images(image_paths, output_path, **kwargs)


if __name__ == "__main__":
    # Test video maker
    import glob
    
    # Tìm ảnh test
    test_images = glob.glob("outputs/images/*.png")
    if not test_images:
        print("Không tìm thấy ảnh test. Vui lòng tạo ảnh trước.")
        exit(1)
    
    maker = VideoMaker()
    
    # Tạo video test
    output_path = "outputs/videos/test_video.mp4"
    
    try:
        result = maker.create_video_from_images(
            test_images[:3],  # Chỉ lấy 3 ảnh đầu
            output_path,
            scene_durations=[3, 3, 3],
            transitions=["fade", "fade", "fade"],
            effects=["ken_burns", "zoom_in", "zoom_out"]
        )
        print(f"Video created successfully: {result}")
    except Exception as e:
        print(f"Error: {e}")
