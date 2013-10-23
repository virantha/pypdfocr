
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
    Provides capability to search PDFs and file to a specific folder based
    on keywords
"""

from sets import Set    
import sys, os
import re
import logging
import shutil

from PyPDF2 import PdfFileReader

class PyPdfFiler(object):
    def __init__(self, target_folder, default_folder, original_move_folder=None):

        self.target_folder = target_folder
        self.default_folder = default_folder
        self.original_move_folder = original_move_folder

        self.folder_targets = {}  # This will need to be populated by the caller using addFolder

    def iter_pdf_page_text(self, filename):
        self.filename = filename
        reader = PdfFileReader(filename)
        logging.info("pdf scanner found %d pages in %s" % (reader.getNumPages(), filename))
        for pgnum in range(reader.getNumPages()):
            text = reader.getPage(pgnum).extractText()
            text = text.encode('ascii', 'ignore')
            yield text

    def add_folder_target(self, dirname, matchStrings):
        assert dirname not in self.folder_targets, "Target folder already defined! (%s)" % (dirname)
        self.folder_targets[dirname] = matchStrings

    def _get_matching_folder(self, pdfText):
        searchText = pdfText.lower()
        for folder,strings in self.folder_targets.items():
            for s in strings:
                if s in searchText:
                    logging.info("Matched keyword '%s'" % s)
                    return folder
        # No match found, so return 
        return None

    def _split_filename_dir_filename_ext(self, filename):
        dr, fn = os.path.split(filename) # Get directory and filename
        fn_no_ext = fn.split('.')[0:-1] # Get the filename without ending extension
        fn_no_ext = ''.join(fn_no_ext)
        ext = fn.split('.')[-1]
        return dr, fn_no_ext, ext

    def _get_unique_filename_by_appending_version_integer(self, tgtfilename):
        if os.path.exists(tgtfilename):
            logging.info("File %s already exists in target directory %s" % (os.path.basename(tgtfilename), os.path.dirname(tgtfilename)))
            # First, try appending a _v1 to it
            num = 1
            dr, fn, ext = self._split_filename_dir_filename_ext(tgtfilename)
            tgtfilename = os.path.join(dr, "%s_%d.%s" % (fn, num, ext))
            while os.path.exists(tgtfilename):
                # Add an incrementing integer to the end of the filename and Loop until we find a new filename
                num += 1
                tgtfilename = os.path.join(dr, "%s_%d.%s" % (fn, num, ext))
                logging.info("Trying %s" % tgtfilename)
            logging.info("Using name %s instead for copying to target directory %s" % (os.path.basename(tgtfilename),os.path.dirname(tgtfilename )))
        return tgtfilename

    def file_original(self, original_filename):
        if not self.original_move_folder:
            logging.debug("Leaving original untouched")
            return original_filename

        tgt_path = self.original_move_folder
        logging.debug("Moving original %s to %s" % (original_filename, tgt_path))
        tgtfilename = os.path.join(tgt_path, os.path.basename(original_filename))
        tgtfilename = self._get_unique_filename_by_appending_version_integer(tgtfilename)

        shutil.move(original_filename, tgtfilename)
        return tgtfilename


    def move_to_matching_folder(self, filename):
        for page_text in self.iter_pdf_page_text(filename):
            tgt_folder = self._get_matching_folder(page_text)
            if tgt_folder: break  # Stop searching through pdf pages as soon as we find a match

        if not tgt_folder:
            logging.info("[DEFAULT] %s --> %s" % (filename, self.default_folder))
            tgt_path = os.path.join(self.target_folder, self.default_folder)
        else:   
            logging.info("[MATCH] %s --> %s" % (filename, tgt_folder))
            tgt_path = os.path.join(self.target_folder,tgt_folder)

        if not os.path.exists(tgt_path):
            logging.debug("Making path %s" % tgt_path)
            os.makedirs(tgt_path)

        logging.debug("Moving %s to %s" % (filename, tgt_path))
        tgtfilename = os.path.join(tgt_path, os.path.basename(filename))
        tgtfilename = self._get_unique_filename_by_appending_version_integer(tgtfilename)

        shutil.move(filename, tgtfilename)
        return tgtfilename
        
