from setuptools import setup, find_packages
from sylph_tax.version import __version__

setup(
    name="sylph-tax",
    version=__version__,
    packages=find_packages(),
    install_requires=[
        "pandas",
        "requests",
    ],
    scripts=['bin/sylph-tax'],  # This tells setup.py to install your bin script
)
