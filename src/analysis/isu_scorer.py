"""
🏅 محرك تسجيل النقاط وفق معايير ISU الرسمية
ISU Official Scoring Engine
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# ===========================================================================
# ISU 2024 Jump Base Values
# Key format: "<rotations><type_abbreviation>"
# Rotations: 1=single, 2=double, 3=triple, 4=quadruple
# Types: A=Axel, Lz=Lutz, F=Flip, Lo=Loop, S=Salchow, T=Toe Loop
# ===========================================================================

JUMP_BASE_VALUES: Dict[str, float] = {
    # Single Jumps (1 rotation)
    "1A":   1.10,
    "1Lz":  0.60,
    "1F":   0.50,
    "1Lo":  0.50,
    "1S":   0.40,
    "1T":   0.40,

    # Double Jumps (2 rotations)
    "2A":   3.30,
    "2Lz":  2.10,
    "2F":   1.80,
    "2Lo":  1.70,
    "2S":   1.30,
    "2T":   1.30,

    # Triple Jumps (3 rotations)
    "3A":   8.00,
    "3Lz":  5.90,
    "3F":   5.30,
    "3Lo":  4.90,
    "3S":   4.30,
    "3T":   4.20,

    # Quadruple Jumps (4 rotations) — ISU 2024 values
    "4A":  12.50,
    "4Lz": 11.50,
    "4F":  11.00,
    "4Lo": 10.50,
    "4S":   9.70,
    "4T":   9.50,
}

# Downgraded jump suffix is "<<"  (e.g. "3A<<" treated as one rotation lower)
# Under-rotated suffix is "<" (base value × 0.70 per ISU rules)
UNDER_ROTATION_FACTOR: float = 0.70

# ===========================================================================
# ISU 2024 Spin Base Values
# Dict structure: spin_type -> list of base values indexed by level [0..4]
# Level 0 = no level / basic, Levels 1-4 = ISU levels
# ===========================================================================

SPIN_BASE_VALUES: Dict[str, List[float]] = {
    "USp":   [0.00, 1.20, 1.50, 1.90, 2.40],   # Upright Spin
    "LSp":   [0.00, 1.50, 1.90, 2.40, 2.70],   # Layback Spin
    "CSp":   [0.00, 1.40, 1.80, 2.30, 2.60],   # Camel Spin
    "SSp":   [0.00, 1.30, 1.60, 2.10, 2.50],   # Sit Spin
    "CoSp":  [0.00, 1.70, 2.00, 2.50, 3.00],   # Combination Spin
    "FCSp":  [0.00, 1.90, 2.30, 2.80, 3.20],   # Flying Camel Spin
    "FSSp":  [0.00, 1.80, 2.10, 2.60, 3.00],   # Flying Sit Spin
    "CCoSp": [0.00, 1.70, 2.00, 2.50, 3.00],   # Change Foot Combination Spin
    "FCCoSp":[0.00, 1.70, 2.00, 2.50, 3.50],   # Flying Change Foot Combination Spin
    "CUSp":  [0.00, 1.40, 1.70, 2.20, 2.60],   # Change Foot Upright Spin
    "CSSp":  [0.00, 1.40, 1.60, 2.10, 2.60],   # Change Foot Sit Spin
}

# ===========================================================================
# GOE Multipliers
# GOE scale: -5 to +5 (11 values)
# Multiplier is applied to base value:  goe_value = base_value * multiplier
# ISU 2018+ system uses proportional GOE based on base value
# ===========================================================================

GOE_MULTIPLIERS: List[float] = [
    -1.0,   # GOE -5
    -0.8,   # GOE -4
    -0.6,   # GOE -3
    -0.4,   # GOE -2
    -0.2,   # GOE -1
     0.0,   # GOE  0
     0.2,   # GOE +1
     0.4,   # GOE +2
     0.6,   # GOE +3
     0.8,   # GOE +4
     1.0,   # GOE +5
]

# Mapping from integer GOE to list index
_GOE_INDEX: Dict[int, int] = {goe: idx for idx, goe in enumerate(range(-5, 6))}

# ===========================================================================
# Program Component Score names
# ===========================================================================

PCS_COMPONENTS: List[str] = [
    "Skating Skills",
    "Transitions",
    "Performance",
    "Composition",
    "Interpretation",
]

# ===========================================================================
# Deduction constants
# ===========================================================================

FALL_DEDUCTION: float = -1.0
TIME_VIOLATION_DEDUCTION: float = -1.0
ILLEGAL_ELEMENT_DEDUCTION: float = -2.0
COSTUME_FAILURE_DEDUCTION: float = -1.0


# ===========================================================================
# ISUScorer class
# ===========================================================================

class ISUScorer:
    """
    Comprehensive ISU scoring engine implementing the 2024 Grade of Execution
    (GOE) system and Program Component Score (PCS) calculations.

    All base values follow the official ISU Communication No. 2445 (2024).
    """

    def __init__(self) -> None:
        self._jump_bv = JUMP_BASE_VALUES
        self._spin_bv = SPIN_BASE_VALUES
        self._goe_multipliers = GOE_MULTIPLIERS

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _goe_multiplier(self, goe: int) -> float:
        """Return the GOE multiplier for an integer GOE value (-5 … +5)."""
        goe = max(-5, min(5, int(goe)))
        return self._goe_multipliers[_GOE_INDEX[goe]]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calc_jump_score(
        self,
        jump_type: str,
        rotations: int,
        goe: int,
        downgrade: bool = False,
        fall: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculate the score for a single jump element.

        Parameters
        ----------
        jump_type : str
            Jump abbreviation: 'A', 'Lz', 'F', 'Lo', 'S', 'T'
        rotations : int
            Number of full rotations (1-4).  For Axel add 0.5 in the
            physics, but the ISU code uses integer rotation count here.
        goe : int
            Grade of Execution (-5 … +5).
        downgrade : bool
            If True the element is treated as fully downgraded (one
            rotation fewer), and the "<<" notation is applied.
        fall : bool
            If True a fall deduction of -1.0 is applied and GOE is
            capped at -3.

        Returns
        -------
        Dict with keys: element_code, base_value, goe_value,
                        final_score, deductions, notes
        """
        rotations = max(1, min(4, int(rotations)))
        goe = max(-5, min(5, int(goe)))

        # Build element code
        element_code = f"{rotations}{jump_type}"
        notes: List[str] = []
        deductions: float = 0.0

        # Downgrade: treat as one rotation fewer
        effective_code = element_code
        if downgrade and rotations > 1:
            effective_code = f"{rotations - 1}{jump_type}"
            notes.append("downgraded (<<)")

        base_value: float = self._jump_bv.get(effective_code, 0.0)
        if base_value == 0.0:
            logger.warning("Unknown jump element: %s", effective_code)
            notes.append(f"unknown element '{effective_code}'")

        # Fall: cap GOE at -3, apply fall deduction
        if fall:
            goe = min(-3, goe)
            deductions += FALL_DEDUCTION
            notes.append("fall (-1.0)")

        multiplier = self._goe_multiplier(goe)
        goe_value = round(base_value * multiplier, 2)
        final_score = round(base_value + goe_value + deductions, 2)
        # Score cannot go below 0
        final_score = max(0.0, final_score)

        return {
            "element_code": element_code,
            "effective_code": effective_code,
            "base_value": base_value,
            "goe": goe,
            "goe_value": goe_value,
            "final_score": final_score,
            "deductions": deductions,
            "notes": notes,
        }

    def calc_spin_score(
        self,
        spin_type: str,
        level: int,
        goe: int,
    ) -> Dict[str, Any]:
        """
        Calculate the score for a spin element.

        Parameters
        ----------
        spin_type : str
            Spin code e.g. 'USp', 'CSp', 'SSp', 'CoSp', etc.
        level : int
            ISU level (0-4).  Level 0 means no level / basic.
        goe : int
            Grade of Execution (-5 … +5).

        Returns
        -------
        Dict with keys: element_code, base_value, goe_value, final_score
        """
        level = max(0, min(4, int(level)))
        goe = max(-5, min(5, int(goe)))

        element_code = f"{spin_type}{level}" if level > 0 else spin_type
        bv_list = self._spin_bv.get(spin_type)
        if bv_list is None:
            logger.warning("Unknown spin type: %s", spin_type)
            base_value = 0.0
        else:
            base_value = bv_list[level]

        multiplier = self._goe_multiplier(goe)
        goe_value = round(base_value * multiplier, 2)
        final_score = round(max(0.0, base_value + goe_value), 2)

        return {
            "element_code": element_code,
            "spin_type": spin_type,
            "level": level,
            "base_value": base_value,
            "goe": goe,
            "goe_value": goe_value,
            "final_score": final_score,
        }

    def calc_pcs(
        self,
        component_scores: Dict[str, float],
        factor: float = 1.0,
    ) -> float:
        """
        Calculate the total Program Component Score (PCS).

        Parameters
        ----------
        component_scores : Dict[str, float]
            Mapping of component name (from PCS_COMPONENTS) to score
            (0.25 … 10.00, in increments of 0.25).
        factor : float
            Multiplication factor applied to each component score.
            Typical values: 1.0 (free skating), 0.8 (short program).

        Returns
        -------
        float  — total PCS (sum of all components × factor).
        """
        total: float = 0.0
        for component in PCS_COMPONENTS:
            score = float(component_scores.get(component, 0.0))
            score = max(0.0, min(10.0, score))
            total += round(score * factor, 2)
        return round(total, 2)

    def calc_total_tes(self, elements: List[Dict[str, Any]]) -> float:
        """
        Calculate the total Technical Element Score (TES).

        Each element dict must contain a 'final_score' key as produced
        by calc_jump_score / calc_spin_score, or any dict with
        'base_value', 'goe_value', and optionally 'deductions'.

        Parameters
        ----------
        elements : List[Dict]
            List of scored element dicts.

        Returns
        -------
        float — total TES rounded to 2 decimal places.
        """
        total: float = 0.0
        for elem in elements:
            if "final_score" in elem:
                total += float(elem["final_score"])
            else:
                bv = float(elem.get("base_value", 0.0))
                gv = float(elem.get("goe_value", 0.0))
                ded = float(elem.get("deductions", 0.0))
                total += max(0.0, bv + gv + ded)
        return round(total, 2)

    def apply_deductions(
        self,
        score: float,
        falls: int = 0,
        time_violation: bool = False,
    ) -> float:
        """
        Apply standard deductions to a total score.

        Parameters
        ----------
        score : float
            Score before deductions.
        falls : int
            Number of falls during the program (-1.0 each).
        time_violation : bool
            Whether a time violation occurred (-1.0).

        Returns
        -------
        float — score after deductions (minimum 0.0).
        """
        total_deduction: float = 0.0
        total_deduction += falls * abs(FALL_DEDUCTION)
        if time_violation:
            total_deduction += abs(TIME_VIOLATION_DEDUCTION)
        return round(max(0.0, score - total_deduction), 2)

    def format_protocol(
        self,
        elements: List[Dict[str, Any]],
        pcs: float,
        deductions: float,
    ) -> Dict[str, Any]:
        """
        Build a full scoring protocol document mirroring the official
        ISU judge's score sheet layout.

        Parameters
        ----------
        elements : List[Dict]
            List of scored element dicts (from calc_jump_score /
            calc_spin_score or manually constructed).
        pcs : float
            Total Program Component Score (already factored).
        deductions : float
            Total deductions as a positive number (will be subtracted).

        Returns
        -------
        Dict — full protocol with keys:
            elements, total_base_value, total_goe, total_tes,
            pcs, deductions, total_score, breakdown
        """
        total_base_value: float = round(
            sum(float(e.get("base_value", 0.0)) for e in elements), 2
        )
        total_goe: float = round(
            sum(float(e.get("goe_value", 0.0)) for e in elements), 2
        )
        total_tes: float = self.calc_total_tes(elements)
        element_deductions: float = round(
            sum(abs(float(e.get("deductions", 0.0))) for e in elements), 2
        )
        # deductions parameter represents program-level deductions
        overall_deductions: float = round(
            abs(deductions) + element_deductions, 2
        )
        total_score: float = round(
            max(0.0, total_tes + pcs - abs(deductions)), 2
        )

        return {
            "elements": elements,
            "total_base_value": total_base_value,
            "total_goe": total_goe,
            "total_tes": total_tes,
            "pcs": round(pcs, 2),
            "deductions": overall_deductions,
            "total_score": total_score,
            "breakdown": {
                "tes": total_tes,
                "pcs": round(pcs, 2),
                "program_deductions": round(abs(deductions), 2),
                "element_deductions": element_deductions,
            },
        }

    def get_base_value(self, element_name: str) -> float:
        """
        Return the base value for a named element.

        Accepts jump codes ('4T', '3A', '2F', …), spin codes with
        optional level suffix ('CoSp4', 'USp3'), or bare spin type
        ('CoSp').

        Parameters
        ----------
        element_name : str
            Element code string.

        Returns
        -------
        float — base value, or 0.0 if the element is not found.
        """
        if element_name in self._jump_bv:
            return self._jump_bv[element_name]

        # Spin with level digit suffix e.g. "CoSp4"
        for spin_type in self._spin_bv:
            if element_name.startswith(spin_type):
                suffix = element_name[len(spin_type):]
                if suffix.isdigit():
                    level = int(suffix)
                    bv_list = self._spin_bv[spin_type]
                    if 0 <= level < len(bv_list):
                        return bv_list[level]
                elif suffix == "":
                    # No level specified — return level 0
                    return self._spin_bv[spin_type][0]

        return 0.0

    def element_lookup(self, name: str) -> Dict[str, Any]:
        """
        Look up detailed information for an element by code.

        Searches jumps first, then spins (with optional level suffix).

        Parameters
        ----------
        name : str
            Element code e.g. '4T', '3A', 'CoSp4', 'USp3'.

        Returns
        -------
        Dict with element info, or empty dict if not found.
        Keys always include: 'code', 'type', 'base_value'.
        Jump elements also include: 'rotations', 'jump_type'.
        Spin elements also include: 'spin_type', 'level'.
        """
        # Jump lookup
        if name in self._jump_bv:
            rotations = int(name[0]) if name[0].isdigit() else None
            jump_type = name[1:] if rotations is not None else name
            return {
                "code": name,
                "type": "jump",
                "base_value": self._jump_bv[name],
                "rotations": rotations,
                "jump_type": jump_type,
            }

        # Spin lookup
        for spin_type in self._spin_bv:
            if name.startswith(spin_type):
                suffix = name[len(spin_type):]
                if suffix.isdigit():
                    level = int(suffix)
                elif suffix == "":
                    level = 0
                else:
                    continue
                bv_list = self._spin_bv[spin_type]
                if 0 <= level < len(bv_list):
                    return {
                        "code": name,
                        "type": "spin",
                        "spin_type": spin_type,
                        "level": level,
                        "base_value": bv_list[level],
                        "all_levels": {
                            i: bv_list[i] for i in range(len(bv_list))
                        },
                    }

        return {}


# ===========================================================================
# Module-level convenience instance
# ===========================================================================

_default_scorer = ISUScorer()


def score_jump(
    jump_type: str,
    rotations: int,
    goe: int,
    downgrade: bool = False,
    fall: bool = False,
) -> Dict[str, Any]:
    """Module-level shortcut for ISUScorer().calc_jump_score(...)."""
    return _default_scorer.calc_jump_score(
        jump_type, rotations, goe, downgrade, fall
    )


def score_spin(spin_type: str, level: int, goe: int) -> Dict[str, Any]:
    """Module-level shortcut for ISUScorer().calc_spin_score(...)."""
    return _default_scorer.calc_spin_score(spin_type, level, goe)
