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

from optparse import OptionParser
import sys, os
import logging

from pyocr_pdf import PyPdf
from pyocr_tesseract import PyTesseract
from pyocr_gs import PyGs

def error(text):
    print("ERROR: %s" % text)
    exit(-1)


class PyOCR(object):

    def __init__ (self):
        self.maxlength = 500
        self.gs = PyGs()
        self.ts = PyTesseract()
        self.pdf = PyPdf()

    def getOptions(self, argv):
        usage = 'pyocr [options] pdf_file'
        p = OptionParser(usage)

        p.add_option('-d', '--debug', action='store_true',
            default=False, dest='debug', help='Turn on debugging')

        p.add_option('-v', '--verbose', action='store_true',
            default=False, dest='verbose', help='Turn on verbose mode')


        (opt, args) = p.parse_args(argv)

        self.debug = opt.debug
        self.verbose = opt.verbose
        
        if len(args) != 1:
            error(usage)
        else:
            self.pdf_filename = args[0]

        if opt.debug:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')

        if opt.verbose:
            logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    def clean_up_files(self, files):
        for file in files:
            try:
                os.remove(file)
            except:
                logging.info("Error removing file %s .... continuing" % file)

    def go(self, argv):
        # Read the command line options
        self.getOptions(argv)
        conversion_format = "tiff"

        tiff_filename = self.gs.make_img_from_pdf(self.pdf_filename, conversion_format)
        hocr_filename = self.ts.make_hocr_from_tiff(tiff_filename)
        
        #hocr_filename = "dmv.hocr.html"
        #tiff_filename = "dmv.tiff"
        im = Image.open(tiff_filename)
        pdf_filename = self.pdf.overlay_hocr(im, hocr_filename)
        self.clean_up_files((tiff_filename, hocr_filename))

if __name__ == '__main__':
    script = PyOCR()
    script.go(sys.argv[1:])


