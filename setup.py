
from setuptools import setup, find_packages

setup(
    name="seleniumfw",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        # Change key to match your CLI package folder name
        "sfw": ["templates/project/**/*"],
    },
    install_requires=[
        "typer",
        "jinja2",
        "python-dotenv",
        "PyYAML",
        "selenium",
        "behave",
        "reportlab",
        "flask",
        "requests",
        "apscheduler",
    ],
    entry_points={
        "console_scripts": [
            "sfw=sfw.cli:app",
        ],
    },
)