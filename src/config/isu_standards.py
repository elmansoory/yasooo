"""
معايير الاتحاد الدولي للتزلج (ISU) للتسجيل والتقييم
ISU (International Skating Union) Standards
"""
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ISUElement:
    """عنصر ISU"""
    code: str
    name: str
    name_ar: str
    base_value: float
    element_type: str
    level: str = None


class ISUStandards:
    """معايير ISU الكاملة للتسجيل"""

    # ===== القفزات (Jumps) =====

    JUMPS: Dict[str, Dict[str, Any]] = {
        # Single Jumps
        '1A': {
            'name': 'Single Axel',
            'name_ar': 'أكسل مفرد',
            'base_value': 1.10,
            'rotations': 1.5,
            'edge': 'forward outside',
            'toe_pick': False
        },
        '1Lz': {
            'name': 'Single Lutz',
            'name_ar': 'لوتز مفرد',
            'base_value': 0.60,
            'rotations': 1.0,
            'edge': 'backward outside',
            'toe_pick': True
        },
        '1F': {
            'name': 'Single Flip',
            'name_ar': 'فليب مفرد',
            'base_value': 0.50,
            'rotations': 1.0,
            'edge': 'backward inside',
            'toe_pick': True
        },
        '1Lo': {
            'name': 'Single Loop',
            'name_ar': 'لووب مفرد',
            'base_value': 0.50,
            'rotations': 1.0,
            'edge': 'backward outside',
            'toe_pick': False
        },
        '1S': {
            'name': 'Single Salchow',
            'name_ar': 'سالكو مفرد',
            'base_value': 0.40,
            'rotations': 1.0,
            'edge': 'backward inside',
            'toe_pick': False
        },
        '1T': {
            'name': 'Single Toe Loop',
            'name_ar': 'تو لووب مفرد',
            'base_value': 0.40,
            'rotations': 1.0,
            'edge': 'backward outside',
            'toe_pick': True
        },

        # Double Jumps
        '2A': {
            'name': 'Double Axel',
            'name_ar': 'أكسل مزدوج',
            'base_value': 3.30,
            'rotations': 2.5,
            'edge': 'forward outside',
            'toe_pick': False
        },
        '2Lz': {
            'name': 'Double Lutz',
            'name_ar': 'لوتز مزدوج',
            'base_value': 2.10,
            'rotations': 2.0,
            'edge': 'backward outside',
            'toe_pick': True
        },
        '2F': {
            'name': 'Double Flip',
            'name_ar': 'فليب مزدوج',
            'base_value': 1.80,
            'rotations': 2.0,
            'edge': 'backward inside',
            'toe_pick': True
        },
        '2Lo': {
            'name': 'Double Loop',
            'name_ar': 'لووب مزدوج',
            'base_value': 1.70,
            'rotations': 2.0,
            'edge': 'backward outside',
            'toe_pick': False
        },
        '2S': {
            'name': 'Double Salchow',
            'name_ar': 'سالكو مزدوج',
            'base_value': 1.30,
            'rotations': 2.0,
            'edge': 'backward inside',
            'toe_pick': False
        },
        '2T': {
            'name': 'Double Toe Loop',
            'name_ar': 'تو لووب مزدوج',
            'base_value': 1.30,
            'rotations': 2.0,
            'edge': 'backward outside',
            'toe_pick': True
        },

        # Triple Jumps
        '3A': {
            'name': 'Triple Axel',
            'name_ar': 'أكسل ثلاثي',
            'base_value': 8.00,
            'rotations': 3.5,
            'edge': 'forward outside',
            'toe_pick': False
        },
        '3Lz': {
            'name': 'Triple Lutz',
            'name_ar': 'لوتز ثلاثي',
            'base_value': 5.90,
            'rotations': 3.0,
            'edge': 'backward outside',
            'toe_pick': True
        },
        '3F': {
            'name': 'Triple Flip',
            'name_ar': 'فليب ثلاثي',
            'base_value': 5.30,
            'rotations': 3.0,
            'edge': 'backward inside',
            'toe_pick': True
        },
        '3Lo': {
            'name': 'Triple Loop',
            'name_ar': 'لووب ثلاثي',
            'base_value': 4.90,
            'rotations': 3.0,
            'edge': 'backward outside',
            'toe_pick': False
        },
        '3S': {
            'name': 'Triple Salchow',
            'name_ar': 'سالكو ثلاثي',
            'base_value': 4.30,
            'rotations': 3.0,
            'edge': 'backward inside',
            'toe_pick': False
        },
        '3T': {
            'name': 'Triple Toe Loop',
            'name_ar': 'تو لووب ثلاثي',
            'base_value': 4.20,
            'rotations': 3.0,
            'edge': 'backward outside',
            'toe_pick': True
        },

        # Quadruple Jumps
        '4A': {
            'name': 'Quadruple Axel',
            'name_ar': 'أكسل رباعي',
            'base_value': 12.50,
            'rotations': 4.5,
            'edge': 'forward outside',
            'toe_pick': False
        },
        '4Lz': {
            'name': 'Quadruple Lutz',
            'name_ar': 'لوتز رباعي',
            'base_value': 11.50,
            'rotations': 4.0,
            'edge': 'backward outside',
            'toe_pick': True
        },
        '4F': {
            'name': 'Quadruple Flip',
            'name_ar': 'فليب رباعي',
            'base_value': 11.00,
            'rotations': 4.0,
            'edge': 'backward inside',
            'toe_pick': True
        },
        '4Lo': {
            'name': 'Quadruple Loop',
            'name_ar': 'لووب رباعي',
            'base_value': 10.50,
            'rotations': 4.0,
            'edge': 'backward outside',
            'toe_pick': False
        },
        '4S': {
            'name': 'Quadruple Salchow',
            'name_ar': 'سالكو رباعي',
            'base_value': 9.70,
            'rotations': 4.0,
            'edge': 'backward inside',
            'toe_pick': False
        },
        '4T': {
            'name': 'Quadruple Toe Loop',
            'name_ar': 'تو لووب رباعي',
            'base_value': 9.50,
            'rotations': 4.0,
            'edge': 'backward outside',
            'toe_pick': True
        },
    }

    # ===== الدورانات (Spins) =====

    SPINS: Dict[str, Dict[str, Any]] = {
        'USp': {
            'name': 'Upright Spin',
            'name_ar': 'دوران عمودي',
            'base_values': [0.0, 1.20, 1.50, 1.90, 2.40],
            'description': 'دوران في وضع الوقوف'
        },
        'LSp': {
            'name': 'Layback Spin',
            'name_ar': 'دوران منحني للخلف',
            'base_values': [0.0, 1.50, 1.90, 2.40, 2.70],
            'description': 'دوران مع انحناء الظهر للخلف'
        },
        'CSp': {
            'name': 'Camel Spin',
            'name_ar': 'دوران الجمل',
            'base_values': [0.0, 1.40, 1.80, 2.30, 2.60],
            'description': 'دوران أفقي مع رفع الرجل'
        },
        'SSp': {
            'name': 'Sit Spin',
            'name_ar': 'دوران القرفصاء',
            'base_values': [0.0, 1.30, 1.60, 2.10, 2.50],
            'description': 'دوران في وضع الجلوس'
        },
        'CoSp': {
            'name': 'Combination Spin',
            'name_ar': 'دوران مركب',
            'base_values': [0.0, 1.70, 2.00, 2.50, 3.00],
            'description': 'مزيج من أنواع الدوران'
        },
        'FCSp': {
            'name': 'Flying Camel Spin',
            'name_ar': 'دوران الجمل الطائر',
            'base_values': [0.0, 1.90, 2.30, 2.80, 3.20],
            'description': 'دوران جمل مع قفزة'
        },
        'FSSp': {
            'name': 'Flying Sit Spin',
            'name_ar': 'دوران القرفصاء الطائر',
            'base_values': [0.0, 1.80, 2.10, 2.60, 3.00],
            'description': 'دوران قرفصاء مع قفزة'
        },
        'CCoSp': {
            'name': 'Change Foot Combination Spin',
            'name_ar': 'دوران مركب بتغيير القدم',
            'base_values': [0.0, 1.70, 2.00, 2.50, 3.00],
            'description': 'دوران مركب مع تبديل القدم'
        },
    }

    # ===== تسلسلات الخطوات (Step Sequences) =====

    STEP_SEQUENCES: Dict[str, Dict[str, Any]] = {
        'StSq': {
            'name': 'Step Sequence',
            'name_ar': 'تسلسل الخطوات',
            'base_values': [0.0, 1.80, 2.60, 3.30, 3.90],
            'description': 'سلسلة من الخطوات والحركات'
        },
        'ChSq': {
            'name': 'Choreographic Sequence',
            'name_ar': 'تسلسل كوريوغرافي',
            'base_values': [0.0, 0.0, 0.0, 0.0, 0.0],
            'fixed_value': 0.0,
            'description': 'تسلسل فني بدون قيمة أساسية'
        },
    }

    # ===== معايير GOE (Grade of Execution) =====

    GOE_SCALE: List[int] = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]

    # قيم GOE كنسبة من القيمة الأساسية
    GOE_VALUES: Dict[int, float] = {
        -5: -0.50,  # -50%
        -4: -0.40,  # -40%
        -3: -0.30,  # -30%
        -2: -0.20,  # -20%
        -1: -0.10,  # -10%
        0: 0.00,    # 0%
        1: 0.10,    # +10%
        2: 0.20,    # +20%
        3: 0.30,    # +30%
        4: 0.40,    # +40%
        5: 0.50,    # +50%
    }

    # معايير GOE الإيجابية
    GOE_CRITERIA_POSITIVE: List[str] = [
        'ارتفاع وطول/مسافة جيدة (القفزات/الرفع)',
        'دخول/خروج جيد وسرعة/تدفق جيد',
        'تنفيذ واضح (بما في ذلك الهواء/الصعود/النزول)',
        'تنوع جيد في الوضعيات (في الدورانات فقط)',
        'سرعة دوران جيدة (في الدورانات فقط)',
        'هبوط نظيف وثابت (في القفزات فقط)',
        'موضع جيد في الهواء/الصعود (في القفزات/الرفع)',
        'عنصر يطابق شخصية الموسيقى',
    ]

    # معايير GOE السلبية
    GOE_CRITERIA_NEGATIVE: List[str] = [
        'سقوط',
        'هبوط غير كامل أو ضعيف',
        'فقدان السرعة/التدفق/الطاقة',
        'ضعف في تنفيذ المواضع',
        'دورات ناقصة',
        'خطأ في الحافة (e)',
        'حافة غير واضحة (!)',
        'دخول/خروج ضعيف',
        'فترة طويلة للتحضير',
        'تردد في التنفيذ',
    ]

    # ===== مكونات البرنامج (Program Components) =====

    PROGRAM_COMPONENTS: Dict[str, Dict[str, Any]] = {
        'skating_skills': {
            'name': 'Skating Skills',
            'name_ar': 'مهارات التزلج',
            'max_score': 10.0,
            'factor_short': 0.80,  # للبرنامج القصير
            'factor_free': 1.00,   # للبرنامج الحر
            'criteria': [
                'التوازن والتحكم في الجسم',
                'السلاسة في الحركة',
                'تنوع الحواف والخطوات',
                'عمق ونظافة الحواف',
                'القوة والسرعة والتسارع',
                'استخدام متعدد الاتجاهات للثلج',
            ]
        },
        'transitions': {
            'name': 'Transitions',
            'name_ar': 'الانتقالات',
            'max_score': 10.0,
            'factor_short': 0.80,
            'factor_free': 1.00,
            'criteria': [
                'تنوع الحركات الربطية',
                'صعوبة الانتقالات',
                'جودة وتدفق الحركات',
                'التعقيد الكوريوغرافي',
                'الاستخدام الأمثل لسطح الثلج',
            ]
        },
        'performance': {
            'name': 'Performance',
            'name_ar': 'الأداء',
            'max_score': 10.0,
            'factor_short': 0.80,
            'factor_free': 1.00,
            'criteria': [
                'التعبير الجسدي والعاطفي',
                'الإسقاط والكاريزما',
                'الطاقة والالتزام',
                'التنوع والتباين في الأداء',
                'التفاعل مع الموسيقى',
            ]
        },
        'composition': {
            'name': 'Composition',
            'name_ar': 'التكوين',
            'max_score': 10.0,
            'factor_short': 0.80,
            'factor_free': 1.00,
            'criteria': [
                'الهدف والوحدة والتعبير',
                'الاستفادة من المساحة',
                'النمط والتوازن',
                'البنية والتركيب',
                'التناسب والتوافق الموسيقي',
            ]
        },
        'interpretation': {
            'name': 'Interpretation of the Music',
            'name_ar': 'تفسير الموسيقى',
            'max_score': 10.0,
            'factor_short': 0.80,
            'factor_free': 1.00,
            'criteria': [
                'ملاءمة الحركات للموسيقى',
                'التعبير عن طابع/مزاج الموسيقى',
                'استخدام التفاصيل الموسيقية',
                'التوقيت الموسيقي الدقيق',
                'الإبداع والشخصية',
            ]
        },
    }

    # ===== الخصومات (Deductions) =====

    DEDUCTIONS: Dict[str, float] = {
        'fall': -1.0,                      # سقوط
        'time_violation': -1.0,            # انتهاك الوقت
        'illegal_element': -2.0,           # عنصر غير قانوني
        'costume_failure': -1.0,           # خلل في الزي
        'music_violation': -1.0,           # انتهاك الموسيقى
        'interruption_brief': -1.0,        # انقطاع قصير
        'interruption_extended': -2.0,     # انقطاع طويل
        'late_start': -1.0,                # بداية متأخرة
    }

    # ===== متطلبات البرامج =====

    PROGRAM_REQUIREMENTS = {
        'senior_men_short': {
            'name': 'Short Program - Senior Men',
            'name_ar': 'البرنامج القصير - رجال متقدمين',
            'duration': 160,  # 2:40 ±10 ثانية
            'required_elements': [
                'قفزة Axel مزدوجة أو ثلاثية',
                'قفزة من القفزات الستة (ليس Axel)',
                'تركيبة قفزات',
                'دوران طائر',
                'دوران',
                'تركيبة دوران',
                'تسلسل خطوات',
            ]
        },
        'senior_women_short': {
            'name': 'Short Program - Senior Women',
            'name_ar': 'البرنامج القصير - سيدات متقدمات',
            'duration': 160,
            'required_elements': [
                'قفزة Axel مزدوجة أو ثلاثية',
                'قفزة من القفزات الستة (ليس Axel)',
                'تركيبة قفزات',
                'دوران طائر',
                'دوران',
                'تركيبة دوران',
                'تسلسل خطوات',
            ]
        },
        'senior_men_free': {
            'name': 'Free Skating - Senior Men',
            'name_ar': 'البرنامج الحر - رجال متقدمين',
            'duration': 250,  # 4:00 ±10 ثانية
            'max_jumps': 8,
            'max_jump_combinations': 3,
            'max_spins': 3,
            'max_step_sequences': 1,
        },
        'senior_women_free': {
            'name': 'Free Skating - Senior Women',
            'name_ar': 'البرنامج الحر - سيدات متقدمات',
            'duration': 250,
            'max_jumps': 7,
            'max_jump_combinations': 3,
            'max_spins': 3,
            'max_step_sequences': 1,
        },
    }

    @staticmethod
    def get_jump_base_value(code: str) -> float:
        """الحصول على القيمة الأساسية للقفزة"""
        jump = ISUStandards.JUMPS.get(code)
        return jump['base_value'] if jump else 0.0

    @staticmethod
    def get_spin_base_value(code: str, level: int) -> float:
        """الحصول على القيمة الأساسية للدوران"""
        spin = ISUStandards.SPINS.get(code)
        if spin and 0 <= level < len(spin['base_values']):
            return spin['base_values'][level]
        return 0.0

    @staticmethod
    def calculate_goe_value(base_value: float, goe: int) -> float:
        """حساب قيمة GOE"""
        if goe not in ISUStandards.GOE_SCALE:
            return 0.0

        percentage = ISUStandards.GOE_VALUES[goe]
        return base_value * percentage

    @staticmethod
    def get_element_info(code: str) -> Dict[str, Any]:
        """الحصول على معلومات العنصر"""
        # البحث في القفزات
        if code in ISUStandards.JUMPS:
            return {
                'type': 'jump',
                **ISUStandards.JUMPS[code]
            }

        # البحث في الدورانات
        spin_code = code[:-1] if code and code[-1].isdigit() else code
        if spin_code in ISUStandards.SPINS:
            level = int(code[-1]) if code and code[-1].isdigit() else 0
            spin_info = ISUStandards.SPINS[spin_code].copy()
            spin_info['base_value'] = spin_info['base_values'][level] if level < len(
                spin_info['base_values']) else 0.0
            return {
                'type': 'spin',
                'level': level,
                **spin_info
            }

        # البحث في تسلسلات الخطوات
        step_code = code[:-1] if code and code[-1].isdigit() else code
        if step_code in ISUStandards.STEP_SEQUENCES:
            level = int(code[-1]) if code and code[-1].isdigit() else 0
            step_info = ISUStandards.STEP_SEQUENCES[step_code].copy()
            step_info['base_value'] = step_info['base_values'][level] if level < len(
                step_info['base_values']) else 0.0
            return {
                'type': 'step_sequence',
                'level': level,
                **step_info
            }

        return None
