#!/usr/bin/env python3
"""
Setup script for NANDA Agent Framework
"""

from setuptools import setup, find_packages
import os

# Read the requirements
def read_requirements(filename):
    """Read requirements from file"""
    requirements = []
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return requirements

# Read the README for long description
def read_readme():
    """Read README file for long description"""
    if os.path.exists('README.md'):
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    return "NANDA Agent Framework - Customizable AI Agent Communication System"

setup(
    name="nanda-adapter",
    version="1.0.2",
    description="Customizable AI Agent Communication Framework with pluggable message improvement logic",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="NANDA Team",
    author_email="support@nanda.ai",
    url="https://github.com/projnanda/adapter.git",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "flask",
        "anthropic",
        "requests",
        "python-a2a==0.5.6",
        "mcp",
        "python-dotenv",
        "flask-cors",
        "pymongo"
    ],
    extras_require={
        "langchain": ["langchain-core", "langchain-anthropic"],
        "crewai": ["crewai", "langchain-anthropic"],
        "all": ["langchain-core", "langchain-anthropic", "crewai"]
    },
    entry_points={
        "console_scripts": [
            "nanda-adapter=nanda_adapter.cli:main"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="nanda ai agent framework",
    include_package_data=True,
    zip_safe=False,
)