"""
محرك التحليلات المتقدم - Advanced Analytics Engine
يوفر تحليلات ذكية متقدمة لأداء اللاعبين
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import json


@dataclass
class PerformanceMetrics:
    """مقاييس الأداء"""
    player_id: int
    player_name: str

    # Attendance Metrics
    total_attendance: int
    attendance_rate: float  # 0-1
    consistency_score: float  # 0-1
    attendance_streak: int

    # Performance Metrics
    average_score: float
    best_score: float
    improvement_rate: float  # % per month
    skill_mastery: float  # 0-1

    # Engagement Metrics
    engagement_score: float  # 0-1
    commitment_level: str  # high, medium, low
    risk_of_dropout: float  # 0-1

    # Financial Metrics
    total_paid: float
    payment_consistency: float
    lifetime_value: float


@dataclass
class SkillProgression:
    """تطور المهارات"""
    skill_name: str
    skill_category: str  # jump, spin, step
    current_level: float  # 0-10
    target_level: float
    progress_rate: float  # improvement per week
    estimated_time_to_target: int  # days
    confidence: float  # 0-1


@dataclass
class PredictionResult:
    """نتيجة التنبؤ"""
    metric_name: str
    current_value: float
    predicted_value: float
    prediction_date: datetime
    confidence: float
    factors: Dict[str, float]


class AdvancedAnalytics:
    """محرك التحليلات المتقدم"""

    def __init__(self):
        self.performance_cache = {}
        self.trend_cache = {}

    def calculate_performance_metrics(
        self,
        player_id: int,
        player_name: str,
        attendance_records: List[Dict],
        score_records: List[Dict],
        payment_records: List[Dict]
    ) -> PerformanceMetrics:
        """
        حساب مقاييس الأداء الشاملة

        Args:
            player_id: معرف اللاعب
            player_name: اسم اللاعب
            attendance_records: سجلات الحضور
            score_records: سجلات الدرجات
            payment_records: سجلات المدفوعات

        Returns:
            PerformanceMetrics
        """
        # Attendance Metrics
        attendance_metrics = self._calculate_attendance_metrics(attendance_records)

        # Performance Metrics
        performance_metrics = self._calculate_performance_metrics(score_records)

        # Engagement Metrics
        engagement_metrics = self._calculate_engagement_metrics(
            attendance_records, score_records
        )

        # Financial Metrics
        financial_metrics = self._calculate_financial_metrics(payment_records)

        return PerformanceMetrics(
            player_id=player_id,
            player_name=player_name,
            total_attendance=attendance_metrics['total'],
            attendance_rate=attendance_metrics['rate'],
            consistency_score=attendance_metrics['consistency'],
            attendance_streak=attendance_metrics['streak'],
            average_score=performance_metrics['average'],
            best_score=performance_metrics['best'],
            improvement_rate=performance_metrics['improvement_rate'],
            skill_mastery=performance_metrics['mastery'],
            engagement_score=engagement_metrics['score'],
            commitment_level=engagement_metrics['level'],
            risk_of_dropout=engagement_metrics['dropout_risk'],
            total_paid=financial_metrics['total'],
            payment_consistency=financial_metrics['consistency'],
            lifetime_value=financial_metrics['ltv']
        )

    def _calculate_attendance_metrics(
        self,
        attendance_records: List[Dict]
    ) -> Dict:
        """حساب مقاييس الحضور"""
        if not attendance_records:
            return {
                'total': 0,
                'rate': 0.0,
                'consistency': 0.0,
                'streak': 0
            }

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(attendance_records)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        total_attendance = len(df)

        # Calculate attendance rate (sessions attended / total sessions available)
        date_range = (df['date'].max() - df['date'].min()).days
        expected_sessions = date_range // 2  # افتراض: 3 حصص في الأسبوع
        attendance_rate = min(1.0, total_attendance / max(1, expected_sessions))

        # Calculate consistency (variability in attendance patterns)
        df['week'] = df['date'].dt.isocalendar().week
        weekly_attendance = df.groupby('week').size()
        consistency = 1.0 - (weekly_attendance.std() / max(1, weekly_attendance.mean()))
        consistency = max(0.0, min(1.0, consistency))

        # Calculate current streak
        streak = self._calculate_streak(df['date'].tolist())

        return {
            'total': total_attendance,
            'rate': attendance_rate,
            'consistency': consistency,
            'streak': streak
        }

    def _calculate_streak(self, dates: List[datetime]) -> int:
        """حساب سلسلة الحضور الحالية"""
        if not dates:
            return 0

        dates = sorted(dates, reverse=True)
        streak = 1

        for i in range(len(dates) - 1):
            days_diff = (dates[i] - dates[i+1]).days
            if days_diff <= 7:  # في نفس الأسبوع
                streak += 1
            else:
                break

        return streak

    def _calculate_performance_metrics(
        self,
        score_records: List[Dict]
    ) -> Dict:
        """حساب مقاييس الأداء"""
        if not score_records:
            return {
                'average': 0.0,
                'best': 0.0,
                'improvement_rate': 0.0,
                'mastery': 0.0
            }

        scores = [r['total_score'] for r in score_records if 'total_score' in r]

        if not scores:
            return {
                'average': 0.0,
                'best': 0.0,
                'improvement_rate': 0.0,
                'mastery': 0.0
            }

        average_score = np.mean(scores)
        best_score = max(scores)

        # Calculate improvement rate
        improvement_rate = 0.0
        if len(scores) >= 2:
            # Linear regression for trend
            x = np.arange(len(scores))
            y = np.array(scores)
            slope, _ = np.polyfit(x, y, 1)
            improvement_rate = slope * 4  # per month (assuming ~4 sessions/month)

        # Skill mastery (based on consistency and level of scores)
        mastery = min(1.0, average_score / 100.0)  # Assuming max score ~100

        return {
            'average': average_score,
            'best': best_score,
            'improvement_rate': improvement_rate,
            'mastery': mastery
        }

    def _calculate_engagement_metrics(
        self,
        attendance_records: List[Dict],
        score_records: List[Dict]
    ) -> Dict:
        """حساب مقاييس المشاركة"""
        # Calculate engagement score from attendance and performance
        attendance_score = len(attendance_records) / max(1, 50)  # normalize to 50 sessions
        attendance_score = min(1.0, attendance_score)

        performance_score = 0.0
        if score_records:
            avg_score = np.mean([r.get('total_score', 0) for r in score_records])
            performance_score = min(1.0, avg_score / 100.0)

        engagement_score = (attendance_score * 0.6 + performance_score * 0.4)

        # Determine commitment level
        if engagement_score >= 0.7:
            commitment_level = 'high'
        elif engagement_score >= 0.4:
            commitment_level = 'medium'
        else:
            commitment_level = 'low'

        # Calculate dropout risk
        recent_attendance = len([r for r in attendance_records
                                if self._is_recent(r.get('date'), days=30)])
        dropout_risk = 1.0 - (recent_attendance / max(1, 12))  # Expected: 3/week
        dropout_risk = max(0.0, min(1.0, dropout_risk))

        return {
            'score': engagement_score,
            'level': commitment_level,
            'dropout_risk': dropout_risk
        }

    def _calculate_financial_metrics(
        self,
        payment_records: List[Dict]
    ) -> Dict:
        """حساب المقاييس المالية"""
        if not payment_records:
            return {
                'total': 0.0,
                'consistency': 0.0,
                'ltv': 0.0
            }

        total_paid = sum(r.get('amount', 0) for r in payment_records)

        # Payment consistency (regularity of payments)
        if len(payment_records) >= 2:
            df = pd.DataFrame(payment_records)
            df['date'] = pd.to_datetime(df['payment_date'])
            df = df.sort_values('date')

            intervals = df['date'].diff().dt.days.dropna()
            consistency = 1.0 - (intervals.std() / max(1, intervals.mean()))
            consistency = max(0.0, min(1.0, consistency))
        else:
            consistency = 0.5

        # Lifetime Value (projected)
        months_active = len(payment_records)
        avg_payment = total_paid / max(1, months_active)
        projected_lifetime = 12  # months
        ltv = avg_payment * projected_lifetime

        return {
            'total': total_paid,
            'consistency': consistency,
            'ltv': ltv
        }

    def _is_recent(self, date_str: str, days: int = 30) -> bool:
        """تحقق إذا كان التاريخ حديثاً"""
        try:
            date = pd.to_datetime(date_str)
            return (datetime.now() - date).days <= days
        except:
            return False

    def predict_future_performance(
        self,
        score_history: List[Dict],
        days_ahead: int = 30
    ) -> PredictionResult:
        """
        التنبؤ بالأداء المستقبلي

        Args:
            score_history: تاريخ الدرجات
            days_ahead: عدد الأيام للتنبؤ

        Returns:
            PredictionResult
        """
        if len(score_history) < 3:
            return PredictionResult(
                metric_name='future_score',
                current_value=0.0,
                predicted_value=0.0,
                prediction_date=datetime.now() + timedelta(days=days_ahead),
                confidence=0.0,
                factors={}
            )

        # Extract scores and dates
        scores = []
        dates = []
        for record in score_history:
            if 'total_score' in record and 'date' in record:
                scores.append(record['total_score'])
                dates.append(pd.to_datetime(record['date']))

        if len(scores) < 2:
            current_value = scores[0] if scores else 0.0
            return PredictionResult(
                metric_name='future_score',
                current_value=current_value,
                predicted_value=current_value,
                prediction_date=datetime.now() + timedelta(days=days_ahead),
                confidence=0.5,
                factors={'trend': 0.0}
            )

        # Fit polynomial trend
        df = pd.DataFrame({'date': dates, 'score': scores})
        df = df.sort_values('date')
        df['days'] = (df['date'] - df['date'].min()).dt.days

        # Polynomial regression (degree 2)
        coeffs = np.polyfit(df['days'], df['score'], deg=2)
        poly = np.poly1d(coeffs)

        # Predict future value
        future_days = df['days'].max() + days_ahead
        predicted_value = poly(future_days)

        # Calculate confidence based on R²
        residuals = df['score'] - poly(df['days'])
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((df['score'] - df['score'].mean())**2)
        r_squared = 1 - (ss_res / ss_tot)
        confidence = max(0.0, min(1.0, r_squared))

        # Calculate trend
        trend = coeffs[0]  # Linear coefficient

        current_value = df['score'].iloc[-1]

        return PredictionResult(
            metric_name='future_score',
            current_value=current_value,
            predicted_value=max(0.0, predicted_value),
            prediction_date=datetime.now() + timedelta(days=days_ahead),
            confidence=confidence,
            factors={
                'trend': trend,
                'r_squared': r_squared,
                'samples': len(scores)
            }
        )

    def analyze_skill_progression(
        self,
        skill_records: List[Dict],
        target_level: float = 10.0
    ) -> List[SkillProgression]:
        """
        تحليل تطور المهارات

        Args:
            skill_records: سجلات المهارات
            target_level: المستوى المستهدف

        Returns:
            قائمة SkillProgression
        """
        if not skill_records:
            return []

        # Group by skill
        skills_by_name = defaultdict(list)
        for record in skill_records:
            skill_name = record.get('skill_name')
            if skill_name:
                skills_by_name[skill_name].append(record)

        progressions = []

        for skill_name, records in skills_by_name.items():
            # Sort by date
            records = sorted(records, key=lambda x: x.get('date', ''))

            # Get current level
            current_level = records[-1].get('level', 0.0)

            # Calculate progress rate
            if len(records) >= 2:
                first_level = records[0].get('level', 0.0)
                days_elapsed = (
                    pd.to_datetime(records[-1].get('date')) -
                    pd.to_datetime(records[0].get('date'))
                ).days

                if days_elapsed > 0:
                    progress_rate = (current_level - first_level) / days_elapsed * 7  # per week
                else:
                    progress_rate = 0.0
            else:
                progress_rate = 0.0

            # Estimate time to target
            if progress_rate > 0:
                days_to_target = int((target_level - current_level) / progress_rate * 7)
            else:
                days_to_target = 999

            # Confidence based on number of data points
            confidence = min(1.0, len(records) / 10.0)

            progressions.append(SkillProgression(
                skill_name=skill_name,
                skill_category=records[0].get('category', 'unknown'),
                current_level=current_level,
                target_level=target_level,
                progress_rate=progress_rate,
                estimated_time_to_target=days_to_target,
                confidence=confidence
            ))

        return progressions

    def calculate_peer_comparison(
        self,
        player_metrics: PerformanceMetrics,
        all_players_metrics: List[PerformanceMetrics]
    ) -> Dict:
        """
        مقارنة مع الأقران

        Args:
            player_metrics: مقاييس اللاعب
            all_players_metrics: مقاييس جميع اللاعبين

        Returns:
            نتائج المقارنة
        """
        if not all_players_metrics:
            return {
                'percentile': 50,
                'rank': 1,
                'total_players': 1,
                'better_than': 0.5
            }

        # Calculate percentiles for different metrics
        scores = [p.average_score for p in all_players_metrics]
        player_score = player_metrics.average_score

        # Percentile ranking
        better_than = sum(1 for s in scores if player_score > s) / len(scores)
        percentile = int(better_than * 100)

        # Absolute rank
        sorted_players = sorted(
            all_players_metrics,
            key=lambda x: x.average_score,
            reverse=True
        )
        rank = next(
            (i+1 for i, p in enumerate(sorted_players)
             if p.player_id == player_metrics.player_id),
            len(sorted_players)
        )

        return {
            'percentile': percentile,
            'rank': rank,
            'total_players': len(all_players_metrics),
            'better_than': better_than,
            'avg_score_comparison': {
                'player': player_score,
                'average': np.mean(scores),
                'top_10_percent': np.percentile(scores, 90)
            }
        }

    def generate_insights(
        self,
        metrics: PerformanceMetrics,
        peer_comparison: Dict
    ) -> List[str]:
        """
        توليد رؤى وتوصيات ذكية

        Args:
            metrics: مقاييس الأداء
            peer_comparison: مقارنة مع الأقران

        Returns:
            قائمة الرؤى
        """
        insights = []

        # Attendance insights
        if metrics.attendance_rate >= 0.8:
            insights.append(f"🌟 ممتاز! معدل حضور عالي ({metrics.attendance_rate:.0%})")
        elif metrics.attendance_rate < 0.5:
            insights.append(f"⚠️ معدل الحضور منخفض ({metrics.attendance_rate:.0%}) - يُنصح بالانتظام أكثر")

        # Performance insights
        if metrics.improvement_rate > 2.0:
            insights.append(f"📈 تحسن ملحوظ! معدل التحسن {metrics.improvement_rate:.1f} نقطة شهرياً")
        elif metrics.improvement_rate < 0:
            insights.append(f"📉 تراجع في الأداء - يُنصح بمراجعة خطة التدريب")

        # Engagement insights
        if metrics.risk_of_dropout > 0.6:
            insights.append(f"🚨 خطر انسحاب عالي ({metrics.risk_of_dropout:.0%}) - يحتاج متابعة")

        # Peer comparison insights
        if peer_comparison['percentile'] >= 75:
            insights.append(f"🏆 من أفضل {100-peer_comparison['percentile']}% من اللاعبين!")
        elif peer_comparison['percentile'] < 25:
            insights.append(f"💪 هناك مجال للتحسين - حالياً في أدنى 25% من اللاعبين")

        # Consistency insights
        if metrics.consistency_score >= 0.8:
            insights.append(f"✅ انتظام ممتاز في الحضور")

        return insights


def create_performance_heatmap_data(
    attendance_records: List[Dict]
) -> Dict:
    """
    إنشاء بيانات Heatmap للحضور

    Args:
        attendance_records: سجلات الحضور

    Returns:
        بيانات جاهزة للعرض في heatmap
    """
    if not attendance_records:
        return {'dates': [], 'values': [], 'weekdays': []}

    df = pd.DataFrame(attendance_records)
    df['date'] = pd.to_datetime(df['date'])
    df['weekday'] = df['date'].dt.day_name()
    df['week'] = df['date'].dt.isocalendar().week

    # Count attendance per day
    heatmap_data = df.groupby(['week', 'weekday']).size().reset_index(name='count')

    return {
        'weeks': heatmap_data['week'].tolist(),
        'weekdays': heatmap_data['weekday'].tolist(),
        'values': heatmap_data['count'].tolist()
    }
