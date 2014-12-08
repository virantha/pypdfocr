#from pypdfocr import PyPDFOCR as P
import pypdfocr.pypdfocr_tesseract as P
import pytest
import os

import hashlib

from mock import patch, call

class TestTesseract:

    @pytest.mark.skipif(os.name=='nt', reason='Does not work on Windows')
    def test_version_shorter_older(self):
        with patch("subprocess.check_output") as mock_subprocess:
            p = P.PyTesseract({})
            p.required = "3.02.02"
            mock_subprocess.return_value = """tesseract 3.02"""
            uptodate,ver = p._is_version_uptodate()
            assert (not uptodate)

    def test_version_minor_older(self):
        with patch("subprocess.check_output") as mock_subprocess:
            p = P.PyTesseract({})
            p.required = "3.02.02"
            mock_subprocess.return_value = """tesseract 3.02.01"""
            uptodate,ver = p._is_version_uptodate()
            assert (not uptodate)

    def test_version_major_older(self):
        with patch("subprocess.check_output") as mock_subprocess:
            p = P.PyTesseract({})
            p.required = "3.02.02"
            mock_subprocess.return_value = """tesseract 2.03.03"""
            uptodate,ver = p._is_version_uptodate()
            assert (not uptodate)

    @pytest.mark.skipif(os.name=='nt', reason='Does not work on Windows')
    def test_version_major_equal(self):
        with patch("subprocess.check_output") as mock_subprocess:
            p = P.PyTesseract({})
            p.required = "3.02.02"
            mock_subprocess.return_value = """tesseract 3.02.02"""
            uptodate,ver = p._is_version_uptodate()
            assert (uptodate)

    def test_version_major_newer(self):
        with patch("subprocess.check_output") as mock_subprocess:
            p = P.PyTesseract({})
            p.required = "3.02.02"

            mock_subprocess.return_value = """tesseract 4.01"""
            uptodate,ver = p._is_version_uptodate()
            assert (uptodate)

    def test_version_minor_newer(self):
        with patch("subprocess.check_output") as mock_subprocess:
            p = P.PyTesseract({})
            p.required = "3.01.02"

            mock_subprocess.return_value = """tesseract 3.02"""
            uptodate,ver = p._is_version_uptodate()
            assert (uptodate)


    def test_tesseract_presence(self, capsys):
        p = P.PyTesseract({})
        p.binary = "tesserac" # Misspell it and make sure we get an error
        with pytest.raises(SystemExit):
            p._is_version_uptodate()
        out, err = capsys.readouterr()
        assert p.msgs['TS_MISSING'] in out

    def test_tesseract_version(self, capsys):
        p = P.PyTesseract({})
        p.required = "100"
        with pytest.raises(SystemExit):
            p.make_hocr_from_pnms("")
        out, err = capsys.readouterr()
        assert p.msgs['TS_VERSION'] in out

    def test_tiff_file_check(self, capsys):
        p = P.PyTesseract({})
        with pytest.raises(SystemExit):
            p.make_hocr_from_pnm("DUMMY_NOTPRESENT.tiff")
        out, err = capsys.readouterr()
        assert p.msgs['TS_img_MISSING'] in out

    @patch('os.name')
    @patch('subprocess.check_output')
    def test_tesseract_version_nt(self, mock_subprocess, mock_os_name):
        """
            Stupid test because Windows Tesseract only returns 3.02 instead of 3.02.02
        """
        mock_os_name.__str__.return_value = 'nt'
        p = P.PyTesseract({})
        p.required = "3.02.02"

        mock_subprocess.return_value = """tesseract 3.02"""
        uptodate,ver = p._is_version_uptodate()
        assert (uptodate)

    @patch('pypdfocr.pypdfocr_tesseract.PyTesseract._is_version_uptodate')
    @patch('pypdfocr.pypdfocr_tesseract.os.name')
    @patch('pypdfocr.pypdfocr_tesseract.os.path.exists')
    def test_force_Nt(self, mock_os_path_exists, mock_os_name, mock_uptodate, capsys):
        mock_os_name.__str__.return_value = 'nt'
        p = P.PyTesseract({})
        assert ('tesseract.exe' in p.binary)

        mock_os_path_exists.return_value = True 
        mock_uptodate.return_value = (True,"")
        # force a bad tesseract on windows
        p.binary = "blah"
        print("here")
        with pytest.raises(SystemExit):
            p.make_hocr_from_pnm('blah.tiff')

    @patch('pypdfocr.pypdfocr_tesseract.subprocess.call')
    @patch('pypdfocr.pypdfocr_tesseract.PyTesseract._is_version_uptodate')
    @patch('pypdfocr.pypdfocr_tesseract.os.name')
    @patch('pypdfocr.pypdfocr_tesseract.os.path.exists')
    def test_tesseract_fail(self, mock_os_path_exists, mock_os_name, mock_uptodate, mock_subprocess_call,capsys):
        """
            Get all the checks past and make sure we report the case where tesseract returns a non-zero status
        """
        mock_os_name.__str__.return_value = 'nt'
        p = P.PyTesseract({})
        assert ('tesseract.exe' in p.binary)

        mock_os_path_exists.return_value = True 
        mock_uptodate.return_value = (True,"")
        mock_subprocess_call.return_value = -1
        with pytest.raises(SystemExit):
            p.make_hocr_from_pnm('blah.tiff')

        out, err = capsys.readouterr()
        assert p.msgs['TS_FAILED'] in out

