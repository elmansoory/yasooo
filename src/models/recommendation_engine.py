"""
محرك التوصيات الذكي - AI Recommendation Engine
يوفر توصيات مخصصة لكل لاعب بناءً على أدائه وأهدافه
"""
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Recommendation:
    """توصية واحدة"""
    title: str
    description: str
    category: str  # training, schedule, skill, financial
    priority: str  # high, medium, low
    impact_score: float  # 0-1
    confidence: float  # 0-1
    action_items: List[str]
    expected_benefit: str


class RecommendationEngine:
    """محرك التوصيات الذكي"""

    def __init__(self):
        self.recommendation_rules = self._initialize_rules()

    def _initialize_rules(self) -> Dict:
        """تهيئة قواعد التوصيات"""
        return {
            'attendance': {
                'low_attendance': {
                    'threshold': 0.5,
                    'priority': 'high',
                    'impact': 0.9
                },
                'inconsistent': {
                    'threshold': 0.6,
                    'priority': 'medium',
                    'impact': 0.7
                }
            },
            'performance': {
                'declining': {
                    'threshold': -1.0,  # negative improvement rate
                    'priority': 'high',
                    'impact': 0.95
                },
                'plateau': {
                    'threshold': 0.5,
                    'priority': 'medium',
                    'impact': 0.7
                }
            },
            'skills': {
                'gap_detected': {
                    'threshold': 0.3,  # skill level difference
                    'priority': 'medium',
                    'impact': 0.8
                }
            },
            'engagement': {
                'dropout_risk': {
                    'threshold': 0.6,
                    'priority': 'high',
                    'impact': 0.95
                }
            }
        }

    def generate_recommendations(
        self,
        player_metrics: 'PerformanceMetrics',
        skill_data: Optional[List[Dict]] = None,
        schedule_data: Optional[List[Dict]] = None,
        peer_comparison: Optional[Dict] = None
    ) -> List[Recommendation]:
        """
        توليد توصيات شاملة للاعب

        Args:
            player_metrics: مقاييس أداء اللاعب
            skill_data: بيانات المهارات
            schedule_data: بيانات الجدول
            peer_comparison: مقارنة مع الأقران

        Returns:
            قائمة التوصيات
        """
        recommendations = []

        # Attendance-based recommendations
        recommendations.extend(
            self._generate_attendance_recommendations(player_metrics)
        )

        # Performance-based recommendations
        recommendations.extend(
            self._generate_performance_recommendations(player_metrics, peer_comparison)
        )

        # Skill-based recommendations
        if skill_data:
            recommendations.extend(
                self._generate_skill_recommendations(skill_data)
            )

        # Schedule optimization recommendations
        if schedule_data:
            recommendations.extend(
                self._generate_schedule_recommendations(player_metrics, schedule_data)
            )

        # Engagement recommendations
        recommendations.extend(
            self._generate_engagement_recommendations(player_metrics)
        )

        # Financial recommendations
        recommendations.extend(
            self._generate_financial_recommendations(player_metrics)
        )

        # Sort by priority and impact
        recommendations.sort(
            key=lambda x: (
                {'high': 0, 'medium': 1, 'low': 2}[x.priority],
                -x.impact_score
            )
        )

        return recommendations

    def _generate_attendance_recommendations(
        self,
        metrics: 'PerformanceMetrics'
    ) -> List[Recommendation]:
        """توصيات متعلقة بالحضور"""
        recommendations = []

        # Low attendance
        if metrics.attendance_rate < 0.5:
            recommendations.append(Recommendation(
                title="⚠️ معدل حضور منخفض",
                description=f"معدل الحضور الحالي ({metrics.attendance_rate:.0%}) أقل من المستوى المطلوب",
                category="attendance",
                priority="high",
                impact_score=0.9,
                confidence=0.95,
                action_items=[
                    "زيادة عدد الحصص الأسبوعية إلى 3-4 حصص",
                    "تحديد أوقات ثابتة للتدريب في الجدول",
                    "التواصل مع ولي الأمر لضمان الالتزام"
                ],
                expected_benefit="تحسين معدل الحضور بنسبة 30-40% خلال شهر"
            ))

        # Inconsistent attendance
        elif metrics.consistency_score < 0.6:
            recommendations.append(Recommendation(
                title="📊 عدم انتظام في الحضور",
                description=f"نمط الحضور غير منتظم (درجة الانتظام: {metrics.consistency_score:.0%})",
                category="attendance",
                priority="medium",
                impact_score=0.7,
                confidence=0.85,
                action_items=[
                    "إنشاء جدول تدريب ثابت",
                    "استخدام تذكيرات قبل الحصص",
                    "مراجعة الأوقات المناسبة مع الأسرة"
                ],
                expected_benefit="تحسين الانتظام بنسبة 25% خلال 3 أسابيع"
            ))

        # Good attendance - positive reinforcement
        elif metrics.attendance_rate >= 0.8:
            recommendations.append(Recommendation(
                title="🌟 معدل حضور ممتاز!",
                description=f"معدل حضور رائع ({metrics.attendance_rate:.0%}) - استمر على هذا المستوى",
                category="attendance",
                priority="low",
                impact_score=0.4,
                confidence=1.0,
                action_items=[
                    "الحفاظ على نفس الوتيرة",
                    "مكافأة الالتزام المستمر",
                    "مشاركة الإنجاز مع الزملاء"
                ],
                expected_benefit="الحفاظ على معدل الحضور العالي"
            ))

        return recommendations

    def _generate_performance_recommendations(
        self,
        metrics: 'PerformanceMetrics',
        peer_comparison: Optional[Dict] = None
    ) -> List[Recommendation]:
        """توصيات متعلقة بالأداء"""
        recommendations = []

        # Declining performance
        if metrics.improvement_rate < -1.0:
            recommendations.append(Recommendation(
                title="📉 تراجع في الأداء",
                description=f"انخفاض في مستوى الأداء بمعدل {abs(metrics.improvement_rate):.1f} نقطة شهرياً",
                category="performance",
                priority="high",
                impact_score=0.95,
                confidence=0.9,
                action_items=[
                    "مراجعة فورية مع المدرب الرئيسي",
                    "تحليل الحصص الأخيرة لتحديد نقاط الضعف",
                    "زيادة التركيز على التدريب الأساسي",
                    "النظر في تعديل خطة التدريب"
                ],
                expected_benefit="إيقاف التراجع خلال 2-3 أسابيع والبدء في التحسن"
            ))

        # Performance plateau
        elif 0 <= metrics.improvement_rate < 0.5:
            recommendations.append(Recommendation(
                title="⏸️ ثبات في مستوى الأداء",
                description="لا يوجد تحسن ملحوظ في الأداء خلال الفترة الأخيرة",
                category="performance",
                priority="medium",
                impact_score=0.75,
                confidence=0.8,
                action_items=[
                    "تجربة تقنيات تدريب جديدة",
                    "إضافة تحديات جديدة للبرنامج",
                    "العمل على عناصر أكثر تعقيداً",
                    "زيادة كثافة التدريب تدريجياً"
                ],
                expected_benefit="كسر حاجز الثبات والبدء في التحسن خلال 4 أسابيع"
            ))

        # Great improvement
        elif metrics.improvement_rate > 2.0:
            recommendations.append(Recommendation(
                title="🚀 تحسن ممتاز!",
                description=f"تقدم رائع بمعدل {metrics.improvement_rate:.1f} نقطة شهرياً",
                category="performance",
                priority="low",
                impact_score=0.5,
                confidence=0.95,
                action_items=[
                    "الحفاظ على نفس وتيرة التدريب",
                    "البدء في إضافة عناصر أكثر تقدماً",
                    "المشاركة في منافسات محلية للتحفيز"
                ],
                expected_benefit="الاستمرار في التحسن والوصول لمستويات أعلى"
            ))

        # Below peer average
        if peer_comparison and peer_comparison.get('percentile', 50) < 25:
            recommendations.append(Recommendation(
                title="💪 فرصة للتحسن",
                description=f"الأداء الحالي في أدنى 25% من الأقران - هناك مجال كبير للتحسن",
                category="performance",
                priority="medium",
                impact_score=0.8,
                confidence=0.85,
                action_items=[
                    "تحديد نقاط الضعف الرئيسية",
                    "زيادة عدد ساعات التدريب",
                    "التدريب مع لاعبين أفضل للتعلم منهم",
                    "التركيز على العناصر الأساسية"
                ],
                expected_benefit="الوصول للمتوسط خلال 2-3 أشهر مع التدريب المناسب"
            ))

        return recommendations

    def _generate_skill_recommendations(
        self,
        skill_data: List[Dict]
    ) -> List[Recommendation]:
        """توصيات متعلقة بالمهارات"""
        recommendations = []

        if not skill_data:
            return recommendations

        # Find skill gaps
        skill_levels = {s['skill_name']: s.get('level', 0) for s in skill_data}

        if skill_levels:
            avg_level = np.mean(list(skill_levels.values()))
            weak_skills = [
                name for name, level in skill_levels.items()
                if level < avg_level - 2
            ]

            if weak_skills:
                recommendations.append(Recommendation(
                    title="🎯 فجوات في المهارات",
                    description=f"بعض المهارات تحتاج تطوير: {', '.join(weak_skills[:3])}",
                    category="skill",
                    priority="medium",
                    impact_score=0.8,
                    confidence=0.85,
                    action_items=[
                        f"التركيز على {weak_skills[0]} في الحصص القادمة",
                        "تخصيص 20-30% من وقت التدريب للمهارات الضعيفة",
                        "مشاهدة فيديوهات تعليمية متخصصة",
                        "طلب جلسات إضافية مع المدرب"
                    ],
                    expected_benefit="تحسين المهارات الضعيفة بنسبة 40% خلال شهرين"
                ))

        return recommendations

    def _generate_schedule_recommendations(
        self,
        metrics: 'PerformanceMetrics',
        schedule_data: List[Dict]
    ) -> List[Recommendation]:
        """توصيات متعلقة بالجدول"""
        recommendations = []

        # If attendance is low, suggest schedule optimization
        if metrics.attendance_rate < 0.6:
            recommendations.append(Recommendation(
                title="📅 تحسين الجدول الزمني",
                description="قد يكون الجدول الحالي غير مناسب - يُنصح بتعديله",
                category="schedule",
                priority="medium",
                impact_score=0.7,
                confidence=0.75,
                action_items=[
                    "مراجعة الأوقات المتاحة مع الأسرة",
                    "تجربة أوقات تدريب مختلفة",
                    "النظر في الحصص المسائية/الصباحية",
                    "اختيار أيام أكثر ملاءمة للأسرة"
                ],
                expected_benefit="زيادة معدل الحضور بنسبة 20-30%"
            ))

        return recommendations

    def _generate_engagement_recommendations(
        self,
        metrics: 'PerformanceMetrics'
    ) -> List[Recommendation]:
        """توصيات متعلقة بالمشاركة"""
        recommendations = []

        # High dropout risk
        if metrics.risk_of_dropout > 0.6:
            recommendations.append(Recommendation(
                title="🚨 خطر انسحاب - تدخل فوري مطلوب",
                description=f"احتمالية انسحاب عالية ({metrics.risk_of_dropout:.0%})",
                category="engagement",
                priority="high",
                impact_score=0.95,
                confidence=0.9,
                action_items=[
                    "اجتماع عاجل مع ولي الأمر واللاعب",
                    "فهم أسباب قلة الحضور أو الاهتمام",
                    "تقديم حوافز أو خصومات مؤقتة",
                    "ربط اللاعب بمجموعة أصدقاء في النادي",
                    "إعادة تقييم الأهداف والتوقعات"
                ],
                expected_benefit="تقليل احتمالية الانسحاب بنسبة 50%"
            ))

        # Low engagement
        elif metrics.engagement_score < 0.4:
            recommendations.append(Recommendation(
                title="📊 مستوى مشاركة منخفض",
                description=f"درجة المشاركة ({metrics.engagement_score:.0%}) تحتاج تحسين",
                category="engagement",
                priority="medium",
                impact_score=0.8,
                confidence=0.85,
                action_items=[
                    "إضافة أنشطة ترفيهية للتدريب",
                    "تنظيم منافسات ودية بين اللاعبين",
                    "تحديد أهداف قصيرة المدى قابلة للتحقيق",
                    "مكافأة التقدم والإنجازات الصغيرة"
                ],
                expected_benefit="زيادة المشاركة بنسبة 30% خلال شهر"
            ))

        return recommendations

    def _generate_financial_recommendations(
        self,
        metrics: 'PerformanceMetrics'
    ) -> List[Recommendation]:
        """توصيات متعلقة بالجانب المالي"""
        recommendations = []

        # Low payment consistency
        if metrics.payment_consistency < 0.5:
            recommendations.append(Recommendation(
                title="💳 عدم انتظام في المدفوعات",
                description="أنماط الدفع غير منتظمة - يُنصح بنظام دفع أوتوماتيكي",
                category="financial",
                priority="low",
                impact_score=0.6,
                confidence=0.8,
                action_items=[
                    "اقتراح نظام دفع شهري ثابت",
                    "توفير خصم للدفع المسبق",
                    "إرسال تذكيرات قبل موعد الدفع",
                    "تسهيل طرق الدفع الإلكتروني"
                ],
                expected_benefit="تحسين انتظام المدفوعات وتقليل التأخير"
            ))

        # High value player
        if metrics.lifetime_value > 10000:
            recommendations.append(Recommendation(
                title="⭐ عميل مميز - VIP",
                description=f"قيمة عميل عالية ({metrics.lifetime_value:.0f} جنيه)",
                category="financial",
                priority="low",
                impact_score=0.5,
                confidence=1.0,
                action_items=[
                    "تقديم خدمات VIP إضافية",
                    "أولوية في الجدول والحجوزات",
                    "خصومات خاصة على البرامج المتقدمة",
                    "دعوة لفعاليات خاصة"
                ],
                expected_benefit="زيادة الولاء والاحتفاظ بالعميل"
            ))

        return recommendations

    def generate_training_plan(
        self,
        player_metrics: 'PerformanceMetrics',
        skill_data: Optional[List[Dict]] = None,
        goals: Optional[List[str]] = None
    ) -> Dict:
        """
        توليد خطة تدريب مخصصة

        Args:
            player_metrics: مقاييس اللاعب
            skill_data: بيانات المهارات
            goals: أهداف اللاعب

        Returns:
            خطة تدريب مفصلة
        """
        plan = {
            'player_name': player_metrics.player_name,
            'generated_date': datetime.now().isoformat(),
            'duration_weeks': 12,
            'focus_areas': [],
            'weekly_schedule': {},
            'milestones': [],
            'success_metrics': []
        }

        # Determine focus areas based on metrics
        if player_metrics.skill_mastery < 0.5:
            plan['focus_areas'].append({
                'area': 'Basic Skills',
                'priority': 'high',
                'allocation': '40%'
            })

        if player_metrics.improvement_rate < 1.0:
            plan['focus_areas'].append({
                'area': 'Technique Refinement',
                'priority': 'high',
                'allocation': '30%'
            })

        if player_metrics.consistency_score < 0.7:
            plan['focus_areas'].append({
                'area': 'Consistency Training',
                'priority': 'medium',
                'allocation': '20%'
            })

        # Weekly schedule suggestions
        sessions_per_week = max(2, int(player_metrics.attendance_rate * 5))

        plan['weekly_schedule'] = {
            'recommended_sessions': sessions_per_week,
            'session_duration': '60-90 minutes',
            'suggested_days': ['Monday', 'Wednesday', 'Friday'][:sessions_per_week]
        }

        # Milestones
        current_score = player_metrics.average_score
        for week in [4, 8, 12]:
            target_improvement = (week / 4) * 5  # 5 points per month
            plan['milestones'].append({
                'week': week,
                'target_score': current_score + target_improvement,
                'description': f'تحسن بمقدار {target_improvement:.1f} نقطة'
            })

        # Success metrics
        plan['success_metrics'] = [
            {
                'metric': 'Attendance Rate',
                'target': 'حضور 85%+ من الحصص',
                'current': f"{player_metrics.attendance_rate:.0%}"
            },
            {
                'metric': 'Average Score',
                'target': f'الوصول إلى {current_score + 10:.1f} نقطة',
                'current': f"{current_score:.1f}"
            },
            {
                'metric': 'Consistency',
                'target': 'تحسين الانتظام إلى 80%+',
                'current': f"{player_metrics.consistency_score:.0%}"
            }
        ]

        return plan
