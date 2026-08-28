# -*- coding: utf-8 -*-
"""
全功能本地化AI智能体大整合框架
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bmad-agno-integration",
    version="1.0.0",
    author="HC20251027",
    author_email="agent@minimax.com",
    description="全功能本地化AI智能体大整合框架",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/minimax/bmad-agno-integration",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.10.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "pre-commit>=3.5.0",
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "visual": [
            "opencv-python>=4.8.0",
            "pillow>=10.0.0",
            "scikit-image>=0.21.0",
            "pytesseract>=0.3.10",
            "mss>=9.0.1",
        ],
        "voice": [
            "SpeechRecognition>=3.10.0",
            "pyaudio>=0.2.11",
            "librosa>=0.10.0",
            "soundfile>=0.12.0",
        ],
        "database": [
            "psycopg2-binary>=2.9.0",
            "sqlalchemy>=2.0.0",
            "alembic>=1.12.0",
            "pgvector>=0.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bmad-agno=bmad_agno_integration.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
