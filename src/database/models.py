"""
نماذج قاعدة البيانات
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class Skater(Base):
    """نموذج المتزلج"""
    __tablename__ = 'skaters'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    country = Column(String(100))
    birth_date = Column(DateTime)
    gender = Column(String(10))
    category = Column(String(50))  # Junior, Senior
    discipline = Column(String(50))  # Men, Women, Pairs, Ice Dance

    # إحصائيات
    total_videos = Column(Integer, default=0)
    total_analyses = Column(Integer, default=0)
    average_score = Column(Float)
    best_score = Column(Float)
    improvement_rate = Column(Float)

    # معلومات إضافية
    coach_name = Column(String(200))
    club = Column(String(200))
    notes = Column(Text)

    # بيانات العضوية
    level = Column(String(50))  # Beta, Gamma, etc.
    bundle = Column(String(100))  # On-Ice Silver, Bronze, etc.
    membership_status = Column(String(50), default='active')  # active, inactive, suspended

    # الصورة الشخصية
    photo_path = Column(String(500))  # مسار الصورة

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # العلاقات
    videos = relationship('Video', back_populates='skater', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Skater(id={self.id}, name='{self.name}')>"


class Video(Base):
    """نموذج الفيديو"""
    __tablename__ = 'videos'

    id = Column(Integer, primary_key=True)
    skater_id = Column(Integer, ForeignKey('skaters.id'), nullable=False, index=True)

    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_mb = Column(Float)
    duration_seconds = Column(Float)
    fps = Column(Float)
    resolution = Column(String(50))
    codec = Column(String(50))

    program_type = Column(String(50))  # short, free, training
    competition_name = Column(String(200))
    competition_date = Column(DateTime)

    upload_date = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(50), default='pending')  # pending, processing, completed, failed

    # العلاقات
    skater = relationship('Skater', back_populates='videos')
    analyses = relationship('Analysis', back_populates='video', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_skater_status', 'skater_id', 'status'),
    )

    def __repr__(self):
        return f"<Video(id={self.id}, filename='{self.filename}')>"


class Analysis(Base):
    """نموذج التحليل"""
    __tablename__ = 'analyses'

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False, index=True)

    analysis_type = Column(String(100))  # full, quick, pose_only
    processing_time_seconds = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    status = Column(String(50), default='pending')

    # نتائج عامة
    overall_score = Column(Float)
    confidence = Column(Float)
    analysis_metadata = Column(JSON)

    # العلاقات
    video = relationship('Video', back_populates='analyses')
    movements = relationship('Movement', back_populates='analysis', cascade='all, delete-orphan')
    scores = relationship('Score', back_populates='analysis', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Analysis(id={self.id}, type='{self.analysis_type}')>"


class Movement(Base):
    """نموذج الحركة"""
    __tablename__ = 'movements'

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=False, index=True)

    movement_type = Column(String(100), index=True)  # jump, spin, step, spiral
    movement_name = Column(String(200))
    isu_code = Column(String(50))

    # توقيت
    start_frame = Column(Integer)
    end_frame = Column(Integer)
    start_time = Column(Float)
    end_time = Column(Float)
    duration = Column(Float)

    # بيانات تقنية
    pose_data = Column(JSON)
    trajectory = Column(JSON)
    velocity_data = Column(JSON)

    # تقييم
    quality_score = Column(Float)
    execution_score = Column(Float)
    difficulty_level = Column(Float)
    goe = Column(Integer)  # -5 to +5
    base_value = Column(Float)

    detected_errors = Column(JSON)
    recommendations = Column(JSON)

    # العلاقات
    analysis = relationship('Analysis', back_populates='movements')

    __table_args__ = (
        Index('idx_analysis_type', 'analysis_id', 'movement_type'),
    )

    def __repr__(self):
        return f"<Movement(id={self.id}, type='{self.movement_type}')>"


class Score(Base):
    """نموذج الدرجات"""
    __tablename__ = 'scores'

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=False, index=True)

    # Technical Score
    total_base_value = Column(Float)
    total_goe = Column(Float)
    technical_score = Column(Float)

    # Program Components
    skating_skills = Column(Float)
    transitions = Column(Float)
    performance = Column(Float)
    composition = Column(Float)
    interpretation = Column(Float)
    program_components_score = Column(Float)
    components_factor = Column(Float, default=1.0)

    # Final Score
    total_deductions = Column(Float, default=0.0)
    total_score = Column(Float)

    # Details
    elements_breakdown = Column(JSON)
    deductions_breakdown = Column(JSON)
    comparison_data = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    # العلاقات
    analysis = relationship('Analysis', back_populates='scores')

    def __repr__(self):
        return f"<Score(id={self.id}, total={self.total_score:.2f})>"


class Attendance(Base):
    """نموذج الحضور"""
    __tablename__ = 'attendance'

    id = Column(Integer, primary_key=True)
    skater_id = Column(Integer, ForeignKey('skaters.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # present, absent, excused, late
    session_type = Column(String(50))  # on-ice, off-ice, competition
    notes = Column(Text)
    recorded_by = Column(String(100))  # اسم المدرب أو الإداري

    created_at = Column(DateTime, default=datetime.utcnow)

    # العلاقات
    skater = relationship('Skater', backref='attendance_records')

    __table_args__ = (
        Index('idx_skater_date', 'skater_id', 'date'),
    )

    def __repr__(self):
        return f"<Attendance(id={self.id}, skater_id={self.skater_id}, status='{self.status}')>"


class Payment(Base):
    """نموذج المدفوعات"""
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    skater_id = Column(Integer, ForeignKey('skaters.id'), nullable=False, index=True)

    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, nullable=False, index=True)
    payment_method = Column(String(50))  # cash, instapay, credit_card, bank_transfer

    bundle_type = Column(String(100))  # On-Ice Bronze, On-Ice Silver, etc.
    period_start = Column(DateTime)  # بداية فترة الاشتراك
    period_end = Column(DateTime)    # نهاية فترة الاشتراك

    status = Column(String(20), default='completed')  # pending, completed, refunded
    discount = Column(Float, default=0.0)
    notes = Column(Text)
    received_by = Column(String(100))  # من استلم الدفعة

    created_at = Column(DateTime, default=datetime.utcnow)

    # العلاقات
    skater = relationship('Skater', backref='payments')

    __table_args__ = (
        Index('idx_skater_payment_date', 'skater_id', 'payment_date'),
        Index('idx_payment_status', 'status'),
    )

    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount}, status='{self.status}')>"


class Schedule(Base):
    """نموذج جدول التدريبات"""
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True)

    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(10), nullable=False)  # "09:00"
    end_time = Column(String(10), nullable=False)    # "10:00"

    session_type = Column(String(50))  # on-ice, off-ice
    level = Column(String(50))  # Beta, Gamma, Delta, etc.
    coach_id = Column(Integer, ForeignKey('skaters.id'))  # المدرب

    max_capacity = Column(Integer, default=15)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # العلاقات
    coach = relationship('Skater', foreign_keys=[coach_id])

    __table_args__ = (
        Index('idx_day_time', 'day_of_week', 'start_time'),
    )

    def __repr__(self):
        return f"<Schedule(id={self.id}, day={self.day_of_week}, time={self.start_time})>"
