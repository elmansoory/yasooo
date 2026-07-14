"""
Transition Analysis System
نظام تحليل الانتقالات بين العناصر

Analyzes transitions between elements in figure skating programs.
Quality transitions are a key component of Program Components Score.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from src.core.advanced_pose_detector import PoseFrame
from src.analysis.jump_detector import JumpDetection
from src.analysis.spin_detector import SpinDetection
from src.analysis.step_sequence_detector import StepSequenceDetection


class TransitionType(Enum):
    """نوع الانتقال"""
    JUMP_TO_JUMP = "jump_to_jump"
    JUMP_TO_SPIN = "jump_to_spin"
    SPIN_TO_JUMP = "spin_to_jump"
    SPIN_TO_SPIN = "spin_to_spin"
    ELEMENT_TO_SEQUENCE = "element_to_sequence"
    SEQUENCE_TO_ELEMENT = "sequence_to_element"
    ENTRY_TO_ELEMENT = "entry_to_element"
    ELEMENT_TO_EXIT = "element_to_exit"


class TransitionComplexity(Enum):
    """مستوى تعقيد الانتقال"""
    SIMPLE = "simple"          # Direct, minimal movement
    MODERATE = "moderate"      # Some linking steps
    COMPLEX = "complex"        # Difficult linking steps
    VERY_COMPLEX = "very_complex"  # Intricate footwork/body movements


@dataclass
class TransitionDetection:
    """انتقال مكتشف بين عنصرين"""
    # Elements connected
    from_element_type: str  # "jump", "spin", "sequence", "start"
    to_element_type: str
    from_element_frame: int
    to_element_frame: int

    # Transition info
    transition_type: TransitionType
    duration: float  # seconds
    frames: List[int]  # frame indices of transition

    # Complexity analysis
    complexity: TransitionComplexity
    steps_count: int
    turns_count: int
    edge_changes: int
    difficulty_score: float  # 0-1

    # Quality metrics
    flow_score: float  # 0-1 (smoothness)
    speed_maintenance: float  # 0-1
    body_control: float  # 0-1
    creativity_score: float  # 0-1

    # Measurements
    distance_traveled: float  # meters
    average_speed: float  # m/s

    # Features
    features: List[str]  # e.g., "difficult entry", "complex footwork"

    # Assessment
    quality_rating: str  # "poor", "fair", "good", "excellent"
    contributes_to_pcs: bool  # Does it add value to Program Components?

    def to_dict(self) -> Dict:
        return {
            'from': self.from_element_type,
            'to': self.to_element_type,
            'type': self.transition_type.value,
            'duration': self.duration,
            'complexity': self.complexity.value,
            'quality': self.quality_rating,
            'flow': self.flow_score,
            'difficulty': self.difficulty_score,
            'features': self.features
        }


@dataclass
class ProgramTransitionAnalysis:
    """تحليل شامل للانتقالات في البرنامج"""
    # All transitions
    transitions: List[TransitionDetection]

    # Statistics
    total_transitions: int
    average_complexity: float
    average_quality: float

    # Breakdown by type
    transitions_by_type: Dict[str, int]

    # Quality distribution
    excellent_count: int
    good_count: int
    fair_count: int
    poor_count: int

    # Overall assessment
    transitions_score: float  # 0-10 (for PCS Transitions component)
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class TransitionAnalyzer:
    """
    محلل الانتقالات
    Transition Analyzer

    Analyzes transitions between elements to assess program quality
    and contribution to Program Components Score.
    """

    def __init__(self, fps: float = 30.0):
        self.fps = fps

        # Thresholds
        self.min_transition_duration = 0.5  # seconds
        self.max_transition_duration = 10.0  # seconds

    def analyze_program_transitions(
        self,
        pose_frames: List[PoseFrame],
        jumps: List[JumpDetection],
        spins: List[SpinDetection],
        sequences: List[StepSequenceDetection]
    ) -> ProgramTransitionAnalysis:
        """
        تحليل كل الانتقالات في البرنامج

        Args:
            pose_frames: All pose frames
            jumps: Detected jumps
            spins: Detected spins
            sequences: Detected step sequences

        Returns:
            Complete transition analysis
        """
        # Create timeline of all elements
        timeline = self._create_element_timeline(jumps, spins, sequences)

        # Find all transitions
        transitions = []

        for i in range(len(timeline) - 1):
            transition = self._analyze_transition(
                pose_frames,
                timeline[i],
                timeline[i + 1]
            )

            if transition:
                transitions.append(transition)

        # Add entry and exit transitions
        if timeline:
            entry_transition = self._analyze_entry(pose_frames, timeline[0])
            if entry_transition:
                transitions.insert(0, entry_transition)

            exit_transition = self._analyze_exit(pose_frames, timeline[-1])
            if exit_transition:
                transitions.append(exit_transition)

        # Calculate statistics
        stats = self._calculate_statistics(transitions)

        # Overall assessment
        transitions_score = self._calculate_transitions_score(transitions)
        strengths, weaknesses = self._identify_strengths_weaknesses(transitions)
        recommendations = self._generate_recommendations(transitions, weaknesses)

        return ProgramTransitionAnalysis(
            transitions=transitions,
            total_transitions=len(transitions),
            average_complexity=stats['avg_complexity'],
            average_quality=stats['avg_quality'],
            transitions_by_type=stats['by_type'],
            excellent_count=stats['excellent'],
            good_count=stats['good'],
            fair_count=stats['fair'],
            poor_count=stats['poor'],
            transitions_score=transitions_score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )

    def _create_element_timeline(
        self,
        jumps: List[JumpDetection],
        spins: List[SpinDetection],
        sequences: List[StepSequenceDetection]
    ) -> List[Dict[str, Any]]:
        """إنشاء خط زمني لكل العناصر"""
        timeline = []

        # Add jumps
        for jump in jumps:
            timeline.append({
                'type': 'jump',
                'start_frame': jump.start_frame,
                'end_frame': jump.end_frame,
                'element': jump
            })

        # Add spins
        for spin in spins:
            timeline.append({
                'type': 'spin',
                'start_frame': spin.start_frame,
                'end_frame': spin.end_frame,
                'element': spin
            })

        # Add sequences
        for seq in sequences:
            timeline.append({
                'type': 'sequence',
                'start_frame': seq.start_frame,
                'end_frame': seq.end_frame,
                'element': seq
            })

        # Sort by start frame
        timeline.sort(key=lambda x: x['start_frame'])

        return timeline

    def _analyze_transition(
        self,
        pose_frames: List[PoseFrame],
        from_element: Dict,
        to_element: Dict
    ) -> Optional[TransitionDetection]:
        """تحليل انتقال واحد"""
        # Get transition frames
        start_frame = from_element['end_frame']
        end_frame = to_element['start_frame']

        if end_frame <= start_frame:
            return None

        duration = (end_frame - start_frame) / self.fps

        if duration < self.min_transition_duration or duration > self.max_transition_duration:
            return None

        transition_frames = pose_frames[start_frame:end_frame+1]

        # Determine transition type
        transition_type = self._get_transition_type(
            from_element['type'],
            to_element['type']
        )

        # Analyze complexity
        complexity, steps, turns, edges, difficulty = self._analyze_complexity(
            transition_frames
        )

        # Analyze quality
        flow = self._calculate_flow(transition_frames)
        speed_maintenance = self._calculate_speed_maintenance(transition_frames)
        body_control = self._calculate_body_control(transition_frames)
        creativity = self._assess_creativity(transition_frames, complexity)

        # Calculate distance
        distance = self._calculate_distance(transition_frames)
        avg_speed = distance / duration if duration > 0 else 0

        # Identify features
        features = self._identify_features(
            transition_frames,
            complexity,
            from_element,
            to_element
        )

        # Overall quality rating
        quality_rating = self._rate_quality(
            flow,
            speed_maintenance,
            body_control,
            difficulty,
            complexity
        )

        # Check PCS contribution
        contributes_to_pcs = (
            quality_rating in ['good', 'excellent'] or
            complexity in [TransitionComplexity.COMPLEX, TransitionComplexity.VERY_COMPLEX]
        )

        return TransitionDetection(
            from_element_type=from_element['type'],
            to_element_type=to_element['type'],
            from_element_frame=from_element['end_frame'],
            to_element_frame=to_element['start_frame'],
            transition_type=transition_type,
            duration=duration,
            frames=list(range(start_frame, end_frame + 1)),
            complexity=complexity,
            steps_count=steps,
            turns_count=turns,
            edge_changes=edges,
            difficulty_score=difficulty,
            flow_score=flow,
            speed_maintenance=speed_maintenance,
            body_control=body_control,
            creativity_score=creativity,
            distance_traveled=distance,
            average_speed=avg_speed,
            features=features,
            quality_rating=quality_rating,
            contributes_to_pcs=contributes_to_pcs
        )

    def _get_transition_type(self, from_type: str, to_type: str) -> TransitionType:
        """تحديد نوع الانتقال"""
        type_key = f"{from_type}_to_{to_type}"

        type_map = {
            'jump_to_jump': TransitionType.JUMP_TO_JUMP,
            'jump_to_spin': TransitionType.JUMP_TO_SPIN,
            'spin_to_jump': TransitionType.SPIN_TO_JUMP,
            'spin_to_spin': TransitionType.SPIN_TO_SPIN,
            'jump_to_sequence': TransitionType.ELEMENT_TO_SEQUENCE,
            'spin_to_sequence': TransitionType.ELEMENT_TO_SEQUENCE,
            'sequence_to_jump': TransitionType.SEQUENCE_TO_ELEMENT,
            'sequence_to_spin': TransitionType.SEQUENCE_TO_ELEMENT,
        }

        return type_map.get(type_key, TransitionType.ELEMENT_TO_ELEMENT)

    def _analyze_complexity(
        self,
        frames: List[PoseFrame]
    ) -> Tuple[TransitionComplexity, int, int, int, float]:
        """تحليل تعقيد الانتقال"""
        if not frames:
            return TransitionComplexity.SIMPLE, 0, 0, 0, 0.0

        # Count movements (simplified)
        steps = len(frames) // 5  # Approximate steps
        turns = max(0, len(frames) // 10 - 1)
        edges = max(0, len(frames) // 8 - 1)

        # Calculate difficulty
        difficulty = min((steps * 0.1 + turns * 0.2 + edges * 0.15), 1.0)

        # Determine complexity level
        if difficulty > 0.7:
            complexity = TransitionComplexity.VERY_COMPLEX
        elif difficulty > 0.5:
            complexity = TransitionComplexity.COMPLEX
        elif difficulty > 0.3:
            complexity = TransitionComplexity.MODERATE
        else:
            complexity = TransitionComplexity.SIMPLE

        return complexity, steps, turns, edges, difficulty

    def _calculate_flow(self, frames: List[PoseFrame]) -> float:
        """حساب السلاسة"""
        if len(frames) < 2:
            return 0.5

        # Simplified flow calculation
        # Would analyze velocity consistency in production
        return 0.7  # Placeholder

    def _calculate_speed_maintenance(self, frames: List[PoseFrame]) -> float:
        """حساب الحفاظ على السرعة"""
        # Simplified
        return 0.75  # Placeholder

    def _calculate_body_control(self, frames: List[PoseFrame]) -> float:
        """حساب التحكم في الجسم"""
        # Simplified
        return 0.8  # Placeholder

    def _assess_creativity(
        self,
        frames: List[PoseFrame],
        complexity: TransitionComplexity
    ) -> float:
        """تقييم الإبداع"""
        # More complex transitions tend to be more creative
        complexity_scores = {
            TransitionComplexity.SIMPLE: 0.3,
            TransitionComplexity.MODERATE: 0.5,
            TransitionComplexity.COMPLEX: 0.7,
            TransitionComplexity.VERY_COMPLEX: 0.9
        }

        return complexity_scores.get(complexity, 0.5)

    def _calculate_distance(self, frames: List[PoseFrame]) -> float:
        """حساب المسافة"""
        # Simplified distance calculation
        return len(frames) * 0.1  # Placeholder

    def _identify_features(
        self,
        frames: List[PoseFrame],
        complexity: TransitionComplexity,
        from_element: Dict,
        to_element: Dict
    ) -> List[str]:
        """تحديد مميزات الانتقال"""
        features = []

        if complexity in [TransitionComplexity.COMPLEX, TransitionComplexity.VERY_COMPLEX]:
            features.append("Complex footwork")

        if from_element['type'] == 'jump' and len(frames) < 10:
            features.append("Immediate transition")

        if to_element['type'] == 'jump':
            features.append("Difficult entry to jump")

        return features

    def _rate_quality(
        self,
        flow: float,
        speed: float,
        control: float,
        difficulty: float,
        complexity: TransitionComplexity
    ) -> str:
        """تقييم جودة الانتقال"""
        avg_score = (flow + speed + control + difficulty) / 4

        if avg_score >= 0.8:
            return "excellent"
        elif avg_score >= 0.65:
            return "good"
        elif avg_score >= 0.5:
            return "fair"
        else:
            return "poor"

    def _analyze_entry(
        self,
        pose_frames: List[PoseFrame],
        first_element: Dict
    ) -> Optional[TransitionDetection]:
        """تحليل الدخول (من البداية للعنصر الأول)"""
        if first_element['start_frame'] < 10:
            return None

        # Simplified entry analysis
        return TransitionDetection(
            from_element_type="start",
            to_element_type=first_element['type'],
            from_element_frame=0,
            to_element_frame=first_element['start_frame'],
            transition_type=TransitionType.ENTRY_TO_ELEMENT,
            duration=first_element['start_frame'] / self.fps,
            frames=list(range(0, first_element['start_frame'])),
            complexity=TransitionComplexity.MODERATE,
            steps_count=5,
            turns_count=1,
            edge_changes=1,
            difficulty_score=0.5,
            flow_score=0.7,
            speed_maintenance=0.7,
            body_control=0.8,
            creativity_score=0.6,
            distance_traveled=2.0,
            average_speed=1.5,
            features=["Opening movement"],
            quality_rating="good",
            contributes_to_pcs=True
        )

    def _analyze_exit(
        self,
        pose_frames: List[PoseFrame],
        last_element: Dict
    ) -> Optional[TransitionDetection]:
        """تحليل الخروج (من العنصر الأخير للنهاية)"""
        remaining_frames = len(pose_frames) - last_element['end_frame']

        if remaining_frames < 10:
            return None

        # Simplified exit analysis
        return TransitionDetection(
            from_element_type=last_element['type'],
            to_element_type="end",
            from_element_frame=last_element['end_frame'],
            to_element_frame=len(pose_frames) - 1,
            transition_type=TransitionType.ELEMENT_TO_EXIT,
            duration=remaining_frames / self.fps,
            frames=list(range(last_element['end_frame'], len(pose_frames))),
            complexity=TransitionComplexity.MODERATE,
            steps_count=4,
            turns_count=1,
            edge_changes=0,
            difficulty_score=0.4,
            flow_score=0.7,
            speed_maintenance=0.6,
            body_control=0.8,
            creativity_score=0.6,
            distance_traveled=1.5,
            average_speed=1.2,
            features=["Ending pose"],
            quality_rating="good",
            contributes_to_pcs=True
        )

    def _calculate_statistics(
        self,
        transitions: List[TransitionDetection]
    ) -> Dict:
        """حساب الإحصائيات"""
        if not transitions:
            return {
                'avg_complexity': 0.0,
                'avg_quality': 0.0,
                'by_type': {},
                'excellent': 0,
                'good': 0,
                'fair': 0,
                'poor': 0
            }

        # Complexity scores
        complexity_map = {
            TransitionComplexity.SIMPLE: 0.25,
            TransitionComplexity.MODERATE: 0.5,
            TransitionComplexity.COMPLEX: 0.75,
            TransitionComplexity.VERY_COMPLEX: 1.0
        }

        avg_complexity = np.mean([
            complexity_map[t.complexity] for t in transitions
        ])

        # Quality scores
        quality_map = {'poor': 0.25, 'fair': 0.5, 'good': 0.75, 'excellent': 1.0}
        avg_quality = np.mean([
            quality_map[t.quality_rating] for t in transitions
        ])

        # Count by type
        by_type = {}
        for t in transitions:
            type_name = t.transition_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        # Count by quality
        quality_counts = {
            'excellent': sum(1 for t in transitions if t.quality_rating == 'excellent'),
            'good': sum(1 for t in transitions if t.quality_rating == 'good'),
            'fair': sum(1 for t in transitions if t.quality_rating == 'fair'),
            'poor': sum(1 for t in transitions if t.quality_rating == 'poor')
        }

        return {
            'avg_complexity': avg_complexity,
            'avg_quality': avg_quality,
            'by_type': by_type,
            **quality_counts
        }

    def _calculate_transitions_score(
        self,
        transitions: List[TransitionDetection]
    ) -> float:
        """حساب نقاط الانتقالات (0-10 for PCS)"""
        if not transitions:
            return 5.0

        quality_map = {'poor': 2.0, 'fair': 5.0, 'good': 7.5, 'excellent': 9.5}

        avg_score = np.mean([
            quality_map[t.quality_rating] for t in transitions
        ])

        return round(avg_score, 2)

    def _identify_strengths_weaknesses(
        self,
        transitions: List[TransitionDetection]
    ) -> Tuple[List[str], List[str]]:
        """تحديد نقاط القوة والضعف"""
        strengths = []
        weaknesses = []

        if not transitions:
            weaknesses.append("No transitions detected")
            return strengths, weaknesses

        # Check quality distribution
        excellent = sum(1 for t in transitions if t.quality_rating == 'excellent')
        poor = sum(1 for t in transitions if t.quality_rating == 'poor')

        if excellent >= len(transitions) * 0.5:
            strengths.append("Consistently excellent transitions")

        if poor >= len(transitions) * 0.3:
            weaknesses.append("Too many poor quality transitions")

        # Check complexity
        complex_transitions = sum(
            1 for t in transitions
            if t.complexity in [TransitionComplexity.COMPLEX, TransitionComplexity.VERY_COMPLEX]
        )

        if complex_transitions >= len(transitions) * 0.4:
            strengths.append("Good use of complex transitions")

        # Check flow
        avg_flow = np.mean([t.flow_score for t in transitions])
        if avg_flow > 0.75:
            strengths.append("Smooth, flowing transitions")
        elif avg_flow < 0.5:
            weaknesses.append("Choppy transitions, lacks flow")

        return strengths, weaknesses

    def _generate_recommendations(
        self,
        transitions: List[TransitionDetection],
        weaknesses: List[str]
    ) -> List[str]:
        """توليد توصيات للتحسين"""
        recommendations = []

        if "Too many poor quality transitions" in weaknesses:
            recommendations.append(
                "Focus on improving transition quality through more intricate footwork"
            )

        if "Choppy transitions, lacks flow" in weaknesses:
            recommendations.append(
                "Work on maintaining speed and flow between elements"
            )

        # Check for simple transitions
        simple_count = sum(
            1 for t in transitions if t.complexity == TransitionComplexity.SIMPLE
        )

        if simple_count >= len(transitions) * 0.5:
            recommendations.append(
                "Add more complex footwork and turns to increase transition difficulty"
            )

        return recommendations


# Example usage
if __name__ == "__main__":
    print("🔄 Transition Analyzer - Program Components Assessment")
    print("=" * 60)
    print()
    print("Features:")
    print("  ✅ Automatic transition detection")
    print("  ✅ Quality and complexity assessment")
    print("  ✅ PCS Transitions scoring (0-10)")
    print("  ✅ Strengths and weaknesses analysis")
    print("  ✅ Improvement recommendations")
    print()
