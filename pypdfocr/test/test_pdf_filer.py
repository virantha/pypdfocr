#from pypdfocr import PyPDFOCR as P
import pypdfocr.pypdfocr as P
import pytest
import os

import hashlib

from mock import patch, call
from pytest import skip

class TestPDFFiler:

    @patch('shutil.move')
    def test_file_by_filename(self, mock_move):
        """
            Test filing of single pdf based on filename.
        """

        # Mock the move function so we don't actually end up filing
        p = P.PyPDFOCR()
        cwd = os.getcwd()
        filename = os.path.join("pdfs", "test_super_long_keyword.pdf")
        out_filename = filename.replace(".pdf", "_ocr.pdf")

        if os.path.exists(out_filename):
            os.remove(out_filename)

        print("Current directory: %s" % os.getcwd())
        #opts = [filename, "--config=test_pypdfocr_config.yaml", "-f"]
        opts = [filename, "--config=test_pypdfocr_config_filename.yaml", "-f", "-n"]
        p.go(opts)

        assert(os.path.exists(out_filename))
        os.remove(out_filename)

        calls = [call(out_filename, os.path.abspath(os.path.join('temp', 'target','recipe', os.path.basename(out_filename))))]
        mock_move.assert_has_calls(calls)



        
