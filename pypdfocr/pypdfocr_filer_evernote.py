
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
import hashlib
import time
import sys

from pypdfocr_filer import PyFiler

import functools

from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
import evernote.edam.userstore.constants as UserStoreConstants
from evernote.edam.error.ttypes import EDAMUserException
from evernote.edam.error.ttypes import EDAMSystemException
from evernote.edam.error.ttypes import EDAMNotFoundException
from evernote.edam.error.ttypes import EDAMErrorCode


"""
    Implementation of a filer class 
        -> Files documents to Evernote notebooks (each document becomes a new note)
"""
class en_handle(object):
    """ Generic exception handler for Evernote actions
    """
    def __init__(self, f):
        # f is the method being decorated, so save it so we can call it later!
        self.f = f
        functools.update_wrapper(self, f)

    def __get__(self, instance, owner):
        # Save a ptr to the object being decorated
        self.cls = owner
        self.obj = instance
        return self.__call__

    def __call__(self, *args, **kwargs):
        # The actual meat of the decorator

        # Call the original method being decorated
        retryCount = 3
        retry_auth = False
        msg = "EVERNOTE ERROR: %s"
        r = None
        while retryCount > 0:
            try: 
                retryCount -= 1
                if retry_auth:
                    logging.debug("Retrying")
                    self.obj._connect_to_evernote(self.obj.dictUserInfo)
                retry_auth = False
                logging.debug("executing user function")
                r = self.f.__call__(self.obj, *args, **kwargs)
                break
            except EDAMUserException as e:
                err = e.errorCode
                c = EDAMErrorCode
                if err == c.AUTH_EXPIRED or err == c.DATA_REQUIRED:
                    logging.debug(msg % "Authorization expired, retrying...")
                    retry_auth = True
                    time.sleep(3)
                else:
                    logging.debug(msg % ("Unhandled error %s:%s" % (c._VALUES_TO_NAMES[err], e.parameter)))
        return r



