"""
إعداد الحزمة
"""
from setuptools import setup, find_packages
from pathlib import Path

# قراءة README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="yasooo-skating-analysis",
    version="1.0.0",
    author="Elmansoory",
    author_email="support@example.com",
    description="نظام متقدم لتحليل التزلج الفني باستخدام الذكاء الاصطناعي",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elmansoory/yasooo",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "streamlit>=1.28.0",
        "opencv-python>=4.8.0",
        "mediapipe>=0.10.8",
        "tensorflow>=2.14.0",
        "numpy>=1.24.0",
        "pandas>=2.1.0",
        "sqlalchemy>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.9.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "yasooo=app:main",
        ],
    },
)
