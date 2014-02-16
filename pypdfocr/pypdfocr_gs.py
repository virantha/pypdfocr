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
    Wrap ghostscript calls
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
        self.gs_options = {'tiff': ['-sDEVICE=tiff24nc','-r%d' % (self.tiff_dpi)],
                            'jpg': ['-sDEVICE=jpeg','-dJPEGQ=75', '-r200']
                        }
        self.msgs = {
                'GS_FAILED': 'Ghostscript execution failed',
                'GS_MISSING_PDF': 'Cannot find specified pdf file',
            }

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
        # Need tiff for multi-page documents
        if not os.path.exists(pdf_filename):
            error(self.msgs['GS_MISSING_PDF'] + " %s" % pdf_filename)

        filename, filext = os.path.splitext(pdf_filename)
        output_filename = "%s.%s" % (filename, output_format)

        logging.info("Running ghostscript on %s to create %s" % (pdf_filename, output_filename))

        options = ' '.join(self.gs_options[output_format])
        self._run_gs(options, output_filename, pdf_filename)

        logging.info("Created %s" % output_filename)

        # Create ancillary jpeg files per page to get around the fact
        # that reportlab doesn't compress PIL images, leading to huge PDFs
        # Instead, we insert the jpeg directly per page
        options = ' '.join(self.gs_options['jpg'])
        self._run_gs(options, "%s_%%d.jpg" % filename, pdf_filename)
        return (self.tiff_dpi,output_filename)

