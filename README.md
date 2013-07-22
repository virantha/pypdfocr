PyOCR
=============

This script will take a pdf file and generate the corresponding OCR'ed version.

Usage: 
------
    python pyocr.py filename.pdf

    --> filename_ocr.pdf will be generated
    

Dependencies:
------------ 

PyOCR relies on the following (free) programs being installed and in the path:
    1. Tesseract OCR software
        - https://code.google.com/p/tesseract-ocr/
    2. GhostScript
        - http://www.ghostscript.com/
    3. PIL (Python Imaging Library)
        - http://www.pythonware.com/products/pil/

On Mac OS X, you can install the first two using homebrew:
    brew install tesseract
    brew install ghostscript

The PIL can be installed using a regular python manager such as pip:
    pip install pil

