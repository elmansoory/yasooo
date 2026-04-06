"""
نظام مقارنة الأداء
Performance Comparison System
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta


@dataclass
class PlayerStats:
    """إحصائيات لاعب"""
    member_id: int
    name: str
    total_attendance: int
    attendance_rate: float
    avg_weekly_attendance: float
    current_streak: int
    longest_streak: int
    level: str
    points: int
    badges_count: int
    rank: Optional[int] = None


class PerformanceComparator:
    """محلل مقارنة الأداء"""

    def __init__(self):
        self.stats_cache = {}

    def calculate_player_stats(
        self,
        member_id: int,
        member_name: str,
        attendance_df: pd.DataFrame,
        progression_summary: Optional[Dict] = None
    ) -> PlayerStats:
        """حساب إحصائيات اللاعب"""

        member_attendance = attendance_df[attendance_df['member_id'] == member_id]

        # الإحصائيات الأساسية
        total_attendance = len(member_attendance)

        # معدل الحضور
        if 'date' in attendance_df.columns:
            total_days = attendance_df['date'].nunique()
            attendance_rate = (total_attendance / total_days * 100) if total_days > 0 else 0
        else:
            attendance_rate = 0

        # متوسط الحضور الأسبوعي
        if 'date' in member_attendance.columns and not member_attendance.empty:
            dates = pd.to_datetime(member_attendance['date'])
            weeks = (dates.max() - dates.min()).days / 7
            avg_weekly = total_attendance / weeks if weeks > 0 else 0
        else:
            avg_weekly = 0

        # حساب Streak
        current_streak, longest_streak = self._calculate_streaks(member_attendance)

        # بيانات التقدم
        if progression_summary:
            level = progression_summary.get('level_name', 'مبتدئ')
            points = progression_summary.get('points', 0)
            badges_count = progression_summary.get('badges_count', 0)
        else:
            level = 'مبتدئ'
            points = total_attendance * 10
            badges_count = 0

        return PlayerStats(
            member_id=member_id,
            name=member_name,
            total_attendance=total_attendance,
            attendance_rate=attendance_rate,
            avg_weekly_attendance=avg_weekly,
            current_streak=current_streak,
            longest_streak=longest_streak,
            level=level,
            points=points,
            badges_count=badges_count
        )

    def _calculate_streaks(self, attendance_df: pd.DataFrame) -> Tuple[int, int]:
        """حساب السلاسل (Streaks)"""
        if 'date' not in attendance_df.columns or attendance_df.empty:
            return 0, 0

        dates = pd.to_datetime(attendance_df['date']).sort_values()
        dates = dates.drop_duplicates()

        current_streak = 0
        longest_streak = 0
        temp_streak = 1

        for i in range(1, len(dates)):
            diff = (dates.iloc[i] - dates.iloc[i-1]).days

            if diff == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1

        # حساب Current Streak
        today = datetime.now()
        if not dates.empty:
            last_date = dates.iloc[-1]
            days_since_last = (today - last_date).days

            if days_since_last <= 1:
                # آخر حضور اليوم أو أمس
                for i in range(len(dates) - 1, -1, -1):
                    if i == 0:
                        current_streak += 1
                        break

                    diff = (dates.iloc[i] - dates.iloc[i-1]).days
                    if diff == 1:
                        current_streak += 1
                    else:
                        break

        return current_streak, longest_streak

    def compare_players(
        self,
        player_ids: List[int],
        members_df: pd.DataFrame,
        attendance_df: pd.DataFrame,
        progression_summaries: Optional[Dict[int, Dict]] = None
    ) -> Dict:
        """مقارنة بين عدة لاعبين"""

        if progression_summaries is None:
            progression_summaries = {}

        players_stats = []

        for player_id in player_ids:
            member = members_df[members_df['id'] == player_id]

            if member.empty:
                continue

            member_name = member.iloc[0]['name']
            progression = progression_summaries.get(player_id)

            stats = self.calculate_player_stats(
                player_id,
                member_name,
                attendance_df,
                progression
            )

            players_stats.append(stats)

        # ترتيب حسب النقاط
        players_stats.sort(key=lambda x: x.points, reverse=True)

        # إضافة الترتيب
        for rank, stats in enumerate(players_stats, 1):
            stats.rank = rank

        return {
            'players': players_stats,
            'comparison_metrics': self._calculate_comparison_metrics(players_stats),
            'insights': self._generate_insights(players_stats)
        }

    def _calculate_comparison_metrics(self, players_stats: List[PlayerStats]) -> Dict:
        """حساب مقاييس المقارنة"""
        if not players_stats:
            return {}

        return {
            'avg_attendance': np.mean([p.total_attendance for p in players_stats]),
            'avg_points': np.mean([p.points for p in players_stats]),
            'avg_badges': np.mean([p.badges_count for p in players_stats]),
            'max_attendance': max([p.total_attendance for p in players_stats]),
            'min_attendance': min([p.total_attendance for p in players_stats]),
            'max_streak': max([p.longest_streak for p in players_stats])
        }

    def _generate_insights(self, players_stats: List[PlayerStats]) -> List[str]:
        """توليد رؤى من المقارنة"""
        insights = []

        if not players_stats:
            return insights

        # أفضل لاعب
        best_player = players_stats[0]
        insights.append(f"🏆 {best_player.name} هو الأفضل بـ {best_player.points} نقطة")

        # أعلى معدل حضور
        best_attendance = max(players_stats, key=lambda x: x.attendance_rate)
        insights.append(f"📊 {best_attendance.name} لديه أعلى معدل حضور: {best_attendance.attendance_rate:.1f}%")

        # أطول سلسلة
        longest_streak_player = max(players_stats, key=lambda x: x.longest_streak)
        if longest_streak_player.longest_streak > 0:
            insights.append(f"🔥 {longest_streak_player.name} لديه أطول سلسلة: {longest_streak_player.longest_streak} يوم")

        # أكثر الشارات
        most_badges = max(players_stats, key=lambda x: x.badges_count)
        if most_badges.badges_count > 0:
            insights.append(f"🏅 {most_badges.name} حصل على أكثر الشارات: {most_badges.badges_count}")

        return insights

    def create_comparison_charts(
        self,
        players_stats: List[PlayerStats]
    ) -> Dict[str, go.Figure]:
        """إنشاء رسوم بيانية للمقارنة"""

        charts = {}

        # 1. مقارنة النقاط
        fig_points = go.Figure()

        fig_points.add_trace(go.Bar(
            x=[p.name for p in players_stats],
            y=[p.points for p in players_stats],
            marker_color='#667eea',
            text=[p.points for p in players_stats],
            textposition='auto',
        ))

        fig_points.update_layout(
            title="مقارنة النقاط",
            xaxis_title="اللاعب",
            yaxis_title="النقاط",
            plot_bgcolor='white',
            height=400
        )

        charts['points'] = fig_points

        # 2. مقارنة الحضور
        fig_attendance = go.Figure()

        fig_attendance.add_trace(go.Bar(
            x=[p.name for p in players_stats],
            y=[p.total_attendance for p in players_stats],
            marker_color='#764ba2',
            text=[p.total_attendance for p in players_stats],
            textposition='auto',
        ))

        fig_attendance.update_layout(
            title="مقارنة الحضور",
            xaxis_title="اللاعب",
            yaxis_title="عدد أيام الحضور",
            plot_bgcolor='white',
            height=400
        )

        charts['attendance'] = fig_attendance

        # 3. Radar Chart للمقاييس المختلفة
        categories = ['الحضور', 'النقاط', 'الشارات', 'أطول سلسلة', 'المستوى']

        fig_radar = go.Figure()

        for player in players_stats:
            # تطبيع القيم (0-100)
            max_attendance = max([p.total_attendance for p in players_stats])
            max_points = max([p.points for p in players_stats])
            max_badges = max([p.badges_count for p in players_stats]) or 1
            max_streak = max([p.longest_streak for p in players_stats]) or 1

            values = [
                (player.total_attendance / max_attendance * 100) if max_attendance > 0 else 0,
                (player.points / max_points * 100) if max_points > 0 else 0,
                (player.badges_count / max_badges * 100),
                (player.longest_streak / max_streak * 100),
                50  # placeholder for level
            ]

            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=player.name
            ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="مقارنة شاملة",
            height=500
        )

        charts['radar'] = fig_radar

        # 4. معدل الحضور
        fig_rate = go.Figure()

        fig_rate.add_trace(go.Bar(
            x=[p.name for p in players_stats],
            y=[p.attendance_rate for p in players_stats],
            marker_color='#10b981',
            text=[f"{p.attendance_rate:.1f}%" for p in players_stats],
            textposition='auto',
        ))

        fig_rate.update_layout(
            title="معدل الحضور (%)",
            xaxis_title="اللاعب",
            yaxis_title="معدل الحضور",
            plot_bgcolor='white',
            height=400
        )

        charts['attendance_rate'] = fig_rate

        return charts

    def create_leaderboard(
        self,
        members_df: pd.DataFrame,
        attendance_df: pd.DataFrame,
        progression_summaries: Optional[Dict] = None,
        top_n: int = 10
    ) -> pd.DataFrame:
        """إنشاء لوحة الصدارة (Leaderboard)"""

        if progression_summaries is None:
            progression_summaries = {}

        leaderboard = []

        for _, member in members_df.iterrows():
            member_id = member['id']
            member_name = member['name']

            progression = progression_summaries.get(member_id)

            stats = self.calculate_player_stats(
                member_id,
                member_name,
                attendance_df,
                progression
            )

            leaderboard.append({
                'الاسم': stats.name,
                'النقاط': stats.points,
                'المستوى': stats.level,
                'الحضور': stats.total_attendance,
                'معدل الحضور': f"{stats.attendance_rate:.1f}%",
                'السلسلة الحالية': stats.current_streak,
                'أطول سلسلة': stats.longest_streak,
                'الشارات': stats.badges_count
            })

        # ترتيب حسب النقاط
        leaderboard_df = pd.DataFrame(leaderboard)
        leaderboard_df = leaderboard_df.sort_values('النقاط', ascending=False)
        leaderboard_df.insert(0, 'الترتيب', range(1, len(leaderboard_df) + 1))

        return leaderboard_df.head(top_n)

    def analyze_strengths_weaknesses(
        self,
        player_id: int,
        members_df: pd.DataFrame,
        attendance_df: pd.DataFrame,
        progression_summary: Optional[Dict] = None
    ) -> Dict:
        """تحليل نقاط القوة والضعف"""

        member = members_df[members_df['id'] == player_id]
        if member.empty:
            return {}

        member_name = member.iloc[0]['name']

        # حساب إحصائيات اللاعب
        player_stats = self.calculate_player_stats(
            player_id,
            member_name,
            attendance_df,
            progression_summary
        )

        # حساب المتوسطات العامة
        all_stats = []
        for _, m in members_df.iterrows():
            stats = self.calculate_player_stats(
                m['id'],
                m['name'],
                attendance_df
            )
            all_stats.append(stats)

        avg_attendance = np.mean([s.total_attendance for s in all_stats])
        avg_points = np.mean([s.points for s in all_stats])
        avg_streak = np.mean([s.longest_streak for s in all_stats])
        avg_badges = np.mean([s.badges_count for s in all_stats])

        strengths = []
        weaknesses = []
        suggestions = []

        # تحليل الحضور
        if player_stats.total_attendance > avg_attendance * 1.2:
            strengths.append({
                'metric': 'الحضور',
                'description': f'حضور ممتاز ({player_stats.total_attendance} يوم)',
                'icon': '🌟'
            })
        elif player_stats.total_attendance < avg_attendance * 0.8:
            weaknesses.append({
                'metric': 'الحضور',
                'description': f'حضور منخفض ({player_stats.total_attendance} يوم)',
                'icon': '⚠️'
            })
            suggestions.append("حاول الحضور بانتظام أكثر لتحسين أدائك")

        # تحليل النقاط
        if player_stats.points > avg_points * 1.2:
            strengths.append({
                'metric': 'النقاط',
                'description': f'نقاط عالية ({player_stats.points})',
                'icon': '💎'
            })
        elif player_stats.points < avg_points * 0.8:
            weaknesses.append({
                'metric': 'النقاط',
                'description': f'نقاط منخفضة ({player_stats.points})',
                'icon': '📉'
            })
            suggestions.append("احصل على المزيد من الشارات لزيادة نقاطك")

        # تحليل السلسلة
        if player_stats.longest_streak > avg_streak * 1.5:
            strengths.append({
                'metric': 'الالتزام',
                'description': f'التزام ممتاز ({player_stats.longest_streak} يوم متتالي)',
                'icon': '🔥'
            })
        elif player_stats.current_streak == 0:
            weaknesses.append({
                'metric': 'الانتظام',
                'description': 'لا توجد سلسلة حالية',
                'icon': '❄️'
            })
            suggestions.append("ابدأ سلسلة جديدة بالحضور المنتظم")

        # تحليل الشارات
        if player_stats.badges_count > avg_badges * 1.2:
            strengths.append({
                'metric': 'الإنجازات',
                'description': f'شارات كثيرة ({player_stats.badges_count})',
                'icon': '🏅'
            })
        elif player_stats.badges_count < avg_badges * 0.8:
            weaknesses.append({
                'metric': 'الإنجازات',
                'description': f'شارات قليلة ({player_stats.badges_count})',
                'icon': '🎯'
            })
            suggestions.append("حاول الحصول على المزيد من الشارات")

        return {
            'player_name': member_name,
            'player_stats': player_stats,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'suggestions': suggestions,
            'overall_score': self._calculate_overall_score(player_stats, all_stats)
        }

    def _calculate_overall_score(
        self,
        player_stats: PlayerStats,
        all_stats: List[PlayerStats]
    ) -> int:
        """حساب النتيجة الإجمالية (0-100)"""

        if not all_stats:
            return 50

        # حساب النسب المئوية لكل مقياس
        max_attendance = max([s.total_attendance for s in all_stats]) or 1
        max_points = max([s.points for s in all_stats]) or 1
        max_streak = max([s.longest_streak for s in all_stats]) or 1
        max_badges = max([s.badges_count for s in all_stats]) or 1

        attendance_score = (player_stats.total_attendance / max_attendance) * 30
        points_score = (player_stats.points / max_points) * 30
        streak_score = (player_stats.longest_streak / max_streak) * 20
        badges_score = (player_stats.badges_count / max_badges) * 20

        overall = attendance_score + points_score + streak_score + badges_score

        return int(min(100, overall))


# مثال على الاستخدام
if __name__ == "__main__":
    comparator = PerformanceComparator()

    # بيانات تجريبية
    members_df = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['محمد', 'أحمد', 'علي']
    })

    attendance_df = pd.DataFrame({
        'member_id': [1, 1, 1, 2, 2, 3],
        'date': pd.date_range('2025-01-01', periods=6, freq='D')
    })

    # مقارنة
    comparison = comparator.compare_players([1, 2, 3], members_df, attendance_df)

    print("المقارنة:")
    for player in comparison['players']:
        print(f"- {player.name}: {player.points} نقطة")

    print("\nالرؤى:")
    for insight in comparison['insights']:
        print(f"  {insight}")
