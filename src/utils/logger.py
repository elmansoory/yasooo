"""
نظام التسجيل (Logging) المتقدم
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import colorlog


def setup_logger(
    name: str = None,
    log_file: Optional[Path] = None,
    log_level: str = 'INFO',
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    use_color: bool = True
) -> logging.Logger:
    """
    إعداد نظام التسجيل المتقدم

    Args:
        name: اسم المسجل
        log_file: مسار ملف السجل
        log_level: مستوى التسجيل
        max_bytes: الحد الأقصى لحجم الملف
        backup_count: عدد الملفات الاحتياطية
        use_color: استخدام الألوان في وحدة التحكم

    Returns:
        كائن Logger
    """

    # إنشاء المسجل
    logger = logging.getLogger(name or __name__)
    logger.setLevel(getattr(logging, log_level.upper()))

    # إزالة المعالجات الموجودة لتجنب التكرار
    logger.handlers = []

    # تنسيق السجلات الأساسي
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # معالج وحدة التحكم مع الألوان
    if use_color:
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt=date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(color_formatter)
    else:
        console_formatter = logging.Formatter(log_format, datefmt=date_format)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)

    # معالج الملفات مع التدوير
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )

        file_formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


class LoggerMixin:
    """
    Mixin لإضافة إمكانية التسجيل إلى أي فئة
    """

    @property
    def logger(self) -> logging.Logger:
        """الحصول على مسجل للفئة"""
        name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return logging.getLogger(name)


def log_execution_time(func):
    """
    Decorator لتسجيل وقت تنفيذ الدالة
    """
    import time
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                f"{func.__name__} تم تنفيذها في {execution_time:.2f} ثانية"
            )
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{func.__name__} فشلت بعد {execution_time:.2f} ثانية: {e}"
            )
            raise

    return wrapper


def log_exception(logger: logging.Logger = None):
    """
    Decorator لتسجيل الاستثناءات
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"استثناء في {func.__name__}: {str(e)}"
                )
                raise

        return wrapper

    return decorator
