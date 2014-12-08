#from pypdfocr import PyPDFOCR as P
import pypdfocr.pypdfocr_gs as P
import pytest
import os

import hashlib

from mock import patch, call
from pytest import skip

class TestGS:

    @pytest.mark.skipif(os.name!='nt', reason="Not on NT")
    @patch('os.name')
    @patch('subprocess.check_output')
    def test_gs_set_nt(self, mock_subprocess, mock_os_name):
        """
            Check that we have a exe on windows
        """
        mock_os_name.__str__.return_value = 'nt'
        p = P.PyGs({})

        assert 'gswin' in p.binary

    @pytest.mark.skipif(os.name!='nt', reason="Not on NT")
    @patch('os.name')
    @patch('subprocess.call')
    def test_gs_run_nt(self, mock_subprocess, mock_os_name, capsys):
        """
            Stupid test because Windows Tesseract only returns 3.02 instead of 3.02.02
        """
        mock_os_name.__str__.return_value = 'nt'
        p = P.PyGs({})

        mock_subprocess.return_value = -1
        p.binary = 'gsblah.exe'
        with pytest.raises(SystemExit):
            p._run_gs("","","")

        out,err = capsys.readouterr()
        assert p.msgs['GS_FAILED'] in out

    def test_gs_pdf_missing(self, capsys):
        p = P.PyGs({})
        with pytest.raises(SystemExit):
            p.make_img_from_pdf("missing123.pdf")
        out,err = capsys.readouterr()
        assert p.msgs['GS_MISSING_PDF'] in out


