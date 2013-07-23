PyPDFOCR
=============

This script will take a pdf file and generate the corresponding OCR'ed version.

Usage: 
------
    python pypdfocr.py filename.pdf

    --> filename_ocr.pdf will be generated
    

Caveats
-------
This code is brand-new, and is barely commented with no unit-tests included.  I plan to improve 
things as time allows in the near-future.

Dependencies:
------------ 

PyPDFOCR relies on the following (free) programs being installed and in the path:
- Tesseract OCR software https://code.google.com/p/tesseract-ocr/
- GhostScript http://www.ghostscript.com/
- PIL (Python Imaging Library) http://www.pythonware.com/products/pil/
- ReportLab (PDF generation library) http://www.reportlab.com/software/opensource/

On Mac OS X, you can install the first two using homebrew:

    brew install tesseract
    brew install ghostscript

The last two can be installed using a regular python manager such as pip:

    pip install pil
    pip install reportlab

