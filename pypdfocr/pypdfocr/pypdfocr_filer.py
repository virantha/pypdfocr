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
import abc
import os, logging

class PyFiler(object):
    """ Abstract base class for defining filing objects, whether you want to 
    save to a file-system/directory structure or to something like Evernote

    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def move_to_matching_folder(self, filename):
        """ Move the file given by filename to the proper location.
            You will need to use :py:attr:`target_folder` and :py:attr:`folder_targets`
            to figure out what the proper destination is.  If there is no matching location,
            then use :py:attr:`default_folder`

            :param filename: File to move
            :type filename: string
            :returns: Full path+filename of destination
            :rtype: string
        """

    @abc.abstractmethod
    def file_original(self, original_filename):
        """ Move the original file given by filename to the proper location.
            You will need to use :py:attr:`original_move_target`

            :param original_filename: File to move
            :type original_filename: string
            :returns: Full path+filename of destination(original_filename if not moved)
            :rtype: string
        """

    @abc.abstractmethod
    def add_folder_target(self, folder, keywords):
        """ Add a target folder for a list of keywords """

    def _get_unique_filename_by_appending_version_integer(self, tgtfilename):
        if os.path.exists(tgtfilename):
            logging.info("File %s already exists in target directory %s" % (os.path.basename(tgtfilename), os.path.dirname(tgtfilename)))
            # First, try appending a _v1 to it
            num = 1
            dr, fn, ext = self._split_filename_dir_filename_ext(tgtfilename)
            tgtfilename = os.path.join(dr, "%s_%d%s" % (fn, num, ext))
            while os.path.exists(tgtfilename):
                # Add an incrementing integer to the end of the filename and Loop until we find a new filename
                num += 1
                tgtfilename = os.path.join(dr, "%s_%d%s" % (fn, num, ext))
                logging.info("Trying %s" % tgtfilename)
            logging.info("Using name %s instead for copying to target directory %s" % (os.path.basename(tgtfilename),os.path.dirname(tgtfilename )))
        return tgtfilename

    def _split_filename_dir_filename_ext(self, filename):
        dr, fn = os.path.split(filename) # Get directory and filename

        # Silly me, forgot about the splitext function
        #fn_no_ext = fn.split('.')[0:-1] # Get the filename without ending extension
        #fn_no_ext = ''.join(fn_no_ext)
        #ext = fn.split('.')[-1]

        fn_no_ext, ext = os.path.splitext(fn)  # Get filename plus extension
        return dr, fn_no_ext, ext

    def get_target_folder(self):
        return self._target_folder
    def set_target_folder(self, target_folder):
        self._target_folder = target_folder

    def get_default_folder(self):
        return self._default_folder
    def set_default_folder(self, default_folder):
        self._default_folder = default_folder
    
    def get_original_move_folder(self):
        return self._original_move_folder
    def set_original_move_folder(self, original_move_folder):
        self._original_move_folder = original_move_folder

    def get_folder_targets(self):
        return self._folder_targets
    def set_folder_targets(self, folder_targets):
        self._folder_targets = folder_targets

    target_folder = property (get_target_folder, set_target_folder)
    default_folder = property (get_default_folder, set_default_folder)
    original_move_folder = property(get_original_move_folder, set_original_move_folder)
   
    folder_targets = property(get_folder_targets, set_folder_targets)
    """ Data structure for mapping a keyword to a folder target.  Usually just a dict, and new mappings
        are added from :py:func:`add_folder_target` 
    """
