"""
أدوات التحقق والتأكد من صحة البيانات
"""
from pathlib import Path
from typing import Union, List
import re


class VideoValidator:
    """التحقق من صحة ملفات الفيديو"""

    ALLOWED_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    MAX_FILE_SIZE_MB = 500

    @classmethod
    def validate_file_exists(cls, file_path: Union[str, Path]) -> bool:
        """التحقق من وجود الملف"""
        return Path(file_path).exists()

    @classmethod
    def validate_file_extension(cls, file_path: Union[str, Path]) -> bool:
        """التحقق من امتداد الملف"""
        extension = Path(file_path).suffix.lower()
        return extension in cls.ALLOWED_EXTENSIONS

    @classmethod
    def validate_file_size(
        cls,
        file_path: Union[str, Path],
        max_size_mb: int = None
    ) -> bool:
        """التحقق من حجم الملف"""
        if max_size_mb is None:
            max_size_mb = cls.MAX_FILE_SIZE_MB

        file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        return file_size_mb <= max_size_mb

    @classmethod
    def validate_video_file(
        cls,
        file_path: Union[str, Path],
        max_size_mb: int = None
    ) -> tuple[bool, str]:
        """
        التحقق الشامل من صحة ملف الفيديو

        Returns:
            (is_valid, error_message)
        """
        path = Path(file_path)

        # التحقق من الوجود
        if not cls.validate_file_exists(path):
            return False, "الملف غير موجود"

        # التحقق من الامتداد
        if not cls.validate_file_extension(path):
            return False, f"الامتداد غير مدعوم. الامتدادات المدعومة: {', '.join(cls.ALLOWED_EXTENSIONS)}"

        # التحقق من الحجم
        if not cls.validate_file_size(path, max_size_mb):
            max_size = max_size_mb or cls.MAX_FILE_SIZE_MB
            return False, f"حجم الملف يتجاوز الحد الأقصى ({max_size} MB)"

        return True, ""


class DataValidator:
    """التحقق من صحة البيانات"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """التحقق من صحة البريد الإلكتروني"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_username(username: str, min_length: int = 3, max_length: int = 30) -> bool:
        """التحقق من صحة اسم المستخدم"""
        if not username or len(username) < min_length or len(username) > max_length:
            return False

        pattern = r'^[a-zA-Z0-9_]+$'
        return bool(re.match(pattern, username))

    @staticmethod
    def validate_score(score: float, min_score: float = 0.0, max_score: float = 10.0) -> bool:
        """التحقق من صحة الدرجة"""
        return min_score <= score <= max_score

    @staticmethod
    def validate_goe(goe: int) -> bool:
        """التحقق من صحة قيمة GOE"""
        return -5 <= goe <= 5

    @staticmethod
    def validate_age(age: int, min_age: int = 5, max_age: int = 100) -> bool:
        """التحقق من صحة العمر"""
        return min_age <= age <= max_age

    @staticmethod
    def validate_not_empty(value: str, field_name: str = "الحقل") -> tuple[bool, str]:
        """التحقق من أن القيمة غير فارغة"""
        if not value or not value.strip():
            return False, f"{field_name} مطلوب ولا يمكن أن يكون فارغاً"
        return True, ""

    @staticmethod
    def validate_string_length(
        value: str,
        min_length: int = 0,
        max_length: int = None,
        field_name: str = "الحقل"
    ) -> tuple[bool, str]:
        """التحقق من طول النص"""
        length = len(value)

        if length < min_length:
            return False, f"{field_name} يجب أن يكون على الأقل {min_length} حرف"

        if max_length and length > max_length:
            return False, f"{field_name} يجب ألا يتجاوز {max_length} حرف"

        return True, ""

    @staticmethod
    def validate_number_range(
        value: Union[int, float],
        min_value: Union[int, float] = None,
        max_value: Union[int, float] = None,
        field_name: str = "القيمة"
    ) -> tuple[bool, str]:
        """التحقق من نطاق الرقم"""
        if min_value is not None and value < min_value:
            return False, f"{field_name} يجب أن تكون على الأقل {min_value}"

        if max_value is not None and value > max_value:
            return False, f"{field_name} يجب ألا تتجاوز {max_value}"

        return True, ""

    @staticmethod
    def validate_list_not_empty(
        values: List,
        field_name: str = "القائمة"
    ) -> tuple[bool, str]:
        """التحقق من أن القائمة غير فارغة"""
        if not values or len(values) == 0:
            return False, f"{field_name} لا يمكن أن تكون فارغة"
        return True, ""


