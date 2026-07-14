"""
اختبارات معالج الفيديو
"""
import pytest
import numpy as np
from pathlib import Path

from src.core.video_processor import VideoProcessor


class TestVideoProcessor:
    """اختبارات معالج الفيديو"""

    def test_video_processor_init(self):
        """اختبار التهيئة"""
        # يجب أن يفشل مع ملف غير موجود
        with pytest.raises(ValueError):
            VideoProcessor("nonexistent.mp4")

    def test_resize_frame(self):
        """اختبار تغيير حجم الإطار"""
        # إنشاء إطار تجريبي
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # إنشاء معالج وهمي
        processor = type('obj', (object,), {})()

        # اختبار التغيير مع الحفاظ على النسبة
        resized = VideoProcessor.resize_frame(
            processor,
            frame,
            (224, 224),
            keep_aspect_ratio=True
        )

        assert resized.shape == (224, 224, 3)

    def test_convert_to_grayscale(self):
        """اختبار التحويل إلى رمادي"""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        processor = type('obj', (object,), {})()
        gray = VideoProcessor.convert_to_grayscale(processor, frame)

        assert len(gray.shape) == 2
        assert gray.shape == (480, 640)
