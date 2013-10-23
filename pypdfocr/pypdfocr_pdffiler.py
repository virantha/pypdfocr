
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

from PyPDF2 import PdfFileReader

class PyPdfFiler(object):
    def __init__(self, target_folder, default_folder):

        self.target_folder = target_folder
        self.default_folder = default_folder

        self.folder_targets = {}  # This will need to be populated by the caller using addFolder

    def read_pdf_first_page(self, filename):
        self.filename = filename
        reader = PdfFileReader(filename)
        text = reader.getPage(0).extractText()
        text = text.encode('ascii', 'ignore')
        return text

    def add_folder_target(self, dirname, matchStrings):
        assert dirname not in self.folder_targets, "Target folder already defined! (%s)" % (dirname)
        self.folder_targets[dirname] = matchStrings

    def _get_matching_folder(self):
        searchText = self.pdfText.lower()
        for folder,strings in self.folder_targets.items():
            for s in strings:
                if s in searchText:
                    print s
                    return folder
        # No match found, so return 
        return None

    def move_to_matching_folder(self, filename):
        pdf_text = self.read_pdf_first_page(filename)
        tgt_folder = self._get_matching_folder(pdf_text)
        if not tgt_folder:
            logging.info("[DEFAULT] %s --> %s" % (filename, self.default_folder))
            tgt_path = os.path.join(self.target_folder, self.default_folder)
        else:   
            logging.info("[MATCH ] %s --> %s" % (filename, tgt_folder))
            tgt_path = os.path.join(self.target_folder,tgt_folder)

        if not os.path.exists(tgt_path):
            logging.debug("Making path %s" % tgt_path)
            os.makedirs(tgt_path)

        logging.debug("Moving %s to %s" % (filename, tgt_path)
        shutil.move(filename, tgt_path)
        
