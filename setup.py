from __future__ import print_function
from setuptools import setup, find_packages

import pypdfocr

with open('README.md') as file:
        long_description = file.read()

setup (
    name = "pypdfocr",
    version = pypdfocr.__version__,
    description="Converts a scanned PDF into an OCR'ed pdf using Tesseract-OCR and Ghostscript",
    long_description = long_description,
    author="Virantha N. Ekanayake",
    author_email="virantha@gmail.com", # Removed.
    package_data = {'': ['*.xml']},
    packages = find_packages(exclude="tests"),
    zip_safe = True,
    install_requires = [ 'pil>=1.1.7', 'reportlab>=2.7' ]
)
