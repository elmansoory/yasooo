"""
معالج الفيديو المتقدم
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Generator, Dict, Any
from dataclasses import dataclass
import logging

from src.utils.logger import LoggerMixin, log_execution_time
from src.utils.validators import VideoValidator


@dataclass
class VideoInfo:
    """معلومات الفيديو"""
    file_path: Path
    width: int
    height: int
    fps: float
    frame_count: int
    duration: float
    codec: str
    size_mb: float


class VideoProcessor(LoggerMixin):
    """معالج الفيديو الأساسي"""

    def __init__(self, video_path: str, config=None):
        """
        Args:
            video_path: مسار ملف الفيديو
            config: كائن الإعدادات
        """
        self.video_path = Path(video_path)
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.video_info: Optional[VideoInfo] = None

        # التحقق من صحة الملف
        is_valid, error_msg = VideoValidator.validate_video_file(self.video_path)
        if not is_valid:
            raise ValueError(f"ملف فيديو غير صالح: {error_msg}")

    def open(self) -> bool:
        """
        فتح ملف الفيديو

        Returns:
            True إذا نجحت العملية
        """
        try:
            self.cap = cv2.VideoCapture(str(self.video_path))

            if not self.cap.isOpened():
                raise ValueError(f"فشل فتح الفيديو: {self.video_path}")

            # جمع معلومات الفيديو
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            codec = int(self.cap.get(cv2.CAP_PROP_FOURCC))
            size_mb = self.video_path.stat().st_size / (1024 * 1024)

            self.video_info = VideoInfo(
                file_path=self.video_path,
                width=width,
                height=height,
                fps=fps,
                frame_count=frame_count,
                duration=duration,
                codec=self._decode_fourcc(codec),
                size_mb=size_mb
            )

            self.logger.info(
                f"تم فتح الفيديو: {width}x{height} @ {fps:.2f}fps, "
                f"{frame_count} إطار, {duration:.2f} ثانية"
            )

            return True

        except Exception as e:
            self.logger.error(f"خطأ في فتح الفيديو: {e}")
            return False

    @staticmethod
    def _decode_fourcc(codec: int) -> str:
        """فك تشفير رمز الترميز"""
        return "".join([chr((codec >> 8 * i) & 0xFF) for i in range(4)])

    def read_frame(self, frame_number: Optional[int] = None) -> Optional[np.ndarray]:
        """
        قراءة إطار واحد

        Args:
            frame_number: رقم الإطار المراد قراءته (اختياري)

        Returns:
            الإطار كمصفوفة numpy أو None
        """
        if self.cap is None:
            self.logger.error("الفيديو غير مفتوح")
            return None

        try:
            if frame_number is not None:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            ret, frame = self.cap.read()
            return frame if ret else None

        except Exception as e:
            self.logger.error(f"خطأ في قراءة الإطار: {e}")
            return None

    def extract_frames(
        self,
        start_frame: int = 0,
        end_frame: Optional[int] = None,
        skip_frames: int = 0
    ) -> Generator[Tuple[int, np.ndarray], None, None]:
        """
        استخراج إطارات من الفيديو

        Args:
            start_frame: الإطار الأول
            end_frame: الإطار الأخير
            skip_frames: عدد الإطارات المراد تخطيها

        Yields:
            (frame_number, frame)
        """
        if self.cap is None:
            self.logger.error("الفيديو غير مفتوح")
            return

        # تحديد الإطار الأخير
        if end_frame is None:
            end_frame = self.video_info.frame_count

        # الانتقال إلى الإطار الأول
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        frame_idx = start_frame
        frames_yielded = 0

        while frame_idx < end_frame:
            ret, frame = self.cap.read()

            if not ret:
                break

            # إرجاع الإطار فقط إذا لم يكن في قائمة التخطي
            if frames_yielded % (skip_frames + 1) == 0:
                yield frame_idx, frame

            frame_idx += 1
            frames_yielded += 1

    def extract_frames_by_time(
        self,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        interval: float = 1.0
    ) -> Generator[Tuple[float, np.ndarray], None, None]:
        """
        استخراج إطارات بناءً على الوقت

        Args:
            start_time: وقت البدء (ثانية)
            end_time: وقت النهاية (ثانية)
            interval: الفاصل الزمني (ثانية)

        Yields:
            (timestamp, frame)
        """
        if self.video_info is None:
            self.logger.error("معلومات الفيديو غير متاحة")
            return

        if end_time is None:
            end_time = self.video_info.duration

        current_time = start_time

        while current_time <= end_time:
            # حساب رقم الإطار
            frame_number = int(current_time * self.video_info.fps)

            # قراءة الإطار
            frame = self.read_frame(frame_number)

            if frame is not None:
                yield current_time, frame

            current_time += interval

    @log_execution_time
    def resize_frame(
        self,
        frame: np.ndarray,
        size: Tuple[int, int],
        keep_aspect_ratio: bool = True
    ) -> np.ndarray:
        """
        تغيير حجم الإطار

        Args:
            frame: الإطار الأصلي
            size: الحجم المطلوب (width, height)
            keep_aspect_ratio: الحفاظ على نسبة العرض إلى الارتفاع

        Returns:
            الإطار بالحجم الجديد
        """
        if keep_aspect_ratio:
            height, width = frame.shape[:2]
            target_width, target_height = size

            # حساب نسبة التحجيم
            scale = min(target_width / width, target_height / height)

            new_width = int(width * scale)
            new_height = int(height * scale)

            resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

            # إضافة حشو إذا لزم الأمر
            if new_width < target_width or new_height < target_height:
                delta_w = target_width - new_width
                delta_h = target_height - new_height
                top, bottom = delta_h // 2, delta_h - (delta_h // 2)
                left, right = delta_w // 2, delta_w - (delta_w // 2)

                resized = cv2.copyMakeBorder(
                    resized, top, bottom, left, right,
                    cv2.BORDER_CONSTANT, value=[0, 0, 0]
                )

            return resized
        else:
            return cv2.resize(frame, size, interpolation=cv2.INTER_AREA)

    @log_execution_time
    def enhance_frame(
        self,
        frame: np.ndarray,
        brightness: float = 1.0,
        contrast: float = 1.0,
        denoise: bool = False
    ) -> np.ndarray:
        """
        تحسين الإطار

        Args:
            frame: الإطار الأصلي
            brightness: السطوع (1.0 = بدون تغيير)
            contrast: التباين (1.0 = بدون تغيير)
            denoise: إزالة الضوضاء

        Returns:
            الإطار المحسن
        """
        enhanced = frame.copy()

        # تعديل السطوع والتباين
        if brightness != 1.0 or contrast != 1.0:
            enhanced = cv2.convertScaleAbs(enhanced, alpha=contrast, beta=(brightness - 1) * 255)

        # إزالة الضوضاء
        if denoise:
            enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)

        return enhanced

    def apply_clahe(self, frame: np.ndarray) -> np.ndarray:
        """
        تطبيق CLAHE (Contrast Limited Adaptive Histogram Equalization)

        Args:
            frame: الإطار الأصلي

        Returns:
            الإطار المحسن
        """
        # تحويل إلى LAB
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # تطبيق CLAHE على قناة L
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)

        # دمج القنوات
        enhanced_lab = cv2.merge([l, a, b])

        # تحويل إلى BGR
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    def crop_frame(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> np.ndarray:
        """
        قص الإطار

        Args:
            frame: الإطار الأصلي
            bbox: صندوق الحدود (x, y, width, height)

        Returns:
            الإطار المقصوص
        """
        x, y, w, h = bbox
        return frame[y:y + h, x:x + w]

    def rotate_frame(self, frame: np.ndarray, angle: float) -> np.ndarray:
        """
        تدوير الإطار

        Args:
            frame: الإطار الأصلي
            angle: زاوية الدوران (بالدرجات)

        Returns:
            الإطار المدور
        """
        height, width = frame.shape[:2]
        center = (width // 2, height // 2)

        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(frame, rotation_matrix, (width, height))

        return rotated

    def flip_frame(self, frame: np.ndarray, flip_code: int = 1) -> np.ndarray:
        """
        قلب الإطار

        Args:
            frame: الإطار الأصلي
            flip_code: 0=عمودي, 1=أفقي, -1=كلاهما

        Returns:
            الإطار المقلوب
        """
        return cv2.flip(frame, flip_code)

    def convert_to_grayscale(self, frame: np.ndarray) -> np.ndarray:
        """تحويل الإطار إلى رمادي"""
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def convert_to_rgb(self, frame: np.ndarray) -> np.ndarray:
        """تحويل الإطار من BGR إلى RGB"""
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def save_frame(
        self,
        frame: np.ndarray,
        output_path: str,
        quality: int = 95
    ) -> bool:
        """
        حفظ الإطار كصورة

        Args:
            frame: الإطار
            output_path: مسار الملف
            quality: جودة الصورة (0-100)

        Returns:
            True إذا نجحت العملية
        """
        try:
            cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            return True
        except Exception as e:
            self.logger.error(f"خطأ في حفظ الإطار: {e}")
            return False

    def create_video_from_frames(
        self,
        frames: List[np.ndarray],
        output_path: str,
        fps: Optional[float] = None,
        codec: str = 'mp4v'
    ) -> bool:
        """
        إنشاء فيديو من الإطارات

        Args:
            frames: قائمة الإطارات
            output_path: مسار الملف الناتج
            fps: معدل الإطارات (يستخدم الأصلي إذا لم يحدد)
            codec: ترميز الفيديو

        Returns:
            True إذا نجحت العملية
        """
        if not frames:
            self.logger.error("قائمة الإطارات فارغة")
            return False

        try:
            if fps is None:
                fps = self.video_info.fps if self.video_info else 30.0

            height, width = frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*codec)

            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            for frame in frames:
                writer.write(frame)

            writer.release()

            self.logger.info(f"تم حفظ الفيديو: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء الفيديو: {e}")
            return False

    def get_frame_at_time(self, timestamp: float) -> Optional[np.ndarray]:
        """
        الحصول على إطار عند وقت معين

        Args:
            timestamp: الوقت بالثواني

        Returns:
            الإطار أو None
        """
        if self.video_info is None:
            return None

        frame_number = int(timestamp * self.video_info.fps)
        return self.read_frame(frame_number)

    def get_video_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الفيديو"""
        if self.video_info is None:
            return {}

        return {
            'width': self.video_info.width,
            'height': self.video_info.height,
            'fps': self.video_info.fps,
            'frame_count': self.video_info.frame_count,
            'duration_seconds': self.video_info.duration,
            'codec': self.video_info.codec,
            'size_mb': self.video_info.size_mb,
            'resolution': f"{self.video_info.width}x{self.video_info.height}",
            'aspect_ratio': self.video_info.width / self.video_info.height,
        }

    def close(self):
        """إغلاق الفيديو وتحرير الموارد"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.logger.info("تم إغلاق الفيديو")

    def __enter__(self):
        """Context manager entry"""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __del__(self):
        """Destructor"""
        self.close()
