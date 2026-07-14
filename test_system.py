#!/usr/bin/env python3
"""
نظام اختبار شامل لنظام التزلج
Comprehensive Testing System for Skating Analysis System
"""

import sys
import sqlite3
from pathlib import Path
import importlib.util

class SystemTester:
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }

    def test_database(self):
        """Test database connections and integrity"""
        print("\n🗄️  Testing Databases...")

        databases = ['skating_database.db', 'skating_analysis.db', 'figure_skating.db']
        for db in databases:
            if Path(db).exists():
                try:
                    conn = sqlite3.connect(db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    conn.close()
                    self.results['passed'].append(f"✅ {db}: {len(tables)} tables")
                    print(f"  ✅ {db}: {len(tables)} tables found")
                    for table in tables[:5]:
                        print(f"     - {table[0]}")
                    if len(tables) > 5:
                        print(f"     ... and {len(tables)-5} more")
                except Exception as e:
                    self.results['failed'].append(f"❌ {db}: {str(e)}")
                    print(f"  ❌ {db}: Error - {str(e)}")
            else:
                self.results['warnings'].append(f"⚠️  {db}: Not found")
                print(f"  ⚠️  {db}: File not found")

    def test_python_modules(self):
        """Test if required Python modules can be imported"""
        print("\n📦 Testing Python Modules...")

        modules = [
            'streamlit', 'pandas', 'numpy', 'plotly',
            'cv2', 'mediapipe', 'tensorflow', 'torch',
            'PIL', 'sklearn', 'scipy', 'matplotlib'
        ]

        for module in modules:
            try:
                __import__(module)
                self.results['passed'].append(f"✅ Module: {module}")
                print(f"  ✅ {module}")
            except ImportError:
                self.results['failed'].append(f"❌ Module: {module}")
                print(f"  ❌ {module} - Not installed")

    def test_source_files(self):
        """Test if all source files are valid Python"""
        print("\n📄 Testing Source Files...")

        src_files = list(Path('src').rglob('*.py'))

        for file in src_files:
            try:
                spec = importlib.util.spec_from_file_location("module", file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # Don't execute, just check syntax
                    compile(file.read_text(), file, 'exec')
                    self.results['passed'].append(f"✅ File: {file}")
                    print(f"  ✅ {file.name}")
            except SyntaxError as e:
                self.results['failed'].append(f"❌ File: {file} - Syntax Error")
                print(f"  ❌ {file.name}: Syntax error at line {e.lineno}")
            except Exception as e:
                self.results['warnings'].append(f"⚠️  File: {file} - {str(e)[:50]}")
                print(f"  ⚠️  {file.name}: {str(e)[:50]}")

    def test_data_files(self):
        """Test if data files exist and are readable"""
        print("\n📊 Testing Data Files...")

        data_patterns = [
            '*.xlsx', '*.csv', '*.json', '*.db'
        ]

        for pattern in data_patterns:
            files = list(Path('.').glob(pattern))
            if files:
                print(f"  ✅ Found {len(files)} {pattern} files")
                self.results['passed'].append(f"✅ Data: {len(files)} {pattern} files")
            else:
                print(f"  ⚠️  No {pattern} files found")
                self.results['warnings'].append(f"⚠️  Data: No {pattern} files")

    def test_apps(self):
        """Test if main application files exist and are valid"""
        print("\n🎯 Testing Application Files...")

        apps = ['app.py', 'advanced_app.py', 'professional_app.py']

        for app in apps:
            if Path(app).exists():
                try:
                    compile(Path(app).read_text(), app, 'exec')
                    size = Path(app).stat().st_size / 1024
                    self.results['passed'].append(f"✅ App: {app}")
                    print(f"  ✅ {app} ({size:.1f} KB)")
                except SyntaxError as e:
                    self.results['failed'].append(f"❌ App: {app} - Syntax Error")
                    print(f"  ❌ {app}: Syntax error")
            else:
                self.results['failed'].append(f"❌ App: {app} - Not found")
                print(f"  ❌ {app}: Not found")

    def test_directories(self):
        """Test if required directories exist"""
        print("\n📁 Testing Directory Structure...")

        dirs = ['src', 'data', 'logs', 'scripts', 'tests', '__pycache__']

        for dir_name in dirs:
            if Path(dir_name).exists():
                files = len(list(Path(dir_name).rglob('*')))
                print(f"  ✅ {dir_name}/ ({files} items)")
                self.results['passed'].append(f"✅ Dir: {dir_name}")
            else:
                print(f"  ⚠️  {dir_name}/ - Not found")
                self.results['warnings'].append(f"⚠️  Dir: {dir_name}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)

        print(f"\n✅ PASSED: {len(self.results['passed'])}")
        print(f"❌ FAILED: {len(self.results['failed'])}")
        print(f"⚠️  WARNINGS: {len(self.results['warnings'])}")

        if self.results['failed']:
            print("\n❌ FAILED TESTS:")
            for fail in self.results['failed']:
                print(f"  {fail}")

        if self.results['warnings']:
            print("\n⚠️  WARNINGS:")
            for warn in self.results['warnings'][:10]:
                print(f"  {warn}")
            if len(self.results['warnings']) > 10:
                print(f"  ... and {len(self.results['warnings'])-10} more warnings")

        print("\n" + "="*60)

        # Calculate score
        total = len(self.results['passed']) + len(self.results['failed'])
        if total > 0:
            score = (len(self.results['passed']) / total) * 100
            print(f"📈 OVERALL SCORE: {score:.1f}%")

            if score >= 90:
                print("🎉 EXCELLENT! System is in great shape!")
            elif score >= 70:
                print("👍 GOOD! Minor issues to address.")
            elif score >= 50:
                print("⚠️  FAIR! Several issues need attention.")
            else:
                print("❌ CRITICAL! Major issues found!")

        print("="*60 + "\n")

    def run_all_tests(self):
        """Run all tests"""
        print("="*60)
        print("🎿 SKATING ANALYSIS SYSTEM - COMPREHENSIVE TEST")
        print("="*60)

        self.test_directories()
        self.test_database()
        self.test_apps()
        self.test_source_files()
        self.test_data_files()
        self.test_python_modules()
        self.print_summary()

if __name__ == "__main__":
    tester = SystemTester()
    tester.run_all_tests()
