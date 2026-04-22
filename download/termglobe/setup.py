from setuptools import setup, find_packages

setup(
    name="termglobe",
    version="0.1.0",
    description="Lightweight 3D ASCII globe renderer for terminal",
    author="Z.ai",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "termglobe=termglobe.cli_adapter:main",
        ],
    },
    python_requires=">=3.8",
)
