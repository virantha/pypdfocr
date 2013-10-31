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
   Run Tesseract to generate hocr file 
"""

import os, sys
import logging
import subprocess

def error(text):
    print("ERROR: %s" % text)
    sys.exit(-1)

class PyTesseract(object):
    """Class to wrap all the tesseract calls"""
    def __init__(self):
        # Detect windows tesseract location
        if os.name == 'nt':
            self.binary = '"c:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe"'
        else:
            self.binary = "tesseract"

    def make_hocr_from_tiff(self, tiff_filename):
        basename,filext = os.path.splitext(tiff_filename)
        hocr_filename = "%s.html" % basename

        if not os.path.exists(tiff_filename):
            error("Cannot find specified tiff file %s" % (tiff_filename))

        logging.info("Running OCR on %s to create %s.html" % (tiff_filename, basename))
        if os.name == 'nt':
            cmd = '%s "%s" "%s" hocr' % (self.binary, tiff_filename, basename)
            logging.info(cmd)        
            ret = subprocess.call(cmd)
        else:
            cmd = '%s "%s" "%s" hocr' % (self.binary, tiff_filename, basename)
            logging.info(cmd)        
            ret = os.system(cmd)
                
        if ret != 0:
            error ("tesseract execution failed!")
        logging.info("Created %s.html" % basename)

        return hocr_filename

