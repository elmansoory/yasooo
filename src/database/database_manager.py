"""
مدير قاعدة البيانات
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging

from src.database.models import Base
from src.utils.logger import LoggerMixin


class DatabaseManager(LoggerMixin):
    """مدير قاعدة البيانات الرئيسي"""

    def __init__(self, database_url: str, echo: bool = False):
        self.database_url = database_url
        self.echo = echo
        self.engine = None
        self.Session = None

    def init_db(self):
        """تهيئة قاعدة البيانات"""
        try:
            # إنشاء المحرك
            if 'sqlite' in self.database_url:
                self.engine = create_engine(
                    self.database_url,
                    echo=self.echo,
                    connect_args={'check_same_thread': False},
                    poolclass=StaticPool
                )
            else:
                self.engine = create_engine(
                    self.database_url,
                    echo=self.echo,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True
                )

            # تفعيل foreign keys لـ SQLite
            if 'sqlite' in self.database_url:
                @event.listens_for(self.engine, "connect")
                def set_sqlite_pragma(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()

            # إنشاء الجلسات
            session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(session_factory)

            # إنشاء الجداول
            Base.metadata.create_all(self.engine)

            self.logger.info("تم تهيئة قاعدة البيانات بنجاح")

        except Exception as e:
            self.logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
            raise

    @contextmanager
    def get_session(self):
        """الحصول على جلسة قاعدة بيانات"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"خطأ في الجلسة: {e}")
            raise
        finally:
            session.close()

    def close(self):
        """إغلاق الاتصالات"""
        if self.Session:
            self.Session.remove()
        if self.engine:
            self.engine.dispose()
