"""
Setup script for the SOC 2 Report Analysis Tool.
"""

from setuptools import setup, find_packages

setup(
    name="soc2_analyzer",
    version="1.0.0",
    description="A tool for analyzing SOC 2 reports using AWS services",
    author="Your Organization",
    author_email="info@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "boto3>=1.26.0",
        "pytest>=7.0.0",
        "pytest-mock>=3.10.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
) 