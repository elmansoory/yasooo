"""
نظام الإعدادات الرئيسي
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List

# تحميل المتغيرات البيئية
load_dotenv()


class Config:
    """الإعدادات الأساسية للنظام"""

    # المسارات الأساسية
    BASE_DIR = Path(__file__).parent.parent.parent
    SRC_DIR = BASE_DIR / "src"
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = DATA_DIR / "models"
    VIDEOS_DIR = DATA_DIR / "videos"
    CACHE_DIR = DATA_DIR / "cache"
    EXPORTS_DIR = DATA_DIR / "exports"
    LOGS_DIR = BASE_DIR / "logs"
    TESTS_DIR = BASE_DIR / "tests"
    DOCS_DIR = BASE_DIR / "docs"

    # إعدادات التطبيق
    APP_NAME = os.getenv('APP_NAME', 'Figure Skating Analysis System')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'

    # إعدادات الفيديو
    VIDEO_MAX_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', 500))
    VIDEO_ALLOWED_FORMATS: List[str] = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))
    VIDEO_RESOLUTION = (
        int(os.getenv('VIDEO_RESOLUTION_WIDTH', 1280)),
        int(os.getenv('VIDEO_RESOLUTION_HEIGHT', 720))
    )
    MAX_FRAMES_TO_PROCESS = int(os.getenv('MAX_FRAMES_TO_PROCESS', 1000))

    # إعدادات النموذج
    MODEL_INPUT_SIZE = (224, 224)
    MODEL_BATCH_SIZE = 32
    MODEL_CONFIDENCE_THRESHOLD = float(os.getenv('MODEL_CONFIDENCE_THRESHOLD', 0.7))

    # إعدادات MediaPipe للوضعيات
    POSE_MIN_DETECTION_CONFIDENCE = float(os.getenv('POSE_MIN_DETECTION_CONFIDENCE', 0.5))
    POSE_MIN_TRACKING_CONFIDENCE = float(os.getenv('POSE_MIN_TRACKING_CONFIDENCE', 0.5))
    POSE_MODEL_COMPLEXITY = int(os.getenv('POSE_MODEL_COMPLEXITY', 2))  # 0, 1, or 2

    # إعدادات قاعدة البيانات
    DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/skating_analysis.db')
    DATABASE_POOL_SIZE = 10
    DATABASE_MAX_OVERFLOW = 20
    DATABASE_POOL_RECYCLE = 3600

    # إعدادات Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

    # إعدادات التخزين المؤقت
    ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'True').lower() == 'true'
    CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', 3600))

    # إعدادات Streamlit
    STREAMLIT_THEME = {
        'primaryColor': '#0066cc',
        'backgroundColor': '#ffffff',
        'secondaryBackgroundColor': '#f0f2f6',
        'textColor': '#262730',
        'font': 'sans serif'
    }

    # إعدادات التسجيل
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = LOGS_DIR / 'app.log'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # إعدادات الأمان
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-me-in-production-jwt')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 30))
    MAX_UPLOAD_SIZE_MB = int(os.getenv('MAX_UPLOAD_SIZE_MB', 500))
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

    # إعدادات الأداء
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    USE_GPU = True  # سيتم التحقق من التوفر تلقائياً

    # إعدادات التحليل
    ANALYSIS_MODES = {
        'fast': {
            'name': 'سريع',
            'max_frames': 100,
            'skip_frames': 3,
            'description': 'تحليل سريع للنظرة العامة'
        },
        'standard': {
            'name': 'قياسي',
            'max_frames': 300,
            'skip_frames': 1,
            'description': 'تحليل متوازن بين السرعة والدقة'
        },
        'detailed': {
            'name': 'مفصل',
            'max_frames': 1000,
            'skip_frames': 0,
            'description': 'تحليل شامل ومفصل'
        }
    }

    # إعدادات التصدير
    EXPORT_FORMATS = ['pdf', 'excel', 'json', 'csv']

    @classmethod
    def create_directories(cls):
        """إنشاء المجلدات المطلوبة"""
        directories = [
            cls.DATA_DIR,
            cls.MODELS_DIR,
            cls.VIDEOS_DIR,
            cls.CACHE_DIR,
            cls.EXPORTS_DIR,
            cls.LOGS_DIR,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_config(cls) -> bool:
        """التحقق من صحة الإعدادات"""
        errors = []

        # التحقق من المسارات
        if not cls.BASE_DIR.exists():
            errors.append(f"المسار الأساسي غير موجود: {cls.BASE_DIR}")

        # التحقق من الإعدادات الأمنية
        if cls.SECRET_KEY == 'change-me-in-production' and not cls.DEBUG:
            errors.append("يجب تغيير SECRET_KEY في بيئة الإنتاج")

        if errors:
            for error in errors:
                print(f"خطأ في الإعدادات: {error}")
            return False

        return True


class DevelopmentConfig(Config):
    """إعدادات بيئة التطوير"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """إعدادات بيئة الإنتاج"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'

    # إعدادات أمان إضافية للإنتاج
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


class TestingConfig(Config):
    """إعدادات بيئة الاختبار"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    LOG_LEVEL = 'DEBUG'


# تحديد الإعدادات بناءً على البيئة
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None):
    """الحصول على كائن الإعدادات المناسب"""
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')

    config_class = config_by_name.get(env, DevelopmentConfig)

    # إنشاء المجلدات المطلوبة
    config_class.create_directories()

    # التحقق من صحة الإعدادات
    config_class.validate_config()

    return config_class


# تصدير كائن الإعدادات الافتراضي
config = get_config()
