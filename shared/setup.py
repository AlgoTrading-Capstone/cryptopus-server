from setuptools import setup, find_packages

setup(
    name="cryptopus-shared",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.26",
        "pandas>=2.0",
        "ta-lib>=0.4.28",
    ],
)