class PyFilerEvernote(PyFiler):
    
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

    def __init__(self, dev_token):
        self.target_folder = None
        self.default_folder = None
        self.original_move_folder = None
        self.folder_targets = {}
        self.dictUserInfo = { 'dev_token': dev_token }
        self._connect_to_evernote(self.dictUserInfo)

    def _connect_to_evernote(self, dictUserInfo):
        """
            Establish a connection to evernote and authenticate.

            :param dictUserInfo: Dict of user info like user/passwrod.  For now, just the dev token
            :returns success: Return wheter connection succeeded
            :rtype bool:
        """
        print("Authenticating to Evernote")
        dev_token = dictUserInfo['dev_token']
        logging.debug("Authenticating using token %s" % dev_token)
        user = None
        try:
            self.client = EvernoteClient(token=dev_token, sandbox=False)
            self.user_store = self.client.get_user_store()
            user = self.user_store.getUser()
        except EDAMUserException as e:
            err = e.errorCode
            print("Error attempting to authenticate to Evernote: %s - %s" % (EDAMErrorCode._VALUES_TO_NAMES[err], e.parameter))
        except EDAMSystemException as e:
            err = e.errorCode
            print("Error attempting to authenticate to Evernote: %s - %s" % (EDAMErrorCode._VALUES_TO_NAMES[err], e.message))
            sys.exit(-1)

        if user:
            print("Authenticated to evernote as user %s" % user.username)
        return True

    def add_folder_target(self, folder, keywords):
        assert folder not in self.folder_targets, "Target folder already defined! (%s)" % (folder)
        self.folder_targets[folder] = keywords

    def file_original(self, original_filename):
        """ 
            Just file it to the local file system (don't upload to evernote)
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

    @en_handle
    def _get_notebooks(self):
        note_store = self.client.get_note_store()
        notebooks = note_store.listNotebooks()
        return {n.name:n for n in notebooks}

    @en_handle
    def _create_notebook(self, notebook):
        note_store = self.client.get_note_store()
        return note_store.createNotebook(notebook)

    def _update_notebook(self, notebook):
        note_store = self.client.get_note_store()
        note_store.updateNotebook(notebook)
        return

    @en_handle
    def _check_and_make_notebook(self, notebook_name):
        """
            Weird.
            :returns notebook: New or existing notebook object
            :rtype Types.Notebook:
        """
        # Get the noteStore
        #note_store = self.client.get_note_store()
        #notebooks = note_store.listNotebooks()
        #notebooks = {n.name:n for n in notebooks}
        notebooks = self._get_notebooks()
        if notebook_name in notebooks:
            notebook = notebooks[notebook_name]
            if notebook.stack != self.target_folder:
                notebook.stack = self.target_folder
                self._update_notebook(notebook)
            return notebook
        else:
            # Need to create a new notebook
            notebook = Types.Notebook()
            notebook.name = notebook_name
            notebook.stack = self.target_folder
            notebook = self._create_notebook(notebook)
            #notebook = note_store.createNotebook(notebook)
            return notebook

    @en_handle
    def _create_evernote_note(self, notebook, filename):
        # Create the new note
        note = Types.Note()
        note.title = os.path.basename(filename)
        note.notebookGuid = notebook.guid
        note.content = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
        note.content += '<en-note>Uploaded by PyPDFOCR <br/>'
       

        logging.debug("Loading PDF")
        md5 = hashlib.md5()
        with open(filename,'rb') as f: 
            pdf_bytes = f.read()

        logging.debug("Calculating md5 checksum of pdf")
        md5.update(pdf_bytes)
        md5hash = md5.hexdigest()

        logging.debug("Uploading note")
        
        # Create the Data type for evernote that goes into a resource
        pdf_data = Types.Data()
        pdf_data.bodyHash = md5hash
        pdf_data.size = len(pdf_bytes) 
        pdf_data.body = pdf_bytes

        # Add a link in the evernote boy for this content
        link = '<en-media type="application/pdf" hash="%s"/>' % md5hash
        logging.debug(link)
        note.content += link
        note.content += '</en-note>'
        
        resource_list = []
        pdf_resource = Types.Resource()
        pdf_resource.data = pdf_data
        pdf_resource.mime = "application/pdf"
        # TODO: Enable filename
        # Make a attributes for this resource
        pdf_resource.attributes = Types.ResourceAttributes()
        pdf_resource.attributes.fileName = os.path.basename(filename)
        resource_list.append(pdf_resource)

        note.resources = resource_list

        return note

        
    def move_to_matching_folder(self, filename, foldername):
        """
            Use the evernote API to create a new note:

            #. Make the notebook if it doesn't exist (:func:`_check_and_make_notebook`)
            #. Create the note (:func:`_create_evernote_note`)
            #. Upload note using API

        """
        assert self.target_folder != None
        assert self.default_folder != None

        if not foldername:
            logging.info("[DEFAULT] %s --> %s" % (filename, self.default_folder))
            foldername = self.default_folder
        else:   
            logging.info("[MATCH] %s --> %s" % (filename, foldername))

        # Check if the evernote notebook exists
        print ("Checking for notebook named %s" % foldername)
        notebook = self._check_and_make_notebook(foldername)
        print("Uploading %s to %s" % (filename, foldername))
        
        note = self._create_evernote_note(notebook, filename)

        # Store the note in evernote
        note_store = self.client.get_note_store()
        note = note_store.createNote(note)
        os.remove(filename)

        return "%s/%s" % (notebook.name, note.title)


if __name__ == '__main__': # pragma: no cover
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    p = PyFilerEvernote()
    p.add_folder_target("auto", ['dmv'])
    p.target_folder = 'myuploads'
    p.default_folder = 'default'
    p.original_move_folder = None

    p.move_to_matching_folder('../dmv/dmv_ocr.pdf', 'auto')
