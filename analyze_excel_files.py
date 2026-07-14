#!/usr/bin/env python3
"""
سكريبت لتحليل ملفات Excel واستخراج أسماء اللاعبين والمدربين
"""
import pandas as pd
import os
import json
from pathlib import Path

def analyze_excel_file(file_path):
    """تحليل ملف Excel واحد"""
    print(f"\n{'='*80}")
    print(f"📄 تحليل: {os.path.basename(file_path)}")
    print(f"{'='*80}")

    try:
        # قراءة جميع الأوراق
        excel_file = pd.ExcelFile(file_path)
        print(f"📋 الأوراق: {', '.join(excel_file.sheet_names)}")

        results = {
            'file': os.path.basename(file_path),
            'sheets': {},
            'players': set(),
            'coaches': set(),
            'all_names': set()
        }

        for sheet_name in excel_file.sheet_names:
            print(f"\n  📑 ورقة: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            print(f"    الصفوف: {len(df)}, الأعمدة: {len(df.columns)}")
            print(f"    أسماء الأعمدة: {list(df.columns)}")

            # عرض أول 3 صفوف
            if len(df) > 0:
                print(f"\n    أول 3 صفوف:")
                print(df.head(3).to_string(index=False))

            results['sheets'][sheet_name] = {
                'rows': len(df),
                'columns': list(df.columns),
                'data': df.head(10).to_dict('records')
            }

            # البحث عن أسماء في الأعمدة
            name_columns = [col for col in df.columns if any(keyword in str(col).lower()
                           for keyword in ['name', 'اسم', 'player', 'لاعب', 'skater', 'متزلج', 'coach', 'مدرب'])]

            for col in name_columns:
                names = df[col].dropna().unique()
                for name in names:
                    if isinstance(name, str) and len(name) > 2:
                        results['all_names'].add(name)

                        # تصنيف الأسماء
                        col_lower = str(col).lower()
                        if any(k in col_lower for k in ['coach', 'مدرب', 'trainer']):
                            results['coaches'].add(name)
                        elif any(k in col_lower for k in ['player', 'لاعب', 'skater', 'متزلج', 'name', 'اسم']):
                            results['players'].add(name)

        # طباعة النتائج
        if results['players']:
            print(f"\n  👥 اللاعبين المكتشفين ({len(results['players'])}):")
            for player in sorted(results['players']):
                print(f"    - {player}")

        if results['coaches']:
            print(f"\n  🎓 المدربين المكتشفين ({len(results['coaches'])}):")
            for coach in sorted(results['coaches']):
                print(f"    - {coach}")

        if results['all_names'] and not results['players'] and not results['coaches']:
            print(f"\n  📝 أسماء أخرى ({len(results['all_names'])}):")
            for name in sorted(results['all_names'])[:20]:  # أول 20 اسم
                print(f"    - {name}")

        return results

    except Exception as e:
        print(f"  ❌ خطأ: {e}")
        return None

def main():
    """تحليل جميع ملفات Excel"""
    print("🔍 بدء تحليل ملفات Excel...")

    # البحث عن جميع ملفات Excel
    excel_files = list(Path('.').glob('*.xlsx')) + list(Path('.').glob('*.xls'))

    print(f"\n📊 تم العثور على {len(excel_files)} ملف")

    all_players = set()
    all_coaches = set()
    all_results = []

    for file_path in sorted(excel_files):
        result = analyze_excel_file(str(file_path))
        if result:
            all_results.append(result)
            all_players.update(result['players'])
            all_coaches.update(result['coaches'])

    # الملخص النهائي
    print(f"\n\n{'='*80}")
    print("📊 الملخص النهائي")
    print(f"{'='*80}")
    print(f"✅ عدد الملفات المحللة: {len(all_results)}")
    print(f"👥 إجمالي اللاعبين: {len(all_players)}")
    print(f"🎓 إجمالي المدربين: {len(all_coaches)}")

    if all_players:
        print(f"\n👥 قائمة جميع اللاعبين ({len(all_players)}):")
        for i, player in enumerate(sorted(all_players), 1):
            print(f"  {i}. {player}")

    if all_coaches:
        print(f"\n🎓 قائمة جميع المدربين ({len(all_coaches)}):")
        for i, coach in enumerate(sorted(all_coaches), 1):
            print(f"  {i}. {coach}")

    # حفظ النتائج في JSON
    output = {
        'total_files': len(all_results),
        'players': sorted(list(all_players)),
        'coaches': sorted(list(all_coaches)),
        'files_details': [{
            'file': r['file'],
            'players': sorted(list(r['players'])),
            'coaches': sorted(list(r['coaches']))
        } for r in all_results]
    }

    with open('extracted_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n💾 تم حفظ النتائج في: extracted_data.json")

if __name__ == "__main__":
    main()
