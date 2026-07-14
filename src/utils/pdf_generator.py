"""
نظام توليد تقارير PDF احترافية
Professional PDF Report Generator
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
import plotly.graph_objects as go
import io


class PDFReportGenerator:
    """مولد تقارير PDF احترافية"""

    def __init__(self, output_path: str, title: str = "تقرير نظام التزلج"):
        self.output_path = output_path
        self.title = title
        self.doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        self.story = []
        self.styles = self._setup_styles()

    def _setup_styles(self):
        """إعداد الأنماط"""
        styles = getSampleStyleSheet()

        # نمط العنوان الرئيسي
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # نمط العنوان الفرعي
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#764ba2'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # نمط النص العادي
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            spaceAfter=12,
            fontName='Helvetica'
        ))

        # نمط للنصوص العربية (إذا توفرت خطوط عربية)
        styles.add(ParagraphStyle(
            name='ArabicText',
            parent=styles['BodyText'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_RIGHT,
            fontName='Helvetica'
        ))

        return styles

    def add_title_page(self, subtitle: str = "", date: Optional[str] = None):
        """إضافة صفحة عنوان"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M")

        # العنوان الرئيسي
        title = Paragraph(self.title, self.styles['CustomTitle'])
        self.story.append(title)
        self.story.append(Spacer(1, 0.5*inch))

        # العنوان الفرعي
        if subtitle:
            subtitle_p = Paragraph(subtitle, self.styles['CustomHeading'])
            self.story.append(subtitle_p)
            self.story.append(Spacer(1, 0.3*inch))

        # التاريخ
        date_style = ParagraphStyle(
            'DateStyle',
            parent=self.styles['CustomBody'],
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        date_p = Paragraph(f"Generated: {date}", date_style)
        self.story.append(date_p)

        self.story.append(PageBreak())

    def add_heading(self, text: str, level: int = 2):
        """إضافة عنوان"""
        style_name = 'CustomHeading' if level == 2 else 'CustomTitle'
        heading = Paragraph(text, self.styles[style_name])
        self.story.append(heading)

    def add_paragraph(self, text: str, arabic: bool = False):
        """إضافة فقرة نصية"""
        style = self.styles['ArabicText'] if arabic else self.styles['CustomBody']
        para = Paragraph(text, style)
        self.story.append(para)
        self.story.append(Spacer(1, 0.1*inch))

    def add_table(self, data: List[List[Any]], headers: Optional[List[str]] = None,
                  col_widths: Optional[List[float]] = None):
        """إضافة جدول"""
        # إضافة الرؤوس إذا كانت موجودة
        if headers:
            table_data = [headers] + data
        else:
            table_data = data

        # إنشاء الجدول
        table = Table(table_data, colWidths=col_widths)

        # تنسيق الجدول
        table_style = TableStyle([
            # تنسيق الرأس
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # تنسيق البيانات
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),

            # حدود الجدول
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#764ba2')),

            # صفوف متبادلة اللون
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#f8fafc')])
        ])

        table.setStyle(table_style)
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))

    def add_dataframe(self, df: pd.DataFrame, max_rows: int = 50):
        """إضافة DataFrame كجدول"""
        # تحديد عدد الصفوف
        df_subset = df.head(max_rows)

        # تحويل إلى قائمة
        headers = df_subset.columns.tolist()
        data = df_subset.values.tolist()

        # إضافة الجدول
        self.add_table(data, headers=headers)

        # إضافة ملاحظة إذا كانت البيانات محدودة
        if len(df) > max_rows:
            note = f"Note: Showing {max_rows} of {len(df)} rows"
            self.add_paragraph(note)

    def add_metrics_section(self, metrics: Dict[str, Any]):
        """إضافة قسم الإحصائيات"""
        self.add_heading("Key Metrics")

        # تحويل الإحصائيات إلى جدول
        data = [[k, str(v)] for k, v in metrics.items()]
        self.add_table(data, headers=["Metric", "Value"])

    def add_chart_as_image(self, fig, width: float = 6*inch, height: float = 4*inch):
        """إضافة رسم بياني من Plotly كصورة"""
        # تحويل الرسم إلى صورة
        img_bytes = fig.to_image(format="png", width=800, height=600)
        img = Image(io.BytesIO(img_bytes), width=width, height=height)

        self.story.append(img)
        self.story.append(Spacer(1, 0.2*inch))

    def add_spacer(self, height: float = 0.2):
        """إضافة مساحة فارغة"""
        self.story.append(Spacer(1, height*inch))

    def add_page_break(self):
        """إضافة فاصل صفحة"""
        self.story.append(PageBreak())

    def build(self):
        """بناء وحفظ ملف PDF"""
        self.doc.build(self.story)
        return self.output_path


