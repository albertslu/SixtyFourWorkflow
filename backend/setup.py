"""
Setup script for the SixtyFour Workflow Engine backend
"""
from setuptools import setup, find_packages

setup(
    name="sixtyfour-workflow-backend",
    version="1.0.0",
    description="Backend for SixtyFour Workflow Engine",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pandas>=2.1.3",
        "numpy>=1.25.2",
        "httpx>=0.25.2",
        "requests>=2.31.0",
        "python-multipart>=0.0.6",
        "aiofiles>=23.2.1",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "celery>=5.3.4",
        "redis>=5.0.1",
        "loguru>=0.7.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
        ]
    },
)
