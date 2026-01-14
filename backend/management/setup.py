from setuptools import setup, find_packages

setup(
    name="codeclarity-ai",
    version="1.0.0",
    description="AI-Powered Repository Analysis Tool",
    author="CodeClarity Team",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.28.0",
        "gitpython>=3.1.37",
        "pandas>=2.1.1",
        "plotly>=5.17.0",
        "requests>=2.31.0",
        "python-dateutil>=2.8.2",
        "sentence-transformers>=2.2.2",
        "numpy>=1.24.3",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "codeclarity=streamlit_app:main",
        ],
    },
)
