# setup.py
from setuptools import setup, find_packages

setup(
    name="wac2j",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "colorlog==6.8.2",
        "openai==1.51.0",
        "pydantic==2.9.2",
        "python-dotenv==1.0.1",
        "ratelimit==2.2.1",
        "setuptools==65.5.0",
        "tabulate==0.9.0",
        "tqdm==4.66.4"

    ],
    entry_points={
        "console_scripts": [
            "wac2j=src.__main__:main",
        ],
    },
)