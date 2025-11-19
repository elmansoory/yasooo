"""
محرك التسجيل وفق معايير ISU
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from src.config.isu_standards import ISUStandards
from src.utils.logger import LoggerMixin


@dataclass
class ElementScore:
    """درجة عنصر واحد"""
    element_code: str
    element_name: str
    base_value: float
    goe: int
    goe_value: float
    total_score: float
    errors: List[str] = None


@dataclass
class ProgramScore:
    """الدرجة الكاملة للبرنامج"""
    # Technical Elements
    total_base_value: float
    total_goe: float
    technical_score: float

    # Program Components
    skating_skills: float
    transitions: float
    performance: float
    composition: float
    interpretation: float
    program_components_score: float

    # Final
    total_deductions: float
    total_score: float

    # Details
    elements: List[ElementScore]
    deductions: Dict[str, float]


class ScoringEngine(LoggerMixin):
    """محرك التسجيل الرئيسي"""

    def __init__(self):
        self.standards = ISUStandards()

    def calculate_element_score(
        self,
        element_code: str,
        goe: int,
        errors: List[str] = None
    ) -> Optional[ElementScore]:
        """
        حساب درجة عنصر واحد

        Args:
            element_code: رمز العنصر (مثل 3A, CCSp4)
            goe: درجة جودة التنفيذ (-5 إلى +5)
            errors: قائمة الأخطاء المكتشفة

        Returns:
            ElementScore أو None
        """
        # الحصول على معلومات العنصر
        element_info = self.standards.get_element_info(element_code)

        if not element_info:
            self.logger.warning(f"عنصر غير معروف: {element_code}")
            return None

        # الحصول على القيمة الأساسية
        base_value = element_info.get('base_value', 0.0)

        # حساب قيمة GOE
        goe_value = self.standards.calculate_goe_value(base_value, goe)

        # الدرجة الإجمالية للعنصر
        total_score = base_value + goe_value

        return ElementScore(
            element_code=element_code,
            element_name=element_info.get('name', element_code),
            base_value=base_value,
            goe=goe,
            goe_value=goe_value,
            total_score=total_score,
            errors=errors or []
        )

    def calculate_technical_score(
        self,
        elements: List[Dict[str, Any]]
    ) -> tuple[float, float, float, List[ElementScore]]:
        """
        حساب الدرجة التقنية الكاملة

        Args:
            elements: قائمة العناصر [{'code': '3A', 'goe': 2, 'errors': []}, ...]

        Returns:
            (total_base_value, total_goe, technical_score, element_scores)
        """
        total_base_value = 0.0
        total_goe = 0.0
        element_scores = []

        for element in elements:
            code = element.get('code')
            goe = element.get('goe', 0)
            errors = element.get('errors', [])

            element_score = self.calculate_element_score(code, goe, errors)

            if element_score:
                total_base_value += element_score.base_value
                total_goe += element_score.goe_value
                element_scores.append(element_score)

        technical_score = total_base_value + total_goe

        return total_base_value, total_goe, technical_score, element_scores

    def calculate_program_components(
        self,
        skating_skills: float,
        transitions: float,
        performance: float,
        composition: float,
        interpretation: float,
        factor: float = 1.0
    ) -> float:
        """
        حساب درجة المكونات البرنامجية

        Args:
            skating_skills: مهارات التزلج (0-10)
            transitions: الانتقالات (0-10)
            performance: الأداء (0-10)
            composition: التكوين (0-10)
            interpretation: التفسير (0-10)
            factor: معامل المكونات (0.8 للقصير، 1.0 للحر)

        Returns:
            درجة المكونات الإجمالية
        """
        # حساب المتوسط
        avg_score = (
            skating_skills +
            transitions +
            performance +
            composition +
            interpretation
        ) / 5.0

        # تطبيق المعامل
        return avg_score * factor

    def calculate_total_score(
        self,
        elements: List[Dict[str, Any]],
        skating_skills: float = 8.0,
        transitions: float = 7.5,
        performance: float = 8.0,
        composition: float = 7.8,
        interpretation: float = 7.9,
        deductions: Dict[str, int] = None,
        program_type: str = 'free'
    ) -> ProgramScore:
        """
        حساب الدرجة الإجمالية للبرنامج

        Args:
            elements: قائمة العناصر
            skating_skills: مهارات التزلج
            transitions: الانتقالات
            performance: الأداء
            composition: التكوين
            interpretation: التفسير
            deductions: الخصومات {'fall': 2, 'time_violation': 1}
            program_type: نوع البرنامج (short أو free)

        Returns:
            ProgramScore
        """
        # حساب الدرجة التقنية
        total_base, total_goe, tech_score, element_scores = self.calculate_technical_score(elements)

        # تحديد معامل المكونات
        factor = 0.8 if program_type == 'short' else 1.0

        # حساب درجة المكونات
        components_score = self.calculate_program_components(
            skating_skills,
            transitions,
            performance,
            composition,
            interpretation,
            factor
        )

        # حساب الخصومات
        total_deductions = 0.0
        deductions_breakdown = {}

        if deductions:
            for deduction_type, count in deductions.items():
                if deduction_type in self.standards.DEDUCTIONS:
                    deduction_value = self.standards.DEDUCTIONS[deduction_type] * count
                    total_deductions += abs(deduction_value)
                    deductions_breakdown[deduction_type] = deduction_value

        # الدرجة النهائية
        final_score = tech_score + components_score - total_deductions

        return ProgramScore(
            total_base_value=total_base,
            total_goe=total_goe,
            technical_score=tech_score,
            skating_skills=skating_skills,
            transitions=transitions,
            performance=performance,
            composition=composition,
            interpretation=interpretation,
            program_components_score=components_score,
            total_deductions=total_deductions,
            total_score=final_score,
            elements=element_scores,
            deductions=deductions_breakdown
        )

    def estimate_goe(
        self,
        quality_metrics: Dict[str, float]
    ) -> int:
        """
        تقدير GOE بناءً على مقاييس الجودة

        Args:
            quality_metrics: مقاييس الجودة
                {
                    'height': 0.8,
                    'rotation': 0.9,
                    'landing': 0.7,
                    'flow': 0.85
                }

        Returns:
            GOE المقدر (-5 إلى +5)
        """
        # حساب متوسط الجودة
        avg_quality = sum(quality_metrics.values()) / len(quality_metrics)

        # تحويل إلى GOE
        if avg_quality >= 0.95:
            return 5
        elif avg_quality >= 0.85:
            return 4
        elif avg_quality >= 0.75:
            return 3
        elif avg_quality >= 0.65:
            return 2
        elif avg_quality >= 0.55:
            return 1
        elif avg_quality >= 0.45:
            return 0
        elif avg_quality >= 0.35:
            return -1
        elif avg_quality >= 0.25:
            return -2
        elif avg_quality >= 0.15:
            return -3
        elif avg_quality >= 0.05:
            return -4
        else:
            return -5
