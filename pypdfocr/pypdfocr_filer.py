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

""" Abstract base class for defining filing objects, whether you want to 
    save to a file-system/directory structure or to something like Evernote

    """

class PyFiler(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def move_to_matching_folder(self, filename):
        """ Move the file given by filename to the proper location"""
        return

    @abc.abstractmethod
    def file_original(self, original_filename):
        """ Move the original file if required """

    @abc.abstractmethod
    def add_folder_target(self, folder, keywords):
        """ Add a target folder for a list of keywords """

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
