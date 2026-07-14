"""
Full Program Analyzer - Complete ISU Scoring System
محلل البرنامج الكامل - نظام تسجيل ISU الشامل

Analyzes complete skating programs and calculates:
- Technical Elements Score (TES)
- Program Components Score (PCS)
- Total Score
- Detailed breakdown and feedback
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json

from src.core.advanced_pose_detector import PoseFrame
from src.analysis.jump_detector import JumpDetection
from src.analysis.spin_detector import SpinDetection
from src.analysis.step_sequence_detector import StepSequenceDetection
from src.analysis.transition_analyzer import (
    TransitionAnalyzer,
    ProgramTransitionAnalysis
)
from src.config.isu_standards import ISUStandards


class ProgramType(Enum):
    """نوع البرنامج"""
    SHORT = "short"
    FREE = "free"
    EXHIBITION = "exhibition"


class SkaterLevel(Enum):
    """مستوى المتزلج"""
    NOVICE = "novice"
    JUNIOR = "junior"
    SENIOR = "senior"


class SkaterCategory(Enum):
    """فئة المتزلج"""
    MEN = "men"
    LADIES = "ladies"
    PAIRS = "pairs"
    ICE_DANCE = "ice_dance"


@dataclass
class ElementScore:
    """نقاط عنصر واحد"""
    element_type: str  # "jump", "spin", "sequence"
    element_code: str  # ISU code (e.g., "3A", "CCoSp4", "StSq3")
    base_value: float
    goe: int  # -5 to +5
    goe_value: float  # Actual GOE value added
    total_score: float
    features: List[str]
    errors: List[str]


@dataclass
class ProgramComponentsScore:
    """Program Components Score (5 components)"""
    # The 5 components (scored 0-10)
    skating_skills: float
    transitions: float
    performance: float
    composition: float
    interpretation: float  # (Short: Interpretation of Music)

    # Factor (depends on program type and category)
    factor: float

    # Total PCS
    total_pcs: float

    def to_dict(self) -> Dict:
        return {
            'skating_skills': self.skating_skills,
            'transitions': self.transitions,
            'performance': self.performance,
            'composition': self.composition,
            'interpretation': self.interpretation,
            'factor': self.factor,
            'total': self.total_pcs
        }


@dataclass
class ProgramAnalysis:
    """تحليل شامل للبرنامج الكامل"""
    # Program info
    program_type: ProgramType
    skater_level: SkaterLevel
    skater_category: SkaterCategory
    duration: float  # seconds

    # Elements detected
    jumps: List[JumpDetection]
    spins: List[SpinDetection]
    sequences: List[StepSequenceDetection]

    # Element scores
    element_scores: List[ElementScore]

    # Technical Elements Score
    total_base_value: float
    total_goe: float
    technical_score: float  # TES = Base Value + GOE

    # Program Components
    program_components: ProgramComponentsScore

    # Deductions
    deductions: Dict[str, float]  # e.g., {'falls': -1.0, 'time': -1.0}
    total_deductions: float

    # Final Score
    total_score: float  # TES + PCS - Deductions

    # Transition Analysis
    transition_analysis: ProgramTransitionAnalysis

    # Program Analysis
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]

    # Comparison
    estimated_rank_range: str  # e.g., "Top 10", "Top 50"
    competitive_level: str  # e.g., "National", "International", "Olympic"

    def to_dict(self) -> Dict:
        return {
            'program_type': self.program_type.value,
            'duration': self.duration,
            'technical_score': self.technical_score,
            'program_components': self.program_components.to_dict(),
            'deductions': self.deductions,
            'total_score': self.total_score,
            'element_count': {
                'jumps': len(self.jumps),
                'spins': len(self.spins),
                'sequences': len(self.sequences)
            },
            'strengths': self.strengths,
            'weaknesses': self.weaknesses
        }


class ProgramAnalyzer:
    """
    محلل البرنامج الكامل
    Full Program Analyzer

    Complete analysis system that combines all detectors
    to provide comprehensive program scoring and feedback.
    """

    def __init__(self):
        self.isu_standards = ISUStandards()
        self.transition_analyzer = TransitionAnalyzer()

        # PCS Factors (multiplier for total PCS)
        self.pcs_factors = {
            ProgramType.SHORT: 0.8,  # Short Program factor
            ProgramType.FREE: 1.6,   # Free Skate factor (Senior/Junior)
        }

    def analyze_program(
        self,
        pose_frames: List[PoseFrame],
        jumps: List[JumpDetection],
        spins: List[SpinDetection],
        sequences: List[StepSequenceDetection],
        program_type: ProgramType = ProgramType.FREE,
        skater_level: SkaterLevel = SkaterLevel.SENIOR,
        skater_category: SkaterCategory = SkaterCategory.LADIES
    ) -> ProgramAnalysis:
        """
        تحليل برنامج كامل مع حساب النقاط

        Args:
            pose_frames: All pose frames from video
            jumps: Detected jumps
            spins: Detected spins
            sequences: Detected step sequences
            program_type: Short or Free program
            skater_level: Skater level
            skater_category: Men, Ladies, etc.

        Returns:
            Complete program analysis with scores
        """
        # Calculate duration
        fps = 30.0  # Assuming 30 fps
        duration = len(pose_frames) / fps

        # Calculate Technical Elements Score
        element_scores = self._score_elements(jumps, spins, sequences)
        total_base_value = sum(e.base_value for e in element_scores)
        total_goe = sum(e.goe_value for e in element_scores)
        technical_score = total_base_value + total_goe

        # Analyze transitions
        transition_analysis = self.transition_analyzer.analyze_program_transitions(
            pose_frames,
            jumps,
            spins,
            sequences
        )

        # Calculate Program Components Score
        program_components = self._calculate_program_components(
            pose_frames,
            jumps,
            spins,
            sequences,
            transition_analysis,
            program_type,
            duration
        )

        # Calculate deductions
        deductions = self._calculate_deductions(
            jumps,
            spins,
            duration,
            program_type,
            skater_level
        )
        total_deductions = sum(deductions.values())

        # Calculate total score
        total_score = technical_score + program_components.total_pcs - total_deductions

        # Program analysis
        strengths, weaknesses = self._analyze_program_quality(
            jumps,
            spins,
            sequences,
            transition_analysis,
            program_components
        )

        recommendations = self._generate_recommendations(
            weaknesses,
            program_type,
            technical_score,
            program_components
        )

        # Estimate competitive level
        rank_range, competitive_level = self._estimate_competitive_level(
            total_score,
            program_type,
            skater_category
        )

        return ProgramAnalysis(
            program_type=program_type,
            skater_level=skater_level,
            skater_category=skater_category,
            duration=duration,
            jumps=jumps,
            spins=spins,
            sequences=sequences,
            element_scores=element_scores,
            total_base_value=total_base_value,
            total_goe=total_goe,
            technical_score=technical_score,
            program_components=program_components,
            deductions=deductions,
            total_deductions=total_deductions,
            total_score=total_score,
            transition_analysis=transition_analysis,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            estimated_rank_range=rank_range,
            competitive_level=competitive_level
        )

    def _score_elements(
        self,
        jumps: List[JumpDetection],
        spins: List[SpinDetection],
        sequences: List[StepSequenceDetection]
    ) -> List[ElementScore]:
        """حساب نقاط جميع العناصر"""
        scores = []

        # Score jumps
        for jump in jumps:
            code = f"{jump.rotations:.0f}{jump.jump_type.value}"
            base_value = self._get_jump_base_value(code)
            goe_value = self._calculate_goe_value(base_value, jump.estimated_goe)

            scores.append(ElementScore(
                element_type="jump",
                element_code=code,
                base_value=base_value,
                goe=jump.estimated_goe,
                goe_value=goe_value,
                total_score=base_value + goe_value,
                features=jump.goe_positive_factors,
                errors=jump.errors
            ))

        # Score spins
        for spin in spins:
            code = spin.get_isu_code()
            base_value = self._get_spin_base_value(code)
            goe_value = self._calculate_goe_value(base_value, spin.estimated_goe)

            scores.append(ElementScore(
                element_type="spin",
                element_code=code,
                base_value=base_value,
                goe=spin.estimated_goe,
                goe_value=goe_value,
                total_score=base_value + goe_value,
                features=spin.features,
                errors=spin.errors
            ))

        # Score sequences
        for seq in sequences:
            code = seq.get_isu_code()
            base_value = self._get_sequence_base_value(code)
            goe_value = self._calculate_goe_value(base_value, seq.estimated_goe)

            scores.append(ElementScore(
                element_type="sequence",
                element_code=code,
                base_value=base_value,
                goe=seq.estimated_goe,
                goe_value=goe_value,
                total_score=base_value + goe_value,
                features=seq.level_features,
                errors=seq.errors
            ))

        return scores

    def _get_jump_base_value(self, code: str) -> float:
        """الحصول على Base Value للقفزة"""
        # Simplified - would use ISU standards table
        base_values = {
            '1A': 1.1, '2A': 3.3, '3A': 8.0, '4A': 12.5,
            '1Lz': 0.6, '2Lz': 2.1, '3Lz': 5.9, '4Lz': 11.5,
            '1F': 0.5, '2F': 1.8, '3F': 5.3, '4F': 11.0,
            '1Lo': 0.5, '2Lo': 1.7, '3Lo': 4.9, '4Lo': 10.5,
            '1S': 0.4, '2S': 1.3, '3S': 4.3, '4S': 9.7,
            '1T': 0.4, '2T': 1.3, '3T': 4.2, '4T': 9.5,
        }
        return base_values.get(code, 1.0)

    def _get_spin_base_value(self, code: str) -> float:
        """الحصول على Base Value للدوران"""
        # Extract level from code (e.g., "CCoSp4" -> 4)
        level = int(code[-1]) if code[-1].isdigit() else 1

        base_values = {1: 1.5, 2: 1.8, 3: 2.4, 4: 3.0}
        return base_values.get(level, 1.5)

    def _get_sequence_base_value(self, code: str) -> float:
        """الحصول على Base Value للمتتالية"""
        level = int(code[-1]) if code[-1].isdigit() else 1

        base_values = {1: 1.8, 2: 2.6, 3: 3.3, 4: 3.9}
        return base_values.get(level, 1.8)

    def _calculate_goe_value(self, base_value: float, goe: int) -> float:
        """حساب قيمة GOE"""
        # GOE percentage of base value
        goe_percentages = {
            -5: -0.50, -4: -0.40, -3: -0.30, -2: -0.20, -1: -0.10,
            0: 0.00,
            1: 0.10, 2: 0.20, 3: 0.30, 4: 0.40, 5: 0.50
        }

        percentage = goe_percentages.get(goe, 0.0)
        return base_value * percentage

    def _calculate_program_components(
        self,
        pose_frames: List[PoseFrame],
        jumps: List[JumpDetection],
        spins: List[SpinDetection],
        sequences: List[StepSequenceDetection],
        transition_analysis: ProgramTransitionAnalysis,
        program_type: ProgramType,
        duration: float
    ) -> ProgramComponentsScore:
        """حساب Program Components Score"""

        # 1. Skating Skills (0-10)
        skating_skills = self._assess_skating_skills(
            pose_frames,
            jumps,
            spins,
            sequences
        )

        # 2. Transitions (0-10)
        transitions = transition_analysis.transitions_score

        # 3. Performance (0-10)
        performance = self._assess_performance(
            pose_frames,
            jumps,
            spins,
            duration
        )

        # 4. Composition (0-10)
        composition = self._assess_composition(
            jumps,
            spins,
            sequences,
            transition_analysis,
            duration
        )

        # 5. Interpretation (0-10)
        interpretation = self._assess_interpretation(
            pose_frames,
            duration
        )

        # Calculate total PCS
        factor = self.pcs_factors.get(program_type, 1.0)

        total_pcs = (
            skating_skills + transitions + performance +
            composition + interpretation
        ) * factor

        return ProgramComponentsScore(
            skating_skills=round(skating_skills, 2),
            transitions=round(transitions, 2),
            performance=round(performance, 2),
            composition=round(composition, 2),
            interpretation=round(interpretation, 2),
            factor=factor,
            total_pcs=round(total_pcs, 2)
        )

    def _assess_skating_skills(
        self,
        frames: List[PoseFrame],
        jumps: List[JumpDetection],
        spins: List[SpinDetection],
        sequences: List[StepSequenceDetection]
    ) -> float:
        """تقييم مهارات التزلج"""
        # Factors: edge quality, power, speed, flow, ice coverage

        # Base score
        score = 6.0

        # Quality of elements
        if jumps:
            avg_jump_quality = np.mean([j.extension_quality for j in jumps])
            score += avg_jump_quality * 2

        if spins:
            avg_spin_quality = np.mean([s.position_quality for s in spins])
            score += avg_spin_quality * 1

        # Sequences show skating ability
        if sequences:
            avg_seq_quality = np.mean([s.flow_score for s in sequences])
            score += avg_seq_quality * 1

        return min(10.0, max(1.0, score))

    def _assess_performance(
        self,
        frames: List[PoseFrame],
        jumps: List[JumpDetection],
        spins: List[SpinDetection],
        duration: float
    ) -> float:
        """تقييم الأداء"""
        # Factors: commitment, carriage, projection, expression

        score = 6.5  # Base score

        # Consistency in execution
        if jumps:
            clean_jumps = sum(1 for j in jumps if j.is_clean)
            jump_consistency = clean_jumps / len(jumps) if jumps else 0
            score += jump_consistency * 1.5

        # Energy throughout program
        score += 0.5  # Placeholder

        return min(10.0, max(1.0, score))

    def _assess_composition(
        self,
        jumps: List[JumpDetection],
        spins: List[SpinDetection],
        sequences: List[StepSequenceDetection],
        transition_analysis: ProgramTransitionAnalysis,
        duration: float
    ) -> float:
        """تقييم التكوين"""
        # Factors: balance, variety, pattern, ice coverage

        score = 6.0

        # Element variety
        element_variety = len(set([
            j.jump_type for j in jumps
        ] + [
            s.spin_type for s in spins
        ]))
        score += min(element_variety * 0.3, 2.0)

        # Balanced distribution
        if transition_analysis.average_complexity > 0.6:
            score += 1.0

        return min(10.0, max(1.0, score))

    def _assess_interpretation(
        self,
        frames: List[PoseFrame],
        duration: float
    ) -> float:
        """تقييم التفسير الموسيقي"""
        # Factors: musicality, timing, expression

        # Simplified - would need audio analysis for accurate assessment
        score = 6.5

        # Movement variety
        score += 0.5

        return min(10.0, max(1.0, score))

    def _calculate_deductions(
        self,
        jumps: List[JumpDetection],
        spins: List[SpinDetection],
        duration: float,
        program_type: ProgramType,
        skater_level: SkaterLevel
    ) -> Dict[str, float]:
        """حساب الخصومات"""
        deductions = {}

        # Falls (-1.0 each)
        falls = sum(1 for j in jumps if 'fall' in [e.lower() for e in j.errors])
        if falls > 0:
            deductions['falls'] = -1.0 * falls

        # Time violations
        time_limits = {
            ProgramType.SHORT: {SkaterLevel.SENIOR: 170, SkaterLevel.JUNIOR: 150},
            ProgramType.FREE: {SkaterLevel.SENIOR: 240, SkaterLevel.JUNIOR: 210}
        }

        limit = time_limits.get(program_type, {}).get(skater_level, 300)

        if duration > limit + 10:
            deductions['time_violation'] = -1.0
        elif duration < limit - 10:
            deductions['time_violation'] = -1.0

        return deductions

    def _analyze_program_quality(
        self,
        jumps: List[JumpDetection],
        spins: List[SpinDetection],
        sequences: List[StepSequenceDetection],
        transition_analysis: ProgramTransitionAnalysis,
        pcs: ProgramComponentsScore
    ) -> Tuple[List[str], List[str]]:
        """تحليل جودة البرنامج"""
        strengths = []
        weaknesses = []

        # Jump analysis
        if jumps:
            clean_ratio = sum(1 for j in jumps if j.is_clean) / len(jumps)
            if clean_ratio > 0.7:
                strengths.append("High jump success rate")
            elif clean_ratio < 0.5:
                weaknesses.append("Many jump errors")

            triple_count = sum(1 for j in jumps if j.rotations >= 3)
            if triple_count >= 5:
                strengths.append("Strong technical content (multiple triples)")

        # Spin analysis
        if spins:
            high_level_spins = sum(1 for s in spins if s.level >= 3)
            if high_level_spins >= 2:
                strengths.append("High-level spin execution")

        # PCS analysis
        if pcs.transitions > 7.5:
            strengths.append("Excellent transitions between elements")
        elif pcs.transitions < 6.0:
            weaknesses.append("Weak transitions, needs more complex footwork")

        if pcs.skating_skills > 7.5:
            strengths.append("Strong skating skills")

        # Transition analysis
        if transition_analysis.average_quality > 0.7:
            strengths.append("Consistently good transitions")

        return strengths, weaknesses

    def _generate_recommendations(
        self,
        weaknesses: List[str],
        program_type: ProgramType,
        technical_score: float,
        pcs: ProgramComponentsScore
    ) -> List[str]:
        """توليد توصيات للتحسين"""
        recommendations = []

        if "Many jump errors" in weaknesses:
            recommendations.append(
                "Focus on jump technique and consistency in training"
            )

        if "Weak transitions" in weaknesses:
            recommendations.append(
                "Add more intricate footwork between elements"
            )

        if technical_score < 30:
            recommendations.append(
                "Consider upgrading technical content (add more triples/difficult spins)"
            )

        if pcs.interpretation < 6.5:
            recommendations.append(
                "Work on musical interpretation and expression"
            )

        return recommendations

    def _estimate_competitive_level(
        self,
        total_score: float,
        program_type: ProgramType,
        category: SkaterCategory
    ) -> Tuple[str, str]:
        """تقدير المستوى التنافسي"""
        # Rough estimates based on typical scores
        if program_type == ProgramType.SHORT:
            if total_score > 75:
                return "Top 3", "Olympic/World Championship"
            elif total_score > 65:
                return "Top 10", "International (Grand Prix)"
            elif total_score > 55:
                return "Top 20", "International"
            elif total_score > 45:
                return "Top 50", "National Championship"
            else:
                return "Developing", "Regional/National"
        else:  # Free Skate
            if total_score > 150:
                return "Top 3", "Olympic/World Championship"
            elif total_score > 130:
                return "Top 10", "International (Grand Prix)"
            elif total_score > 110:
                return "Top 20", "International"
            elif total_score > 90:
                return "Top 50", "National Championship"
            else:
                return "Developing", "Regional/National"


# Example usage
if __name__ == "__main__":
    print("🎭 Full Program Analyzer - Complete ISU Scoring")
    print("=" * 60)
    print()
    print("Features:")
    print("  ✅ Technical Elements Score (TES)")
    print("  ✅ Program Components Score (PCS)")
    print("  ✅ Total Score with deductions")
    print("  ✅ Detailed element breakdown")
    print("  ✅ Competitive level estimation")
    print("  ✅ Strengths & weaknesses analysis")
    print("  ✅ Improvement recommendations")
    print()
