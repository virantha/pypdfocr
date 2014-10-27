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
    Wrap ImageMagick calls.  Yes, this is ugly.
"""

import subprocess
import sys, os
import logging
import glob

def error(text):
    print("ERROR: %s" % text)
    exit(-1)

class PyPreprocess(object):
    """Class to wrap all the ImageMagick convert calls"""
    def __init__(self):
        self.msgs = {
                'CV_FAILED': 'convert execution failed',
            }



    def _warn(self, msg):
        print("WARNING: %s" % msg)

    def cmd(self, cmd_list):
        if isinstance(cmd_list, list):
            cmd_list = ' '.join(cmd_list)
        logging.debug("Running cmd: %s" % cmd_list)
        try:
            out = subprocess.check_output(cmd_list, stderr=subprocess.STDOUT, shell=True)
            logging.debug(out)
            return out
        except subprocess.CalledProcessError as e:
            print e.output
            self._warn("Could not run command %s" % cmd_list)
            

    def _run_preprocess(self,  in_filename):
        basename, filext = os.path.splitext(in_filename)
        out_filename = '%s_preprocess%s' % (basename, filext)
        #-respect-parenthesis \( -clone 0 -colorspace gray -negate -lat 15x5+5% -contrast-stretch 0 \) -compose copy_opacity -composite -opaque none +matte -modulate 100,50 -adaptive-blur 2.0 -sharpen 0x1 
        c = ['convert',
                "'%s'" % in_filename,
                '-respect-parenthesis',
                #'\\( $setcspace -colorspace gray -type grayscale \\)',
                '\\(',
                '-clone 0',
                '-colorspace gray -negate -lat 15x15+5\% -contrast-stretch 0 \\) -compose copy_opacity -composite -opaque none +matte -modulate 100,100',
                #'-adaptive-blur 1.0',
                '-blur 1x1',
                #'-selective-blur 4x4+5%',
                '-adaptive-sharpen 0x2',
                '-negate -define morphology:compose=darken -morphology Thinning Rectangle:1x30+0+0 -negate ',  # Removes vertical lines >=60 pixes, reduces widht of >30 (oherwise tesseract completely ignores text close to vertical lines in a table)
                "'%s'" % (out_filename)
                ]
        logging.info("Preprocessing image for better OCR")
        res = self.cmd(c)
        if res is None:
            return in_filename
        else:
            return out_filename



    def preprocess(self, in_filenames):
        fns = in_filenames
        preprocessed_filenames = []
        for fn in fns:
            out_fn = self._run_preprocess(fn)
            logging.debug("Created %s" % out_fn)
            preprocessed_filenames.append(out_fn)
        return preprocessed_filenames

        self._get_dpi(pdf_filename) # No need to bother anymore

