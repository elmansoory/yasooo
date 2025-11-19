"""
معالج الملفات والمجلدات
"""
import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Union
import tempfile
from datetime import datetime


class FileHandler:
    """معالج الملفات والعمليات المتعلقة بها"""

    @staticmethod
    def ensure_dir(directory: Union[str, Path]) -> Path:
        """
        التأكد من وجود المجلد وإنشاؤه إذا لم يكن موجوداً

        Args:
            directory: مسار المجلد

        Returns:
            Path object للمجلد
        """
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """
        الحصول على حجم الملف بالبايت

        Args:
            file_path: مسار الملف

        Returns:
            حجم الملف بالبايت
        """
        return Path(file_path).stat().st_size

    @staticmethod
    def get_file_size_mb(file_path: Union[str, Path]) -> float:
        """
        الحصول على حجم الملف بالميجابايت

        Args:
            file_path: مسار الملف

        Returns:
            حجم الملف بالميجابايت
        """
        size_bytes = FileHandler.get_file_size(file_path)
        return size_bytes / (1024 * 1024)

    @staticmethod
    def calculate_md5(file_path: Union[str, Path]) -> str:
        """
        حساب MD5 hash للملف

        Args:
            file_path: مسار الملف

        Returns:
            MD5 hash كنص
        """
        hash_md5 = hashlib.md5()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    @staticmethod
    def copy_file(
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False
    ) -> bool:
        """
        نسخ ملف

        Args:
            source: مسار الملف المصدر
            destination: مسار الوجهة
            overwrite: الكتابة فوق الملف الموجود

        Returns:
            True إذا نجحت العملية
        """
        source_path = Path(source)
        dest_path = Path(destination)

        if not source_path.exists():
            raise FileNotFoundError(f"الملف المصدر غير موجود: {source}")

        if dest_path.exists() and not overwrite:
            raise FileExistsError(f"الملف موجود بالفعل: {destination}")

        # التأكد من وجود مجلد الوجهة
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_path, dest_path)
        return True

    @staticmethod
    def move_file(
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False
    ) -> bool:
        """
        نقل ملف

        Args:
            source: مسار الملف المصدر
            destination: مسار الوجهة
            overwrite: الكتابة فوق الملف الموجود

        Returns:
            True إذا نجحت العملية
        """
        source_path = Path(source)
        dest_path = Path(destination)

        if not source_path.exists():
            raise FileNotFoundError(f"الملف المصدر غير موجود: {source}")

        if dest_path.exists() and not overwrite:
            raise FileExistsError(f"الملف موجود بالفعل: {destination}")

        # التأكد من وجود مجلد الوجهة
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(source_path), str(dest_path))
        return True

    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> bool:
        """
        حذف ملف

        Args:
            file_path: مسار الملف

        Returns:
            True إذا نجحت العملية
        """
        path = Path(file_path)

        if path.exists():
            path.unlink()
            return True

        return False

    @staticmethod
    def clean_directory(
        directory: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False
    ) -> int:
        """
        تنظيف المجلد من الملفات

        Args:
            directory: مسار المجلد
            pattern: نمط الملفات المراد حذفها
            recursive: الحذف بشكل تكراري

        Returns:
            عدد الملفات المحذوفة
        """
        path = Path(directory)
        count = 0

        if not path.exists():
            return count

        if recursive:
            files = path.rglob(pattern)
        else:
            files = path.glob(pattern)

        for file in files:
            if file.is_file():
                file.unlink()
                count += 1

        return count

    @staticmethod
    def get_files_in_directory(
        directory: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """
        الحصول على قائمة الملفات في المجلد

        Args:
            directory: مسار المجلد
            pattern: نمط الملفات
            recursive: البحث بشكل تكراري

        Returns:
            قائمة بمسارات الملفات
        """
        path = Path(directory)

        if not path.exists():
            return []

        if recursive:
            files = path.rglob(pattern)
        else:
            files = path.glob(pattern)

        return [f for f in files if f.is_file()]

    @staticmethod
    def create_temp_file(suffix: str = "", prefix: str = "tmp") -> Path:
        """
        إنشاء ملف مؤقت

        Args:
            suffix: لاحقة الملف
            prefix: بادئة الملف

        Returns:
            مسار الملف المؤقت
        """
        temp_file = tempfile.NamedTemporaryFile(
            suffix=suffix,
            prefix=prefix,
            delete=False
        )
        temp_file.close()
        return Path(temp_file.name)

    @staticmethod
    def create_temp_directory(prefix: str = "tmp") -> Path:
        """
        إنشاء مجلد مؤقت

        Args:
            prefix: بادئة المجلد

        Returns:
            مسار المجلد المؤقت
        """
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        return Path(temp_dir)

    @staticmethod
    def generate_unique_filename(
        directory: Union[str, Path],
        base_name: str,
        extension: str
    ) -> Path:
        """
        توليد اسم ملف فريد

        Args:
            directory: مسار المجلد
            base_name: الاسم الأساسي
            extension: الامتداد

        Returns:
            مسار الملف الفريد
        """
        path = Path(directory)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}{extension}"
        full_path = path / filename

        # إضافة رقم إذا كان الملف موجوداً
        counter = 1
        while full_path.exists():
            filename = f"{base_name}_{timestamp}_{counter}{extension}"
            full_path = path / filename
            counter += 1

        return full_path

    @staticmethod
    def get_directory_size(directory: Union[str, Path]) -> int:
        """
        حساب حجم المجلد الإجمالي

        Args:
            directory: مسار المجلد

        Returns:
            الحجم بالبايت
        """
        path = Path(directory)
        total_size = 0

        for item in path.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size

        return total_size

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        تنسيق حجم الملف للعرض

        Args:
            size_bytes: الحجم بالبايت

        Returns:
            الحجم المنسق (مثل: "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.2f} PB"
