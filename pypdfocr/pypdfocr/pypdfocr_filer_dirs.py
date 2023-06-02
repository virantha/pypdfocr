
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
import logging
import os
import shutil

from pypdfocr_filer import PyFiler

"""
    Implementation of a filer class 
        -> Works on file system/directory structure
"""
class PyFilerDirs(PyFiler):
    
    def __init__(self):
        self.target_folder = None
        self.default_folder = None
        self.original_move_folder = None
        self.folder_targets = {}

    def add_folder_target(self, folder, keywords):
        assert folder not in self.folder_targets, "Target folder already defined! (%s)" % (folder)
        self.folder_targets[folder] = keywords

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

    def move_to_matching_folder(self, filename, foldername):
        assert self.target_folder != None
        assert self.default_folder != None

        if not foldername:
            logging.info("[DEFAULT] %s --> %s" % (filename, self.default_folder))
            tgt_path = os.path.join(self.target_folder, self.default_folder)
        else:   
            logging.info("[MATCH] %s --> %s" % (filename, foldername))
            tgt_path = os.path.join(self.target_folder,foldername)

        if not os.path.exists(tgt_path):
            logging.debug("Making path %s" % tgt_path)
            os.makedirs(tgt_path)

        logging.debug("Moving %s to %s" % (filename, tgt_path))
        tgtfilename = os.path.join(tgt_path, os.path.basename(filename))
        tgtfilename = self._get_unique_filename_by_appending_version_integer(tgtfilename)

        shutil.move(filename, tgtfilename)
        return tgtfilename


