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
import glob

def error(text):
    print("ERROR: %s" % text)
    exit(-1)

class PyGs(object):
    """Class to wrap all the ghostscript calls"""

    def __init__(self, config):
        self.msgs = {
                'GS_FAILED': 'Ghostscript execution failed',
                'GS_MISSING_PDF': 'Cannot find specified pdf file',
                'GS_OUTDATED': 'Your Ghostscript version is probably out of date.  Please upgrade to the latest version',
                'GS_MISSING_BINARY': 'Could not find Ghostscript in the usual place; please specify it using your config file',
            }
        self.threads = config.get('threads',4)

        if "binary" in config:  # Override location of binary
            binary = config['binary']
            if os.name == 'nt':
                binary = '"%s"' % binary
                binary = binary.replace("\\", "\\\\")
            logging.info("Setting location for executable to %s" % (binary))
        else:
            if str(os.name) == 'nt':
                win_binary = self._find_windows_gs()
                binary = '"%s"' % win_binary
                logging.info("Using Ghostscript: %s" % binary)
            else:
                binary = "gs"
        self.binary = binary

        #self.tiff_dpi = 300
        self.output_dpi = 300
        self.greyscale = True
        # Tiff is used for the ocr, so just fix it at 300dpi
        #  The other formats will be used to create the final OCR'ed image, so determine
        #  the DPI by using pdfimages if available, o/w default to 200
        self.gs_options = {'tiff': ['tiff', ['-sDEVICE=tiff24nc','-r%(dpi)s' ]],
                            'jpg': ['jpg', ['-sDEVICE=jpeg','-dJPEGQ=75', '-r%(dpi)s']],
                            'jpggrey': ['jpg', ['-sDEVICE=jpeggray', '-dJPEGQ=75', '-r%(dpi)s']],
                            'png': ['png', ['-sDEVICE=png16m', '-r%(dpi)s']],
                            'pnggrey': ['png', ['-sDEVICE=pngmono', '-r%(dpi)s']],
                            'tifflzw': ['tiff', ['-sDEVICE=tifflzw', '-r%(dpi)s']],
                            'tiffg4': ['tiff', ['-sDEVICE=tiffg4', '-r%(dpi)s']],
                            'pnm': ['pnm', ['-sDEVICE=pnmraw', '-r%(dpi)s']],
                            'pgm': ['pgm', ['-sDEVICE=pgm', '-r%(dpi)s']],
                        }

    def _find_windows_gs(self):
        """
            Searches through the Windows program files directories to find Ghostscript.
            If it finds multiple versions, it does a naive sort for now to find the most
            recent.

            :rval: The ghostscript binary location

        """
        windirs = ["c:\\Program Files\\gs", "c:\\Program Files (x86)\\gs"]
        gs = None
        for d in windirs:
            if not os.path.exists(d):
                continue
            cwd = os.getcwd()
            os.chdir(d)
            listing = os.listdir('.')

            # Find all possible gs* sub-directories
	    listing = [x for x in listing if x.startswith('gs')]

            # TODO: Make this a natural sort
            listing.sort(reverse=True)
	    for bindir in listing:
		binpath = os.path.join(bindir,'bin')
		if not os.path.exists(binpath): continue
		os.chdir(binpath)
                # Look for gswin64c.exe or gswin32c.exe (the c is for the command-line version)
		gswin = glob.glob('gswin*c.exe')
		if len(gswin) == 0:
		    continue
		gs = os.path.abspath(gswin[0]) # Just use the first found .exe (Do i need to do anything more complicated here?)
		os.chdir(cwd)
		return gs

        if not gs:
            error(self.msgs['GS_MISSING_BINARY'])

    def _warn(self, msg):
        print("WARNING: %s" % msg)

    def _get_dpi(self, pdf_filename):
        if not os.path.exists(pdf_filename):
            error(self.msgs['GS_MISSING_PDF'] + " %s" % pdf_filename)

        cmd = 'pdfimages -list "%s"' % pdf_filename
        logging.info("Running pdfimages to figure out DPI...")
        logging.debug(cmd)
        try:
            out = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            self._warn ("Could not execute pdfimages to calculate DPI (try installing xpdf or poppler?), so defaulting to %sdpi" % self.output_dpi) 
            return

        # Need the second line of output
        # Make sure it exists (in case this is an empty pdf)
        results = out.splitlines()
        if len(results)<3:
            self._warn("Empty pdf, cannot determine dpi using pdfimages")
            return
        results = results[2]
        logging.debug(results)
        results = results.split()
        if(results[2] != 'image'):
            self._warn("Could not understand output of pdfimages, please rerun with -d option and file an issue at http://github.com/virantha/pypdfocr/issues") 
            return
        x_pt, y_pt, greyscale = int(results[3]), int(results[4]), results[5]=='gray'
        self.greyscale = greyscale

        # Now, run imagemagick identify to get pdf width/height/density
        cmd = 'identify -format "%%w %%x %%h %%y\n" "%s"' % pdf_filename
        try:
            out = subprocess.check_output(cmd, shell=True)
            results = out.splitlines()[0]
            results = results.replace("Undefined", "")
            width, xdensity, height, ydensity = [float(x) for x in results.split()]
            xdpi = round(x_pt/width*xdensity)
            ydpi = round(y_pt/height*ydensity)
            self.output_dpi = xdpi
            if ydpi>xdpi: self.output_dpi = ydpi
            if self.output_dpi < 300: self.output_dpi = 300
            if abs(xdpi-ydpi) > xdpi*.05:  # Make sure the two dpi's are within 5%
                self._warn("X-dpi is %d, Y-dpi is %d, defaulting to %d" % (xdpi, ydpi, self.output_dpi))
            else:
                print("Using %d DPI" % self.output_dpi)


        except Exception as e:
            logging.debug(str(e))
            self._warn ("Could not execute identify to calculate DPI (try installing imagemagick?), so defaulting to %sdpi" % self.output_dpi) 
        return



    def _run_gs(self, options, output_filename, pdf_filename):
        try:
            cmd = '%s -q -dNOPAUSE %s -sOutputFile="%s" "%s" -c quit' % (self.binary, options, output_filename, pdf_filename)
            logging.info(cmd)        
            out = subprocess.check_output(cmd, shell=True)

        except subprocess.CalledProcessError as e:
            print e.output
            if "undefined in .getdeviceparams" in e.output:
                error(self.msgs['GS_OUTDATED'])
            else:
                error (self.msgs['GS_FAILED'])


    def make_img_from_pdf(self, pdf_filename):
        self._get_dpi(pdf_filename) # No need to bother anymore

        if not os.path.exists(pdf_filename):
            error(self.msgs['GS_MISSING_PDF'] + " %s" % pdf_filename)

        filename, filext = os.path.splitext(pdf_filename)


        # Create ancillary jpeg files to use later to calculate image dpi etc
        #   We no longer use these for the final image. Instead the text is merged
        #   directly with the original PDF.  Yay!
        if self.greyscale:
            self.img_format = 'jpggrey'
            #self.img_format = 'pnggrey'
            logging.info("Detected greyscale")
        else:
            self.img_format = 'jpg'
            #self.img_format = 'png'
            logging.info("Detected color")

        self.img_file_ext = self.gs_options[self.img_format][0]

        # The possible output files glob
        globable_filename = '%s_*.%s' % (filename, self.img_file_ext)
        # Delete any img files already existing
        for fn in glob.glob(globable_filename):
            os.remove(fn)

        options = ' '.join(self.gs_options[self.img_format][1]) % {'dpi':self.output_dpi}
        output_filename = '%s_%%d.%s' % (filename, self.img_file_ext)
        self._run_gs(options, output_filename, pdf_filename)
        for fn in glob.glob(globable_filename):
            logging.info("Created image %s" % fn)
        return (self.output_dpi, globable_filename)

