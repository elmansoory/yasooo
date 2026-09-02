"""
🏅 امتحانات ISU — نفس بنية مختبر ISI لكن مقيّدة على معايير اتحاد ISU.
"""
from src.pages.test_standards_page import show_federation_exams_page
from src.analysis.test_standards import FEDERATION_ISU


def show_isu_exams_page(lang: str = 'ar'):
    show_federation_exams_page(FEDERATION_ISU, lang)
