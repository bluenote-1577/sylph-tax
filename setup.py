from setuptools import setup, find_packages

setup(
    name="sylph-tax",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "requests",
    ],
    scripts=['bin/sylph-tax'],  # This tells setup.py to install your bin script
)
