
# Copyright 2013 Stefan Gorling All Rights Reserved.
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
import hashlib
import time
import sys

from pypdfocr_filer import PyFiler

import functools

import dropbox

"""
    Implementation of a filer class 
        -> Files documents into dropbox subfolders. Mainly copy and paste from PyFilerEvernote
"""


class PyFilerDropbox(PyFiler):
    
    def get_target_folder(self):
        return self._target_folder
    def set_target_folder (self, target_folder):
        """ Override this to make sure we only have the basename"""
        print("Setting target_folder %s" % target_folder)
        if target_folder:
            self._target_folder = os.path.basename(target_folder)
        else:
            self._target_folder = target_folder

    target_folder = property(get_target_folder, set_target_folder)

    def get_default_folder (self):
        """ Override this to make sure we only have the basename"""
        return self._default_folder

    def set_default_folder (self, default_folder):
        """ Override this to make sure we only have the basename"""
        if default_folder:
            self._default_folder = os.path.basename(default_folder)
        else:
            self._default_folder = default_folder

    default_folder = property(get_default_folder, set_default_folder)

    def __init__(self, dev_token,base_path):
        self.target_folder = None
        self.default_folder = None
        self.original_move_folder = None
        self.folder_targets = {}
        self.dictUserInfo = { 'dev_token': dev_token }
        self.base_path = base_path
        self._connect_to_dropbox(self.dictUserInfo)

    def _connect_to_dropbox(self, dictUserInfo):
        """
            Establish a connection to dropbox and authenticate.

            :param dictUserInfo: contains the token that is needed to connect ot hte api
            :returns success: Return wheter connection succeeded
            :rtype bool:
        """
        print("Authenticating to Dropbox")
        dev_token = dictUserInfo['dev_token']
        logging.debug("Authenticating using token %s" % dev_token)
        user = None
        try:
            self.client = dropbox.Dropbox(dev_token)
        except Exception as e:
            print("Error attempting to connect to Dropbox: %s " % (e))
            sys.exit(-1)

        return True

    def add_folder_target(self, folder, keywords):
        assert folder not in self.folder_targets, "Target folder already defined! (%s)" % (folder)
        self.folder_targets[folder] = keywords

    def file_original(self, original_filename):
        """ 
            Just file it to the local file system (don't upload to dropbox)
        """
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
        """
          #Move file to dropbox

        """
        assert self.target_folder != None
        assert self.default_folder != None

        if not foldername:
            logging.info("[DEFAULT] %s --> %s" % (filename, self.default_folder))
            foldername = self.default_folder
        else:   
            logging.info("[MATCH] %s --> %s" % (filename, foldername))


        dest_path=self.base_path+"/"+foldername+"/"+os.path.basename(filename)
        logging.info("Sending to dropboxy as %s" % dest_path)

        #Send file to dropbox
        with open(filename) as f:
            self.client.files_upload(f.read(), dest_path, mute=True)
                              
        return "%s" % (dest_path)


if __name__ == '__main__': # pragma: no cover
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    p = PyFilerDropbox()
    p.add_folder_target("auto", ['dmv'])
    p.target_folder = 'myuploads'
    p.default_folder = 'default'
    p.original_move_folder = None

    p.move_to_matching_folder('../dmv/dmv_ocr.pdf', 'auto')
