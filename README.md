# PyPDFOCR

This script will take a pdf file and generate the corresponding OCR'ed version.

## Usage: 
### Single conversion:
    python pypdfocr.py filename.pdf

    --> filename_ocr.pdf will be generated

### Folder monitoring (new!):
    python pypdfocr.py -w watch_directory

    --> Every time a pdf file is added to `watch_directory` it will be OCR'ed
    
For those on Windows, because it's such a pain to get all the PIL and PDF
dependencies installed, I've gone ahead and made an executable available under:

    dist/pypdfocr.exe

You still need to install Tesseract and GhostScript as detailed below in the dependencies
list.

## Caveats
This code is brand-new, and is barely commented with no unit-tests included.  I plan to improve 
things as time allows in the near-future.

## Dependencies:
PyPDFOCR relies on the following (free) programs being installed and in the path:
- Tesseract OCR software https://code.google.com/p/tesseract-ocr/
- GhostScript http://www.ghostscript.com/
- PIL (Python Imaging Library) http://www.pythonware.com/products/pil/
- ReportLab (PDF generation library) http://www.reportlab.com/software/opensource/
- Watchdog (Cross-platform fhlesystem events monitoring) https://pypi.python.org/pypi/watchdog

On Mac OS X, you can install the first two using homebrew:

    brew install tesseract
    brew install ghostscript

The last three can be installed using a regular python manager such as pip:

    pip install pil
    pip install reportlab
    pip install watchdog
