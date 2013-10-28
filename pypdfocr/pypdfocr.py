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

import smtplib
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
from pypdfocr_filer_dirs import PyFilerDirs
from pypdfocr_filer_evernote import PyFilerEvernote

def error(text):
    print("ERROR: %s" % text)
    sys.exit(-1)



"""
    Make scanned PDFs searchable using Tesseract-OCR and autofile them
.. automodule:: pypdfocr
    :private-members:
"""

class PyPDFOCR(object):
    """
        The main clas.  Performs the following functions:

        * Parses command line options
        * Optionally just watches a directory for new PDF's to OCR; once a file appears, it does the next step
        * Runs a single file conversion:
            * Runs ghostscript to get tiff/jpg
            * Runs Tesseract-OCR to do the actual OCR
            * Takes the HOCR from Tesseract and creates a new PDF with the text overlay
        * Files the OCR'ed file in the proper place if specified
        * Files the original file if specified
        * 
    """

    def __init__ (self):
        self.maxlength = 500
        self.gs = PyGs()
        self.ts = PyTesseract()
        self.pdf = PyPdf()

    def _get_config_file(self, config_file):
        """
            
        """
        with config_file:
            myconfig = yaml.load(config_file)
        return myconfig



    def get_options(self, argv):
        """
            :param argv: usually just sys.argv[1:]
            :returns: Nothing
            Parse the command-line options and set the following object properties:


            :ivar debug: Enable logging debug statements
            :ivar verbose: Enable verbose logging
            :ivar enable_filing: Whether to enable post-OCR filing of PDFs
            :ivar pdf_filename: Filename for single conversion mode
            :ivar watch_dir: Directory to watch for files to convert
            :ivar config: Dict of the config file
            :ivar watch: Whether folder watching mode is turned on
            :ivar enable_evernote: Enable filing to evernote

        """
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
        filing_group.add_argument('-e', '--evernote', action='store_true',
            default=False, dest='enable_evernote', help='Enable filing to Evernote')


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

        if args.enable_evernote:
            self.enable_evernote = True
        else:
            self.enable_evernote = False

        if args.enable_filing or args.enable_evernote:
            self.enable_filing = True
            if not args.configfile:
                p.error("Please specify a configuration file(CONFIGFILE) to enable filing")
        else:
            self.enable_filing = False

        self.watch = False

        if args.watch_dir:
            logging.debug("Starting to watch")
            self.watch = True
    
    def _clean_up_files(self, files):
        for file in files:
            try:
                os.remove(file)
            except:
                logging.info("Error removing file %s .... continuing" % file)

            

    def _setup_filing(self):
        # Look at self.config and create a self.pdf_filer object

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
            original_move_folder = self.config[orig]
        else:
            original_move_folder = None

        # Start the filing object
        if self.enable_evernote:
            self.filer = PyFilerEvernote(self.config['evernote_developer_token'])
        else:
            self.filer = PyFilerDirs()
            
        self.filer.target_folder = self.config['target_folder']
        self.filer.default_folder = self.config['default_folder']
        self.filer.original_move_folder = original_move_folder

        self.pdf_filer = PyPdfFiler(self.filer)

        keyword_count = 0
        folder_count = 0
        if 'folders' in self.config:
            for folder, keywords in self.config['folders'].items():
                folder_count +=1
                keyword_count += len(keywords)
                self.filer.add_folder_target(folder, keywords)

        print ("Filing of PDFs is enabled")
        print (" - %d target filing folders" % (folder_count))
        print (" - %d keywords" % (keyword_count))

    
    def run_conversion(self, pdf_filename):
        print ("Starting conversion of %s" % pdf_filename)
        conversion_format = "tiff"
        tiff_dpi, tiff_filename = self.gs.make_img_from_pdf(pdf_filename, conversion_format)
        hocr_filename = self.ts.make_hocr_from_tiff(tiff_filename)
        
        ocr_pdf_filename = self.pdf.overlay_hocr(tiff_dpi, hocr_filename)
        self._clean_up_files((tiff_filename, hocr_filename))
        print ("Completed conversion successfully to %s" % ocr_pdf_filename)
        return ocr_pdf_filename

    def file_converted_file(self, ocr_pdffilename, original_pdffilename):
        tgt_path = self.pdf_filer.move_to_matching_folder(ocr_pdffilename)  
        print("Filed %s to %s as %s" % (ocr_pdffilename, os.path.dirname(tgt_path), os.path.basename(tgt_path)))

        tgt_path = self.pdf_filer.file_original(original_pdffilename)
        if tgt_path != original_pdffilename:
            print("Filed original file %s to %s as %s" % (original_pdffilename, os.path.dirname(tgt_path), os.path.basename(tgt_path)))

  
    def _send_email(self, from_addr, to_addr_list, cc_addr_list,
                  subject, message,
                  login, password,
                  smtpserver):
        header  = 'From: %s\n' % from_addr
        header += 'To: %s\n' % ','.join(to_addr_list)
        header += 'Cc: %s\n' % ','.join(cc_addr_list)
        header += 'Subject: %s\n\n' % subject
        message = header + message
      
        server = smtplib.SMTP(smtpserver)
        server.starttls()
        server.login(login,password)
        problems = server.sendmail(from_addr, to_addr_list, message)
        server.quit()

    def go(self, argv):

        # Read the command line options
        self.get_options(argv)

        # 
        #self._send_email(
                        #from_addr="virantha@gmail.com",
                        #to_addr_list=["virantha@gmail.com"],
                        #cc_addr_list = [],
                        #subject = "PyPDFOCR upload",
                        #message = "Uploaded email\n\n-Virantha", 
                        #login = "virantha@gmail.com",
                        #password = "cctahvuntxbuwmox",
                        #smtpserver = "smtp.gmail.com:587",
                        #)

        # Setup the pdf filing if enabled
        if self.enable_filing:
            self._setup_filing()

        if self.watch:
            py_watcher = PyPdfWatcher(self.watch_dir)
            for pdf_filename in py_watcher.start():
                ocr_pdffilename = self.run_conversion(pdf_filename)
                if self.enable_filing:
                    self.file_converted_file(ocr_pdffilename, pdf_filename)
        else:
            ocr_pdffilename = self.run_conversion(self.pdf_filename)
            if self.enable_filing:
                self.file_converted_file(ocr_pdffilename, self.pdf_filename)

def main():
    script = PyPDFOCR()
    script.go(sys.argv[1:])

if __name__ == '__main__':
    main()


