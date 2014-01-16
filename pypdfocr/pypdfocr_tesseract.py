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
from subprocess import CalledProcessError
def error(text):
    print("ERROR: %s" % text)
    sys.exit(-1)

class PyTesseract(object):
    """Class to wrap all the tesseract calls"""
    def __init__(self):
        """
           Detect windows tesseract location.  The main script overrides self.binary
           if it is set in the config file
        """
        self.required = "3.02.02"
        if str(os.name) == 'nt':
            # Explicit str here to get around some MagicMock stuff for testing that I don't quite understand
            self.binary = '"c:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe"'
        else:
            self.binary = "tesseract"

        self.msgs = {
            'TS_MISSING': """ 
                Could not execute %s
                Please make sure you have Tesseract installed correctly
                """ % self.binary,
            'TS_VERSION':'Tesseract version is too old',
            'TS_TIFF_MISSING':'Cannot find specified tiff file',
            'TS_FAILED': 'Tesseract-OCR execution failed!',
        }

    def _is_version_uptodate(self):
        """
            Make sure the version is current 
        """
        logging.info("Checking tesseract version")
        cmd = '%s -v' % (self.binary)
        logging.info(cmd)        
        try:
            ret_output = subprocess.check_output(cmd, shell=True,  stderr=subprocess.STDOUT)
        except CalledProcessError:
            # Could not run tesseract
            error(self.msgs['TS_MISSING'])

        ver_str = '0.0.0'
        for line in ret_output.splitlines():
            if 'tesseract' in line:
                ver_str = line.split(' ')[1]

        # Iterate through the version dots
        ver = [int(x) for x in ver_str.split('.')]
        req = [int(x) for x in self.required.split('.')]

        # Aargh, in windows 3.02.02 is reported as version 3.02  
        # SFKM
        if str(os.name) == 'nt':
            req = req[:2]

        version_good = False
        for i,num in enumerate(req):
            if len(ver) < i+1:
                # This minor version number is not present in tesseract, so it must be
                # lower than required.  (3.02 < 3.02.01)
                break
            if ver[i]==num and len(ver) == i+1 and len(ver)==len(req):
                # 3.02.02 == 3.02.02
                version_good = True
                continue
            if ver[i]>num:
                # 4.0 > 3.02.02
                # 3.03.02 > 3.02.02
                version_good = True
                break
            if ver[i]<num:
                # 3.01.02 < 3.02.02
                break
            
        return version_good, ver_str



    def make_hocr_from_tiff(self, tiff_filename):
        uptodate,ver =  self._is_version_uptodate()
        if not uptodate:
            error(self.msgs['TS_VERSION']+ " (found %s, required %s)" % (ver, self.required))

        basename,filext = os.path.splitext(tiff_filename)
        hocr_filename = "%s.html" % basename

        if not os.path.exists(tiff_filename):
            error(self.msgs['TS_TIFF_MISSING'] + " %s" % (tiff_filename))

        logging.info("Running OCR on %s to create %s.html" % (tiff_filename, basename))
        if str(os.name) == 'nt':
            cmd = '%s "%s" "%s" hocr' % (self.binary, tiff_filename, basename)
            logging.info(cmd)        
            ret = subprocess.call(cmd)
        else:
            cmd = '%s "%s" "%s" hocr' % (self.binary, tiff_filename, basename)
            logging.info(cmd)        
            ret = os.system(cmd)
                
        if ret != 0:
            error (self.msgs['TS_FAILED'])
        logging.info("Created %s.html" % basename)

        return hocr_filename

