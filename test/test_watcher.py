#from pypdfocr import PyPDFOCR as P
import pypdfocr.pypdfocr_watcher as P
import pytest

import evernote.api.client
import evernote.edam.type.ttypes as Types
import hashlib
import time
import os
from collections import namedtuple

from mock import patch, call

class TestWatching:


    filenames = [   ("test_recipe.pdf", "test_recipe.pdf"),
                    (os.path.join("..","test_recipe.pdf"), os.path.join("..","test_recipe.pdf")),
                    (os.path.join("/", "Volumes","Media", "test_recipe.pdf"), os.path.join("/","Volumes", "Media", "test_recipe.pdf")),
                    (os.path.join("/", "Volumes", "Media", "test recipe.pdf"), os.path.join("/","Volumes","Media","test_recipe.pdf")),
                    (os.path.join("..","V olumes","Media", "test recipe.pdf"), os.path.join("..", "V olumes","Media", "test_recipe.pdf")),
                ]

    @patch('shutil.move')
    @pytest.mark.parametrize(("filename, expected"), filenames)
    def test_rename(self, mock_move, filename, expected):
    
        if expected == None:
            expected = filename

        p = P.PyPdfWatcher('temp',{})

        # First, test code that does not move original
        ret = p.rename_file_with_spaces(filename)
        assert (ret==expected)

    def test_check_for_new_pdf(self):
    
        p = P.PyPdfWatcher('temp', {})
        p.check_for_new_pdf("blah_ocr.pdf")
        assert("blah_ocr.pdf" not in p.events)
        p.check_for_new_pdf("blah.pdf")
        assert("blah.pdf" in p.events)
        p.events['blah.pdf'] = -1
        p.check_for_new_pdf("blah.pdf")
        assert("blah.pdf" not in p.events)
        p.check_for_new_pdf("blah.pdf")
        time.sleep(p.scan_interval+1)
        p.check_for_new_pdf("blah.pdf")
        assert(p.events['blah.pdf']-time.time() <=1) # Check that time stamp was updated

    def test_events(self):
        p = P.PyPdfWatcher('temp', {})

        event = namedtuple('event', 'src_path, dest_path')

        p.on_created(event(src_path='temp_recipe.pdf', dest_path=None))
        assert('temp_recipe.pdf' in p.events)

        p.on_moved(event(src_path=None, dest_path='temp_recipe2.pdf'))
        assert('temp_recipe2.pdf' in p.events)

        p.on_modified(event(src_path='temp_recipe3.pdf', dest_path=None))
        assert('temp_recipe3.pdf' in p.events)

    def test_check_queue(self):
        p = P.PyPdfWatcher('temp', {})
        now = time.time()
        p.events['blah.pdf'] = now
        f = p.check_queue()
        assert (not f)
        assert ('blah.pdf' in p.events)
        time.sleep(p.scan_interval+1)
        f = p.check_queue()
        assert (f=='blah.pdf')
        assert ('blah.pdf' in p.events)
        assert (p.events['blah.pdf'] == -1)
        f = p.check_queue()
        assert ('blah.pdf' not in p.events)

