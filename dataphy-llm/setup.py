"""Phy-LLM 项目 Setup 脚本"""
from setuptools import setup, find_packages

setup(
    name='phy-llm',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pyarrow>=10.0',
        'duckdb>=0.9.0',
    ],
    python_requires='>=3.14',
)
