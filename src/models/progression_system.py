"""
نظام المستويات والترقيات
Player Progression & Leveling System
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd


class SkillLevel(Enum):
    """مستويات المهارة"""
    BEGINNER = "مبتدئ"
    ELEMENTARY = "ابتدائي"
    INTERMEDIATE = "متوسط"
    ADVANCED = "متقدم"
    EXPERT = "خبير"
    PROFESSIONAL = "محترف"
    ELITE = "نخبة"


class BadgeType(Enum):
    """أنواع الشارات"""
    ATTENDANCE = "الحضور"
    PERFORMANCE = "الأداء"
    ACHIEVEMENT = "الإنجاز"
    MILESTONE = "إنجاز مهم"
    SPECIAL = "خاص"


@dataclass
class Badge:
    """شارة إنجاز"""
    id: str
    name: str
    description: str
    badge_type: BadgeType
    icon: str
    points: int
    rarity: str  # common, rare, epic, legendary
    unlocked_at: Optional[datetime] = None

    def is_unlocked(self) -> bool:
        return self.unlocked_at is not None


@dataclass
class LevelRequirements:
    """متطلبات المستوى"""
    level: SkillLevel
    min_attendance: int
    min_points: int
    min_days: int
    required_badges: List[str]
    description: str


class ProgressionSystem:
    """نظام التقدم والترقيات"""

    # تعريف المستويات ومتطلباتها
    LEVEL_REQUIREMENTS = {
        SkillLevel.BEGINNER: LevelRequirements(
            level=SkillLevel.BEGINNER,
            min_attendance=0,
            min_points=0,
            min_days=0,
            required_badges=[],
            description="المستوى الابتدائي - بداية الرحلة"
        ),
        SkillLevel.ELEMENTARY: LevelRequirements(
            level=SkillLevel.ELEMENTARY,
            min_attendance=10,
            min_points=100,
            min_days=30,
            required_badges=["first_week"],
            description="مستوى ابتدائي - تعلم الأساسيات"
        ),
        SkillLevel.INTERMEDIATE: LevelRequirements(
            level=SkillLevel.INTERMEDIATE,
            min_attendance=30,
            min_points=500,
            min_days=90,
            required_badges=["first_week", "consistent_10"],
            description="مستوى متوسط - إتقان المهارات الأساسية"
        ),
        SkillLevel.ADVANCED: LevelRequirements(
            level=SkillLevel.ADVANCED,
            min_attendance=60,
            min_points=1500,
            min_days=180,
            required_badges=["first_week", "consistent_10", "consistent_30"],
            description="مستوى متقدم - مهارات احترافية"
        ),
        SkillLevel.EXPERT: LevelRequirements(
            level=SkillLevel.EXPERT,
            min_attendance=120,
            min_points=3000,
            min_days=365,
            required_badges=["first_week", "consistent_30", "perfect_month"],
            description="مستوى خبير - احتراف عالي"
        ),
        SkillLevel.PROFESSIONAL: LevelRequirements(
            level=SkillLevel.PROFESSIONAL,
            min_attendance=200,
            min_points=5000,
            min_days=540,
            required_badges=["first_week", "consistent_30", "perfect_month", "year_warrior"],
            description="مستوى محترف - مستوى عالمي"
        ),
        SkillLevel.ELITE: LevelRequirements(
            level=SkillLevel.ELITE,
            min_attendance=365,
            min_points=10000,
            min_days=730,
            required_badges=["first_week", "perfect_month", "year_warrior", "legend"],
            description="النخبة - قمة الاحتراف"
        )
    }

    # تعريف الشارات
    BADGES = {
        # شارات الحضور
        "first_day": Badge(
            "first_day", "اليوم الأول", "حضور أول يوم تدريب",
            BadgeType.ATTENDANCE, "🎉", 10, "common"
        ),
        "first_week": Badge(
            "first_week", "الأسبوع الأول", "إكمال أسبوع كامل من التدريب",
            BadgeType.ATTENDANCE, "🌟", 50, "common"
        ),
        "consistent_10": Badge(
            "consistent_10", "المثابر", "10 أيام حضور متتالية",
            BadgeType.ATTENDANCE, "💪", 100, "rare"
        ),
        "consistent_30": Badge(
            "consistent_30", "الملتزم", "30 يوم حضور متتالي",
            BadgeType.ATTENDANCE, "🔥", 300, "epic"
        ),
        "perfect_month": Badge(
            "perfect_month", "الشهر الكامل", "حضور جميع أيام التدريب في شهر",
            BadgeType.MILESTONE, "🏆", 500, "epic"
        ),
        "year_warrior": Badge(
            "year_warrior", "محارب السنة", "حضور 200+ يوم في سنة",
            BadgeType.ACHIEVEMENT, "⚔️", 1000, "legendary"
        ),
        "legend": Badge(
            "legend", "الأسطورة", "حضور 365+ يوم",
            BadgeType.SPECIAL, "👑", 2000, "legendary"
        ),

        # شارات الأداء
        "first_jump": Badge(
            "first_jump", "القفزة الأولى", "تنفيذ أول قفزة ناجحة",
            BadgeType.PERFORMANCE, "🦘", 50, "common"
        ),
        "perfect_spin": Badge(
            "perfect_spin", "الدوران المثالي", "تنفيذ دوران مثالي",
            BadgeType.PERFORMANCE, "🌀", 150, "rare"
        ),
        "combo_master": Badge(
            "combo_master", "سيد الكومبو", "تنفيذ تسلسل حركات معقد",
            BadgeType.ACHIEVEMENT, "🎯", 300, "epic"
        ),

        # شارات خاصة
        "early_bird": Badge(
            "early_bird", "الطائر المبكر", "الحضور قبل 6 صباحاً 10 مرات",
            BadgeType.SPECIAL, "🐦", 200, "rare"
        ),
        "night_owl": Badge(
            "night_owl", "بومة الليل", "التدريب المسائي 20 مرة",
            BadgeType.SPECIAL, "🦉", 200, "rare"
        ),
        "team_player": Badge(
            "team_player", "روح الفريق", "المشاركة في 10 تدريبات جماعية",
            BadgeType.SPECIAL, "🤝", 250, "epic"
        )
    }

    def __init__(self):
        self.badges_db = self.BADGES.copy()

    def calculate_level(self, attendance_count: int, points: int,
                       days_active: int, earned_badges: List[str]) -> SkillLevel:
        """حساب مستوى اللاعب"""
        current_level = SkillLevel.BEGINNER

        # التحقق من كل مستوى بالترتيب
        for level in [SkillLevel.ELEMENTARY, SkillLevel.INTERMEDIATE,
                     SkillLevel.ADVANCED, SkillLevel.EXPERT,
                     SkillLevel.PROFESSIONAL, SkillLevel.ELITE]:

            req = self.LEVEL_REQUIREMENTS[level]

            # التحقق من المتطلبات
            if (attendance_count >= req.min_attendance and
                points >= req.min_points and
                days_active >= req.min_days and
                all(badge in earned_badges for badge in req.required_badges)):
                current_level = level
            else:
                break

        return current_level

    def get_progress_to_next_level(self, current_level: SkillLevel,
                                   attendance_count: int, points: int,
                                   days_active: int,
                                   earned_badges: List[str]) -> Dict:
        """حساب التقدم نحو المستوى التالي"""
        level_order = [
            SkillLevel.BEGINNER, SkillLevel.ELEMENTARY, SkillLevel.INTERMEDIATE,
            SkillLevel.ADVANCED, SkillLevel.EXPERT, SkillLevel.PROFESSIONAL,
            SkillLevel.ELITE
        ]

        current_index = level_order.index(current_level)

        if current_index == len(level_order) - 1:
            return {
                "next_level": None,
                "progress": 100,
                "requirements_met": True,
                "missing_requirements": []
            }

        next_level = level_order[current_index + 1]
        req = self.LEVEL_REQUIREMENTS[next_level]

        # حساب التقدم
        attendance_progress = min(100, (attendance_count / req.min_attendance) * 100)
        points_progress = min(100, (points / req.min_points) * 100)
        days_progress = min(100, (days_active / req.min_days) * 100)

        missing_badges = [b for b in req.required_badges if b not in earned_badges]
        badges_progress = ((len(req.required_badges) - len(missing_badges)) /
                          len(req.required_badges) * 100) if req.required_badges else 100

        overall_progress = (attendance_progress + points_progress +
                          days_progress + badges_progress) / 4

        missing_requirements = []
        if attendance_count < req.min_attendance:
            missing_requirements.append(
                f"الحضور: {attendance_count}/{req.min_attendance}"
            )
        if points < req.min_points:
            missing_requirements.append(f"النقاط: {points}/{req.min_points}")
        if days_active < req.min_days:
            missing_requirements.append(f"الأيام: {days_active}/{req.min_days}")
        if missing_badges:
            missing_requirements.append(f"الشارات المطلوبة: {', '.join(missing_badges)}")

        return {
            "next_level": next_level,
            "progress": round(overall_progress, 2),
            "requirements_met": len(missing_requirements) == 0,
            "missing_requirements": missing_requirements,
            "breakdown": {
                "attendance": round(attendance_progress, 2),
                "points": round(points_progress, 2),
                "days": round(days_progress, 2),
                "badges": round(badges_progress, 2)
            }
        }

    def check_badge_eligibility(self, badge_id: str,
                               attendance_data: pd.DataFrame,
                               performance_data: Optional[Dict] = None) -> bool:
        """التحقق من أهلية الحصول على شارة"""
        if badge_id not in self.badges_db:
            return False

        badge = self.badges_db[badge_id]

        # منطق التحقق لكل شارة
        if badge_id == "first_day":
            return len(attendance_data) >= 1

        elif badge_id == "first_week":
            return len(attendance_data) >= 7

        elif badge_id == "consistent_10":
            return self._check_consecutive_days(attendance_data, 10)

        elif badge_id == "consistent_30":
            return self._check_consecutive_days(attendance_data, 30)

        elif badge_id == "perfect_month":
            return self._check_perfect_month(attendance_data)

        elif badge_id == "year_warrior":
            # التحقق من الحضور في آخر 365 يوم
            if 'date' in attendance_data.columns:
                year_ago = datetime.now() - timedelta(days=365)
                recent = attendance_data[
                    pd.to_datetime(attendance_data['date']) >= year_ago
                ]
                return len(recent) >= 200

        elif badge_id == "legend":
            return len(attendance_data) >= 365

        return False

    def _check_consecutive_days(self, attendance_data: pd.DataFrame,
                               required_days: int) -> bool:
        """التحقق من الأيام المتتالية"""
        if 'date' not in attendance_data.columns or len(attendance_data) < required_days:
            return False

        dates = pd.to_datetime(attendance_data['date']).sort_values()
        dates = dates.drop_duplicates()

        max_streak = 0
        current_streak = 1

        for i in range(1, len(dates)):
            diff = (dates.iloc[i] - dates.iloc[i-1]).days

            if diff == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        return max_streak >= required_days

    def _check_perfect_month(self, attendance_data: pd.DataFrame) -> bool:
        """التحقق من الشهر الكامل"""
        if 'date' not in attendance_data.columns:
            return False

        dates = pd.to_datetime(attendance_data['date'])
        monthly_counts = dates.dt.to_period('M').value_counts()

        # افتراض أن الشهر الكامل = 20+ يوم
        return (monthly_counts >= 20).any()

    def calculate_points(self, attendance_count: int,
                        badges_earned: List[str]) -> int:
        """حساب مجموع النقاط"""
        # نقاط الحضور (10 نقاط لكل يوم)
        attendance_points = attendance_count * 10

        # نقاط الشارات
        badge_points = sum(
            self.badges_db[badge_id].points
            for badge_id in badges_earned
            if badge_id in self.badges_db
        )

        return attendance_points + badge_points

    def get_player_summary(self, member_id: int,
                          attendance_data: pd.DataFrame) -> Dict:
        """الحصول على ملخص كامل للاعب"""
        # حساب الإحصائيات الأساسية
        attendance_count = len(attendance_data)

        if 'date' in attendance_data.columns:
            dates = pd.to_datetime(attendance_data['date'])
            first_date = dates.min()
            days_active = (datetime.now() - first_date).days if not pd.isna(first_date) else 0
        else:
            days_active = 0

        # التحقق من الشارات المكتسبة
        earned_badges = []
        for badge_id in self.badges_db.keys():
            if self.check_badge_eligibility(badge_id, attendance_data):
                earned_badges.append(badge_id)

        # حساب النقاط والمستوى
        points = self.calculate_points(attendance_count, earned_badges)
        level = self.calculate_level(attendance_count, points, days_active, earned_badges)

        # حساب التقدم
        progress = self.get_progress_to_next_level(
            level, attendance_count, points, days_active, earned_badges
        )

        return {
            "member_id": member_id,
            "level": level,
            "level_name": level.value,
            "points": points,
            "attendance_count": attendance_count,
            "days_active": days_active,
            "earned_badges": earned_badges,
            "badges_count": len(earned_badges),
            "progress_to_next": progress,
            "achievements": self._get_achievements(earned_badges)
        }

    def _get_achievements(self, earned_badges: List[str]) -> List[Dict]:
        """الحصول على قائمة الإنجازات"""
        achievements = []
        for badge_id in earned_badges:
            if badge_id in self.badges_db:
                badge = self.badges_db[badge_id]
                achievements.append({
                    "id": badge.id,
                    "name": badge.name,
                    "description": badge.description,
                    "icon": badge.icon,
                    "points": badge.points,
                    "rarity": badge.rarity
                })
        return achievements


# مثال على الاستخدام
if __name__ == "__main__":
    # اختبار النظام
    system = ProgressionSystem()

    # بيانات تجريبية
    test_attendance = pd.DataFrame({
        'date': pd.date_range('2025-01-01', periods=50, freq='D')
    })

    summary = system.get_player_summary(1, test_attendance)
    print(f"المستوى: {summary['level_name']}")
    print(f"النقاط: {summary['points']}")
    print(f"الشارات: {summary['badges_count']}")
    print(f"التقدم للمستوى التالي: {summary['progress_to_next']['progress']}%")
