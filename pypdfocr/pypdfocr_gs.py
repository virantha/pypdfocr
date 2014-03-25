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
    Wrap ghostscript calls.  Yes, this is ugly.
"""

import subprocess
import sys, os
import logging

def error(text):
    print("ERROR: %s" % text)
    exit(-1)

class PyGs(object):
    """Class to wrap all the ghostscript calls"""
    def __init__(self):
        # Detect windows gs binary (make this smarter in the future)
        if str(os.name) == 'nt':
            self.binary = '"c:\\Program Files (x86)\\gs\\gs9.07\\bin\\gswin32c.exe"'
        else:
            self.binary = "gs"
        self.tiff_dpi = 300
        self.output_dpi = 200
        self.greyscale = True
        # Tiff is used for the ocr, so just fix it at 300dpi
        #  The other formats will be used to create the final OCR'ed image, so determine
        #  the DPI by using pdfimages if available, o/w default to 200
        self.gs_options = {'tiff': ['tiff', ['-sDEVICE=tiff24nc','-r%d' % (self.tiff_dpi)]],
                            'jpg': ['jpg', ['-sDEVICE=jpeg','-dJPEGQ=75', '-r%(dpi)s']],
                            'jpggrey': ['jpg', ['-sDEVICE=jpeggray', '-dJPEGQ=75', '-r%(dpi)s']],
                            'png': ['png', ['-sDEVICE=png16m', '-r%(dpi)s']],
                        }
        self.msgs = {
                'GS_FAILED': 'Ghostscript execution failed',
                'GS_MISSING_PDF': 'Cannot find specified pdf file',
            }

    def _warn(self, msg):
        print("WARNING: %s" % msg)

    def _get_dpi(self, pdf_filename):
        if not os.path.exists(pdf_filename):
            error(self.msgs['GS_MISSING_PDF'] + " %s" % pdf_filename)

        cmd = "pdfimages -list %s" % pdf_filename
        try:
            out = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            self._warn ("Could not execute pdfimages to calculate DPI (try installing xpdf or poppler?), so defaulting to %sdpi" % self.output_dpi) 
	    return

        # Need the second line of output
        results = out.splitlines()[2]
        logging.debug(results)
        results = results.split()
        if(results[2] != 'image'):
            self._warn("Could not understand output of pdfimages, please rerun with -d option and file an issue at http://github.com/virantha/pypdfocr/issues") 
            return
        x_pt, y_pt, greyscale = int(results[3]), int(results[4]), results[5]=='gray'
        self.greyscale = greyscale

        # Now, run imagemagick identify to get pdf width/height/density
        cmd = 'identify -format "%%w %%x %%h %%y\n" %s' % pdf_filename
        try:
            out = subprocess.check_output(cmd, shell=True)
            results = out.splitlines()[0]
            width, xdensity, height, ydensity = [float(x) for x in results.split()]
            xdpi = round(x_pt/width*xdensity)
            ydpi = round(y_pt/height*ydensity)
            self.output_dpi = xdpi
            if xdpi != ydpi:
                if ydpi>xdpi: self.output_dpi = ydpi
                self._warn("X-dpi is %d, Y-dpi is %d, defaulting to %d" % (xdpi, ydpi, self.output_dpi))
            else:
                print("Using %d DPI" % self.output_dpi)


        except Exception as e:
            logging.debug(str(e))
            self._warn ("Could not execute identify to calculate DPI (try installing imagemagick?), so defaulting to %sdpi" % self.output_dpi) 
	    return





    def _run_gs(self, options, output_filename, pdf_filename):
        if str(os.name)=='nt':
            cmd = '%s -q -dNOPAUSE %s -sOutputFile="%s" "%s" -c quit' % (self.binary, options, output_filename, pdf_filename)
            logging.info(cmd)        
            ret = subprocess.call(cmd)
        else:
            cmd = '%s -q -dNOPAUSE %s -sOutputFile="%s" "%s" -c quit' % (self.binary, options, output_filename, pdf_filename)
            logging.debug(cmd)
            ret = os.system(cmd)

        if ret != 0:
            error (self.msgs['GS_FAILED'])

    def make_img_from_pdf(self, pdf_filename, output_format):
        self._get_dpi(pdf_filename)
        # Need tiff for multi-page documents
        if not os.path.exists(pdf_filename):
            error(self.msgs['GS_MISSING_PDF'] + " %s" % pdf_filename)

        filename, filext = os.path.splitext(pdf_filename)
        output_filename = "%s.%s" % (filename, self.gs_options[output_format][0])

        logging.info("Running ghostscript on %s to create %s" % (pdf_filename, output_filename))

        options = ' '.join(self.gs_options[output_format][1])
        self._run_gs(options, output_filename, pdf_filename)

        logging.info("Created %s" % output_filename)

        # Create ancillary jpeg files per page to get around the fact
        # that reportlab doesn't compress PIL images, leading to huge PDFs
        # Instead, we insert the jpeg directly per page
        if self.greyscale:
            self.img_format = 'jpggrey'
        else:
            self.img_format = 'jpg'

        self.img_file_ext = self.gs_options[self.img_format][0]
        options = ' '.join(self.gs_options[self.img_format][1]) % {'dpi':self.output_dpi}
        self._run_gs(options, "%s_%%d.%s" % (filename, self.img_file_ext), pdf_filename)
        return (self.tiff_dpi,output_filename)