class ISUValidator:
    """التحقق من صحة عناصر ISU"""

    @staticmethod
    def validate_jump_code(code: str) -> bool:
        """التحقق من صحة رمز القفزة"""
        from src.config.isu_standards import ISUStandards
        return code in ISUStandards.JUMPS

    @staticmethod
    def validate_spin_code(code: str) -> bool:
        """التحقق من صحة رمز الدوران"""
        from src.config.isu_standards import ISUStandards

        # استخراج الكود الأساسي (بدون المستوى)
        base_code = code[:-1] if code and code[-1].isdigit() else code
        return base_code in ISUStandards.SPINS

    @staticmethod
    def validate_element_code(code: str) -> tuple[bool, str]:
        """
        التحقق من صحة رمز العنصر

        Returns:
            (is_valid, element_type)
        """
        from src.config.isu_standards import ISUStandards

        if code in ISUStandards.JUMPS:
            return True, 'jump'

        base_code = code[:-1] if code and code[-1].isdigit() else code
        if base_code in ISUStandards.SPINS:
            return True, 'spin'

        if base_code in ISUStandards.STEP_SEQUENCES:
            return True, 'step_sequence'

        return False, 'unknown'


class AnalysisValidator:
    """التحقق من صحة بيانات التحليل"""

    @staticmethod
    def validate_analysis_data(data: dict) -> tuple[bool, List[str]]:
        """
        التحقق من صحة بيانات التحليل

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # التحقق من الحقول المطلوبة
        required_fields = ['video_id', 'analysis_type']
        for field in required_fields:
            if field not in data:
                errors.append(f"الحقل '{field}' مطلوب")

        # التحقق من نوع التحليل
        if 'analysis_type' in data:
            valid_types = ['pose_detection', 'movement_classification', 'scoring']
            if data['analysis_type'] not in valid_types:
                errors.append(f"نوع التحليل غير صحيح. الأنواع المدعومة: {', '.join(valid_types)}")

        # التحقق من الدرجات إذا كانت موجودة
        if 'technical_score' in data:
            is_valid, msg = DataValidator.validate_score(data['technical_score'])
            if not is_valid:
                errors.append(f"الدرجة التقنية: {msg}")

        if 'artistic_score' in data:
            is_valid, msg = DataValidator.validate_score(data['artistic_score'])
            if not is_valid:
                errors.append(f"الدرجة الفنية: {msg}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_movement_data(data: dict) -> tuple[bool, List[str]]:
        """
        التحقق من صحة بيانات الحركة

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # التحقق من الحقول المطلوبة
        required_fields = ['movement_type', 'movement_name']
        for field in required_fields:
            if field not in data:
                errors.append(f"الحقل '{field}' مطلوب")

        # التحقق من نوع الحركة
        if 'movement_type' in data:
            valid_types = ['jump', 'spin', 'step', 'spiral', 'transition']
            if data['movement_type'] not in valid_types:
                errors.append(f"نوع الحركة غير صحيح. الأنواع المدعومة: {', '.join(valid_types)}")

        # التحقق من الأطر
        if 'start_frame' in data and 'end_frame' in data:
            if data['start_frame'] >= data['end_frame']:
                errors.append("إطار البداية يجب أن يكون قبل إطار النهاية")

        return len(errors) == 0, errors
