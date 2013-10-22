#!/usr/bin/env python2.7
# Copyright 2013 Virantha Ekanayake All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
    Wrap ghostscript and tesseract to generate OCR'ed pdfs
"""

#from optparse import OptionParser
import argparse
import sys, os
import logging
import shutil

from PIL import Image
from pypdfocr_pdf import PyPdf
from pypdfocr_tesseract import PyTesseract
from pypdfocr_gs import PyGs
from pypdfocr_watcher import PyPdfWatcher

def error(text):
    print("ERROR: %s" % text)
    sys.exit(-1)


class PyPDFOCR(object):

    def __init__ (self):
        self.maxlength = 500
        self.gs = PyGs()
        self.ts = PyTesseract()
        self.pdf = PyPdf()

    def getOptions(self, argv):
        usage = 'python pypdfocr.py '
        p = argparse.ArgumentParser(prog=usage)

        p.add_argument('-d', '--debug', action='store_true',
            default=False, dest='debug', help='Turn on debugging')

        p.add_argument('-v', '--verbose', action='store_true',
            default=False, dest='verbose', help='Turn on verbose mode')

        p.add_argument('-w', '--watch', 
             dest='watch_dir', help='Watch given directory and run ocr automatically until terminated')

        # Positional argument
        p.add_argument("pdf_filename", nargs="?", help="Scanned pdf file to OCR")

        args = p.parse_args(argv)

        self.debug = args.debug
        self.verbose = args.verbose
        self.pdf_filename = args.pdf_filename
        self.watch_dir = args.watch_dir
        
        if self.debug:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')

        if self.verbose:
            logging.basicConfig(level=logging.INFO, format='%(message)s')

        self.watch = False
        if args.watch_dir:
            logging.debug("Starting to watch")
            self.watch = True
        elif not self.pdf_filename:
            p.print_help()
            error("pdf_filename or -w option are required")
    
    def clean_up_files(self, files):
        for file in files:
            try:
                os.remove(file)
            except:
                logging.info("Error removing file %s .... continuing" % file)

            
    def runConversion(self, pdf_filename):
        conversion_format = "tiff"
        tiff_dpi, tiff_filename = self.gs.make_img_from_pdf(pdf_filename, conversion_format)
        hocr_filename = self.ts.make_hocr_from_tiff(tiff_filename)
        
        #hocr_filename = "dmv.hocr.html"
        #tiff_filename = "dmv.tiff"
        pdf_filename = self.pdf.overlay_hocr(tiff_dpi, hocr_filename)
        self.clean_up_files((tiff_filename, hocr_filename))

    def go(self, argv):
        # Read the command line options
        self.getOptions(argv)
        if self.watch:
            py_watcher = PyPdfWatcher(self.watch_dir)
            for pdf_filename in py_watcher.start():
                self.runConversion(pdf_filename)
        else:
            self.runConversion(self.pdf_filename)


if __name__ == '__main__':
    script = PyPDFOCR()
    script.go(sys.argv[1:])


