"""
فحص سريع للنظام - Quick System Check
"""
import sys
import subprocess

print("=" * 60)
print("🔍 فحص النظام - System Check")
print("=" * 60)

# Python version
print(f"\n📌 Python Version: {sys.version}")
print(f"   Python Executable: {sys.executable}")

# Check installed packages
print("\n📦 Checking installed packages...")
packages = ['streamlit', 'pandas', 'plotly', 'mediapipe', 'opencv-python', 'numpy', 'tensorflow', 'torch']

for pkg in packages:
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', pkg],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Extract version
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':')[1].strip()
                    print(f"   ✅ {pkg}: {version}")
                    break
        else:
            print(f"   ❌ {pkg}: NOT INSTALLED")
    except Exception as e:
        print(f"   ❌ {pkg}: ERROR - {e}")

# Test imports
print("\n🧪 Testing imports...")
test_packages = {
    'streamlit': 'import streamlit',
    'pandas': 'import pandas',
    'plotly': 'import plotly',
    'mediapipe': 'import mediapipe',
    'cv2': 'import cv2',
    'numpy': 'import numpy',
    'tensorflow': 'import tensorflow',
    'torch': 'import torch'
}

for name, import_cmd in test_packages.items():
    try:
        exec(import_cmd)
        print(f"   ✅ {name}: Can import")
    except ImportError:
        print(f"   ❌ {name}: Cannot import (NOT INSTALLED)")
    except Exception as e:
        print(f"   ⚠️ {name}: Error - {str(e)[:50]}")

print("\n" + "=" * 60)
print("📊 Summary:")
print("=" * 60)
print("\nRun this file and share the output:")
print("   python check_system.py")
print("\n" + "=" * 60)
