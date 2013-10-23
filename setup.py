from __future__ import print_function
from setuptools import setup, find_packages

import pypdfocr
from pypdfocr.version import __version__

with open('README.rst') as file:
        long_description = file.read()

packages = find_packages(exclude="tests")
setup (
    name = "pypdfocr",
    version = __version__,
    description="Converts a scanned PDF into an OCR'ed pdf using Tesseract-OCR and Ghostscript",
    license = "LICENSE",
    long_description = long_description,
    author="Virantha N. Ekanayake",
    author_email="virantha@gmail.com", # Removed.
    package_data = {'': ['*.xml']},
    zip_safe = True,
    packages = packages,
    install_requires = [ 'pil>=1.1.7', 'reportlab>=2.7', "watchdog>=0.6.0" ],
    entry_points = {
            'console_scripts': [
                    'pypdfocr = pypdfocr.pypdfocr:main'
                ],
        },
    options = {
	    "pyinstaller": {"packages": packages}
	    }

)
