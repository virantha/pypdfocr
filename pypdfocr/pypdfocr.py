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

from version import __version__
from PIL import Image
import yaml

from pypdfocr_pdf import PyPdf
from pypdfocr_tesseract import PyTesseract
from pypdfocr_gs import PyGs
from pypdfocr_watcher import PyPdfWatcher
from pypdfocr_pdffiler import PyPdfFiler

def error(text):
    print("ERROR: %s" % text)
    sys.exit(-1)


class PyPDFOCR(object):

    def __init__ (self):
        self.maxlength = 500
        self.gs = PyGs()
        self.ts = PyTesseract()
        self.pdf = PyPdf()

    def _get_config_file(self, config_file):
        with config_file:
            myconfig = yaml.load(config_file)
        return myconfig



    def get_options(self, argv):
        p = argparse.ArgumentParser(
                description = "Convert scanned PDFs into their OCR equivalent.  Depends on GhostScript and Tesseract-OCR being installed.",
                epilog = "PyPDFOCR version %s (Copyright 2013 Virantha Ekanayake)" % __version__,
                )

        p.add_argument('-d', '--debug', action='store_true',
            default=False, dest='debug', help='Turn on debugging')

        p.add_argument('-v', '--verbose', action='store_true',
            default=False, dest='verbose', help='Turn on verbose mode')

        #---------
        # Single or watch mode
        #--------
        single_or_watch_group = p.add_mutually_exclusive_group(required=True)
        # Positional argument for single file conversion
        single_or_watch_group.add_argument("pdf_filename", nargs="?", help="Scanned pdf file to OCR")
        # Watch directory for watch mode
        single_or_watch_group.add_argument('-w', '--watch', 
             dest='watch_dir', help='Watch given directory and run ocr automatically until terminated')

        #-----------
        # Filing options
        #----------
        filing_group = p.add_argument_group(title="Filing optinos")
        filing_group.add_argument('-f', '--file', action='store_true',
            default=False, dest='enable_filing', help='Enable filing of converted PDFs')
        filing_group.add_argument('-c', '--config', type = argparse.FileType('r'),
             dest='configfile', help='Configuration file for defaults and PDF filing')


        args = p.parse_args(argv)

        self.debug = args.debug
        self.verbose = args.verbose
        self.pdf_filename = args.pdf_filename
        self.watch_dir = args.watch_dir

        if self.debug:
            logging.basicConfig(level=logging.DEBUG, format='%(message)s')

        if self.verbose:
            logging.basicConfig(level=logging.INFO, format='%(message)s')

        # Parse configuration file (YAML) if specified
        if args.configfile:
            self.config = self._get_config_file(args.configfile)
            logging.debug("Read in configuration file")
            logging.debug(self.config)

        if args.enable_filing:
            self.enable_filing = True
            if not args.configfile:
                p.error("Please specify a configuration file(CONFIGFILE) to enable filing")
        else:
            self.enable_filing = False

        self.watch = False

        if args.watch_dir:
            logging.debug("Starting to watch")
            self.watch = True
    
    def clean_up_files(self, files):
        for file in files:
            try:
                os.remove(file)
            except:
                logging.info("Error removing file %s .... continuing" % file)

            

    def _setup_filing(self):
        # Look at self.config and create a self.filer object

        # Some sanity checks
        assert(self.config and self.enable_filing)
        for required in ['target_folder', 'default_folder']:
            if not required in self.config:
                error ("%s must be specified in config file" % required)
            else:
                # Make sure these required folders are in abspath format
                self.config[required] = os.path.abspath(self.config[required])
        if 'original_move_folder' in self.config:
            # User wants to move the original after filing
            orig = 'original_move_folder'
            self.config[orig] = os.path.abspath(self.config[orig])
            if not os.path.exists(self.config[orig]):
                os.makedirs(self.config[orig])
            self.move_original = True
        else:
            self.move_original = False

        # Start the filing object
        self.filer = PyPdfFiler(target_folder = self.config['target_folder'],
                                default_folder = self.config['default_folder']
                                )
        if 'folders' in self.config:
            for folder, keywords in self.config['folders'].items():
                self.filer.add_folder_target(folder, keywords)

        print ("Filing of PDFs is enabled")

    
    def run_conversion(self, pdf_filename):
        print ("Starting conversion of %s" % pdf_filename)
        conversion_format = "tiff"
        tiff_dpi, tiff_filename = self.gs.make_img_from_pdf(pdf_filename, conversion_format)
        hocr_filename = self.ts.make_hocr_from_tiff(tiff_filename)
        
        ocr_pdf_filename = self.pdf.overlay_hocr(tiff_dpi, hocr_filename)
        self.clean_up_files((tiff_filename, hocr_filename))
        print ("Completed conversion successfully to %s" % ocr_pdf_filename)
        return ocr_pdf_filename

    def go(self, argv):

        # Read the command line options
        self.get_options(argv)

        # Setup the pdf filing if enabled
        if self.enable_filing:
            self._setup_filing()

        if self.watch:
            py_watcher = PyPdfWatcher(self.watch_dir)
            for pdf_filename in py_watcher.start():
                ocr_pdffilename = self.run_conversion(pdf_filename)
                if self.enable_filing:
                    tgt_path = self.filer.move_to_matching_folder(ocr_pdffilename)  
                    print("Filed %s to %s as %s" % (ocr_pdffilename, os.path.dirname(tgt_path), os.path.basename(tgt_path)))
        else:
            ocr_pdffilename = self.run_conversion(self.pdf_filename)
            if self.enable_filing:
                tgt_path = self.filer.move_to_matching_folder(ocr_pdffilename)  
                print("Filed %s to %s as %s" % (ocr_pdffilename, os.path.dirname(tgt_path), os.path.basename(tgt_path)))

def main():
    script = PyPDFOCR()
    script.go(sys.argv[1:])

if __name__ == '__main__':
    main()