class MemberReportGenerator(PDFReportGenerator):
    """مولد تقرير خاص بعضو"""

    def generate_member_report(self, member_data: Dict[str, Any],
                               attendance_data: pd.DataFrame):
        """توليد تقرير كامل لعضو"""
        # صفحة العنوان
        self.add_title_page(
            subtitle=f"Member Report: {member_data.get('name', 'Unknown')}",
            date=datetime.now().strftime("%Y-%m-%d")
        )

        # معلومات العضو
        self.add_heading("Member Information")

        member_info = [
            ["Name", member_data.get('name', 'N/A')],
            ["Gender", member_data.get('gender', 'N/A')],
            ["Birth Date", str(member_data.get('birth_date', 'N/A'))],
            ["Member ID", str(member_data.get('id', 'N/A'))]
        ]

        self.add_table(member_info, col_widths=[2*inch, 4*inch])

        # إحصائيات الحضور
        self.add_heading("Attendance Statistics")

        if not attendance_data.empty:
            stats = {
                "Total Attendance": len(attendance_data),
                "First Attendance": attendance_data['date'].min(),
                "Last Attendance": attendance_data['date'].max(),
                "Unique Dates": attendance_data['date'].nunique()
            }

            self.add_metrics_section(stats)

            # جدول الحضور
            self.add_heading("Attendance History", level=3)
            self.add_dataframe(attendance_data[['date']].sort_values('date', ascending=False))

        # بناء التقرير
        return self.build()


class SystemReportGenerator(PDFReportGenerator):
    """مولد تقرير النظام الشامل"""

    def generate_system_report(self, members_df: pd.DataFrame,
                               attendance_df: pd.DataFrame,
                               memberships_df: pd.DataFrame):
        """توليد تقرير شامل للنظام"""
        # صفحة العنوان
        self.add_title_page(
            subtitle="Comprehensive System Report",
            date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        # نظرة عامة
        self.add_heading("System Overview")

        overview = {
            "Total Members": len(members_df),
            "Total Attendance Records": len(attendance_df),
            "Total Memberships": len(memberships_df),
            "Unique Training Days": attendance_df['date'].nunique() if 'date' in attendance_df.columns else 0,
            "Average Attendance": f"{len(attendance_df) / len(members_df):.2f}" if len(members_df) > 0 else "0"
        }

        self.add_metrics_section(overview)

        # توزيع الأعضاء
        self.add_page_break()
        self.add_heading("Members Distribution")

        if 'gender' in members_df.columns:
            gender_dist = members_df['gender'].value_counts()
            gender_data = [[gender, count] for gender, count in gender_dist.items()]
            self.add_table(gender_data, headers=["Gender", "Count"])

        # أفضل 20 عضو
        self.add_page_break()
        self.add_heading("Top 20 Members by Attendance")

        if 'member_id' in attendance_df.columns:
            top_members = attendance_df['member_id'].value_counts().head(20)
            top_data = []

            for member_id, count in top_members.items():
                member_info = members_df[members_df['id'] == member_id]
                if not member_info.empty:
                    name = member_info.iloc[0]['name']
                    top_data.append([name, count])

            self.add_table(top_data, headers=["Member Name", "Attendance Count"])

        # إحصائيات شهرية
        self.add_page_break()
        self.add_heading("Monthly Attendance Statistics")

        if 'date' in attendance_df.columns:
            attendance_df['month'] = pd.to_datetime(attendance_df['date']).dt.to_period('M')
            monthly = attendance_df.groupby('month').size().reset_index(name='count')
            monthly['month'] = monthly['month'].astype(str)

            monthly_data = monthly.values.tolist()
            self.add_table(monthly_data, headers=["Month", "Attendance Count"])

        # بناء التقرير
        return self.build()


# دوال مساعدة
def generate_member_pdf(member_data: Dict, attendance_data: pd.DataFrame,
                       output_path: str) -> str:
    """توليد تقرير PDF لعضو"""
    generator = MemberReportGenerator(output_path, "Skating Member Report")
    return generator.generate_member_report(member_data, attendance_data)


def generate_system_pdf(members_df: pd.DataFrame, attendance_df: pd.DataFrame,
                       memberships_df: pd.DataFrame, output_path: str) -> str:
    """توليد تقرير PDF للنظام"""
    generator = SystemReportGenerator(output_path, "Skating System Report")
    return generator.generate_system_report(members_df, attendance_df, memberships_df)


if __name__ == "__main__":
    # اختبار التقرير
    print("PDF Report Generator - Ready!")
