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
import glob
from subprocess import CalledProcessError

from multiprocessing import Pool
from pypdfocr_interrupts import init_worker

def error(text):
    print("ERROR: %s" % text)
    sys.exit(-1)

# Ugly hack to pass in object method to the multiprocessing library
# From http://www.rueckstiess.net/research/snippets/show/ca1d7d90
# Basically gets passed in a pair of (self, arg), and calls the method
def unwrap_self(arg, **kwarg):
    return PyTesseract.make_hocr_from_pnm(*arg, **kwarg)

class PyTesseract(object):
    """Class to wrap all the tesseract calls"""
    def __init__(self, config):
        """
           Detect windows tesseract location.  
        """
        self.lang = 'eng'
        self.required = "3.02.02"
        self.threads = config.get('threads',4)

        if "binary" in config:  # Override location of binary
            binary = config['binary']
            if os.name == 'nt':
                binary = '"%s"' % binary
                binary = binary.replace("\\", "\\\\")
            logging.info("Setting location for tesseracdt executable to %s" % (binary))
        else:
            if str(os.name) == 'nt':
                # Explicit str here to get around some MagicMock stuff for testing that I don't quite understand
                binary = '"c:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe"'
            else:
                binary = "tesseract"

        self.binary = binary

        self.msgs = {
            'TS_MISSING': """ 
                Could not execute %s
                Please make sure you have Tesseract installed correctly
                """ % self.binary,
            'TS_VERSION':'Tesseract version is too old',
            'TS_img_MISSING':'Cannot find specified tiff file',
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
                if ver_str.endswith('dev'): # Fix for version strings that end in 'dev'
                    ver_str = ver_str[:-3]

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

    def _warn(self, msg): # pragma: no cover
        print("WARNING: %s" % msg)


    def make_hocr_from_pnms(self, fns):
        uptodate,ver =  self._is_version_uptodate()
        if not uptodate:
            error(self.msgs['TS_VERSION']+ " (found %s, required %s)" % (ver, self.required))

        # Glob it
        #fns = glob.glob(img_filename)
        logging.debug("Making pool for tesseract")
        pool = Pool(processes=self.threads, initializer=init_worker)

        try:
            hocr_filenames = pool.map(unwrap_self, zip([self]*len(fns), fns))
            pool.close()
        except KeyboardInterrupt or Exception:
            print("Caught keyboard interrupt... terminating")
            pool.terminate()
            raise
        finally:
            pool.join()

        return zip(fns,hocr_filenames)


    def make_hocr_from_pnm(self, img_filename):

        basename,filext = os.path.splitext(img_filename)
        hocr_filename = "%s.html" % basename

        if not os.path.exists(img_filename):
            error(self.msgs['TS_img_MISSING'] + " %s" % (img_filename))

        logging.info("Running OCR on %s to create %s.html" % (img_filename, basename))
        cmd = '%s "%s" "%s" -psm 1 -c hocr_font_info=1 -l %s hocr' % (self.binary, img_filename, basename, self.lang)
        logging.info(cmd)
        try:
            ret_output = subprocess.check_output(cmd, shell=True,  stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            # Could not run tesseract
            print e.output
            self._warn (self.msgs['TS_FAILED'])
                
        if os.path.isfile(hocr_filename):
            # Output format is html for old versions of tesseract
            logging.info("Created %s.html" % basename)
            return hocr_filename
        else:
            # Try changing extension to .hocr for tesseract 3.03 and higher
            hocr_filename = "%s.hocr" % basename
            if os.path.isfile(hocr_filename):
                logging.info("Created %s.hocr" % basename)
                return hocr_filename
            else:
                error(self.msgs['TS_FAILED'])
            
