#!/usr/bin/env python3
"""
مثال بسيط لنظام تحليل التزلج الفني
يعمل بدون تثبيت مكتبات إضافية
"""

print("\n" + "="*60)
print("   🏒 نظام تحليل التزلج الفني - النسخة التجريبية")
print("="*60)

# معايير ISU الكاملة
JUMPS = {
    # Single
    '1A': {'name_ar': 'أكسل مفرد', 'base': 1.10},
    '1Lz': {'name_ar': 'لوتز مفرد', 'base': 0.60},
    '1F': {'name_ar': 'فليب مفرد', 'base': 0.50},

    # Double
    '2A': {'name_ar': 'أكسل مزدوج', 'base': 3.30},
    '2Lz': {'name_ar': 'لوتز مزدوج', 'base': 2.10},
    '2F': {'name_ar': 'فليب مزدوج', 'base': 1.80},

    # Triple
    '3A': {'name_ar': 'أكسل ثلاثي', 'base': 8.00},
    '3Lz': {'name_ar': 'لوتز ثلاثي', 'base': 5.90},
    '3F': {'name_ar': 'فليب ثلاثي', 'base': 5.30},
    '3Lo': {'name_ar': 'لووب ثلاثي', 'base': 4.90},
    '3S': {'name_ar': 'سالكو ثلاثي', 'base': 4.30},
    '3T': {'name_ar': 'تو لووب ثلاثي', 'base': 4.20},

    # Quad
    '4A': {'name_ar': 'أكسل رباعي', 'base': 12.50},
    '4Lz': {'name_ar': 'لوتز رباعي', 'base': 11.50},
    '4T': {'name_ar': 'تو لووب رباعي', 'base': 9.50},
}

GOE_VALUES = {
    -5: -0.50, -4: -0.40, -3: -0.30, -2: -0.20, -1: -0.10,
    0: 0.00,
    1: 0.10, 2: 0.20, 3: 0.30, 4: 0.40, 5: 0.50
}

def analyze_program():
    """تحليل برنامج كامل"""

    print("\n📝 أدخل عناصر البرنامج:")
    print("   (مثال: 3A 2 للقفزة Triple Axel مع GOE +2)")
    print("   اكتب 'done' عند الانتهاء\n")

    elements = []
    while True:
        inp = input("   عنصر: ").strip()
        if inp.lower() == 'done':
            break
        if not inp:
            continue

        parts = inp.split()
        if len(parts) == 2:
            code, goe = parts[0], int(parts[1])
            if code in JUMPS and -5 <= goe <= 5:
                elements.append((code, goe))
            else:
                print("   ⚠️  عنصر غير صحيح!")

    if not elements:
        # استخدم برنامج تجريبي
        print("\n   ✓ استخدام برنامج تجريبي...")
        elements = [
            ('4T', 2), ('3A', 3), ('3Lz', 1),
            ('3F', 1), ('3Lo', 0), ('2A', 2)
        ]

    # حساب الدرجة التقنية
    print("\n" + "-"*60)
    print("📊 تحليل العناصر:")
    print("-"*60)

    total_base = 0
    total_goe = 0

    for i, (code, goe) in enumerate(elements, 1):
        jump = JUMPS[code]
        base = jump['base']
        goe_val = base * GOE_VALUES[goe]
        total = base + goe_val

        total_base += base
        total_goe += goe_val

        print(f"\n{i}. {jump['name_ar']} ({code})")
        print(f"   القيمة الأساسية: {base:.2f}")
        print(f"   GOE: {goe:+d} ({goe_val:+.2f})")
        print(f"   المجموع: {total:.2f}")

    tech_score = total_base + total_goe

    # درجات المكونات
    print("\n" + "="*60)
    print("🎨 المكونات البرنامجية:")
    print("-"*60)

    components = {
        'مهارات التزلج': 8.75,
        'الانتقالات': 8.50,
        'الأداء': 9.00,
        'التكوين': 8.25,
        'التفسير': 9.25
    }

    for name, score in components.items():
        print(f"   {name:20s}: {score:.2f}")

    comp_score = sum(components.values()) / len(components)

    # الدرجة النهائية
    print("\n" + "="*60)
    print("🏆 النتيجة النهائية:")
    print("="*60)
    print(f"   الدرجة التقنية: {tech_score:.2f}")
    print(f"   درجة المكونات: {comp_score:.2f}")
    print(f"   المجموع: {tech_score + comp_score:.2f}")
    print("="*60 + "\n")

def show_isu_standards():
    """عرض معايير ISU"""
    print("\n📖 معايير ISU للقفزات:")
    print("-"*60)

    categories = {
        'Single (مفرد)': ['1A', '1Lz', '1F'],
        'Double (مزدوج)': ['2A', '2Lz', '2F'],
        'Triple (ثلاثي)': ['3A', '3Lz', '3F', '3Lo', '3S', '3T'],
        'Quad (رباعي)': ['4A', '4Lz', '4T']
    }

    for cat, codes in categories.items():
        print(f"\n{cat}:")
        for code in codes:
            jump = JUMPS[code]
            print(f"  {code:4s} - {jump['name_ar']:20s} {jump['base']:.2f}")

def main():
    """القائمة الرئيسية"""
    while True:
        print("\n📋 القائمة:")
        print("   1. تحليل برنامج")
        print("   2. عرض معايير ISU")
        print("   3. خروج")

        choice = input("\nاختر (1-3): ").strip()

        if choice == '1':
            analyze_program()
        elif choice == '2':
            show_isu_standards()
        elif choice == '3':
            print("\n✨ شكراً لاستخدام النظام!\n")
            break
        else:
            print("⚠️  اختيار غير صحيح!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✨ تم إيقاف البرنامج\n")
