"""
اختبارات محرك التسجيل
"""
import pytest
from src.analysis.scoring_engine import ScoringEngine


class TestScoringEngine:
    """اختبارات محرك التسجيل"""

    def setUp(self):
        """إعداد الاختبارات"""
        self.engine = ScoringEngine()

    def test_calculate_element_score(self):
        """اختبار حساب درجة عنصر"""
        engine = ScoringEngine()

        # اختبار قفزة Triple Axel مع GOE +2
        element_score = engine.calculate_element_score('3A', 2)

        assert element_score is not None
        assert element_score.base_value == 8.00
        assert element_score.goe == 2
        assert element_score.total_score > element_score.base_value

    def test_calculate_technical_score(self):
        """اختبار حساب الدرجة التقنية"""
        engine = ScoringEngine()

        elements = [
            {'code': '3A', 'goe': 2},
            {'code': '3Lz', 'goe': 1},
            {'code': '2T', 'goe': 0}
        ]

        base, goe, tech, element_scores = engine.calculate_technical_score(elements)

        assert base > 0
        assert tech == base + goe
        assert len(element_scores) == 3

    def test_estimate_goe(self):
        """اختبار تقدير GOE"""
        engine = ScoringEngine()

        # جودة ممتازة
        goe_excellent = engine.estimate_goe({
            'height': 0.95,
            'rotation': 0.98,
            'landing': 0.92,
            'flow': 0.90
        })

        assert goe_excellent >= 3

        # جودة متوسطة
        goe_average = engine.estimate_goe({
            'height': 0.5,
            'rotation': 0.5,
            'landing': 0.5,
            'flow': 0.5
        })

        assert -1 <= goe_average <= 1
