from __future__ import print_function
from setuptools import setup, find_packages

import pypdfocr
import io
from pypdfocr.version import __version__


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

packages = find_packages(exclude="tests")

long_description = read('README.rst', 'CHANGES.rst', 'TODO.rst')

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup (
    name = "pypdfocr",
    version = __version__,
    description="Converts a scanned PDF into an OCR'ed pdf using Tesseract-OCR and Ghostscript",
    license = "ASL 2.0",
    long_description = long_description,
    author="Virantha N. Ekanayake",
    author_email="virantha@gmail.com", # Removed.
    package_data = {'': ['*.xml']},
    zip_safe = True,
    include_package_data = True,
    packages = packages,
    install_requires = required,
    entry_points = {
            'console_scripts': [
                    'pypdfocr = pypdfocr.pypdfocr:main'
                ],
        },
    options = {
	    "pyinstaller": {"packages": packages}
	    }

)
