#from pypdfocr import PyPDFOCR as P
import pypdfocr.pypdfocr as P
import pytest
import os
import logging

from PyPDF2 import PdfFileReader
import smtplib
from mock import Mock
from mock import patch, call
from mock import MagicMock
from mock import PropertyMock


class TestPydfocr:

    def setup(self):
        self.p = P.PyPDFOCR()

    def _iter_pdf(self, filename):
        with open(filename, 'rb') as f:
            reader = PdfFileReader(f)
            logging.debug("pdf scanner found %d pages in %s" % (reader.getNumPages(), filename))
            for pgnum in range(reader.getNumPages()):
                text = reader.getPage(pgnum).extractText()
                text = text.encode('ascii', 'ignore')
                text = text.replace('\n', ' ')
                yield text
    
    pdf_tests = [
            (".", os.path.join("temp","target","recipe"), os.path.join("..","test", "pdfs", "test_recipe.pdf"), [ ["Simply Recipes"],
                                 ]),
        (".", os.path.join("temp","target","patents"), os.path.join("pdfs","test_patent.pdf"), [ 
                           ["asynchronous", "subject to", "20 Claims"], # Page 1
                           ["FOREIGN PATENT" ], # Page 2
                            ]),
        (".", os.path.join("temp","target", "default"), os.path.join("pdfs","test_sherlock.pdf"), [ ["Bohemia", "Trincomalee"], # Page 1
                           ["hundreds of times" ], # Page 2
                           ]),
        ("pdfs", os.path.join("temp","target","default"), "test_sherlock.pdf", [ ["Bohemia", "Trincomalee"], # Page 1
                           ["hundreds of times" ], # Page 2
                           ]),
            (".", os.path.join("temp","target","recipe"), os.path.join("..","test", "pdfs", "1.pdf"), [ ["Simply","Recipes"],
                                 ]),
            (".", os.path.join("temp","target","recipe"), os.path.join("..","test", "pdfs", "test_recipe_sideways.pdf"), [ ["Simply","Recipes", 'spinach'],
                                 ]),
        ]

    #@pytest.mark.skipif(True, reason="Just testing")
    @pytest.mark.parametrize("dirname, tgt_folder, filename, expected", pdf_tests)
    def test_standalone(self, dirname, tgt_folder, filename, expected):
        """
            Test the single file conversion with no filing.  
            Tests relative paths (".."), files in subirs, and files in current dir
            Checks for that _ocr file is created and keywords found in pdf.
            Modify :attribute:`pdf_tests` for changing keywords, etc

            :param expected: List of keywords lists per page.  expected[0][1] is the second keyword to assert on page 1
        """
        # Run a single file conversion

        # First redo the unix-style paths, in case we're running on windows
        # Assume paths in unix-style
        dirname = os.path.join(*(dirname.split("/")))
        tgt_folder = os.path.join(*(tgt_folder.split("/")))
        filename = os.path.join(*(filename.split("/")))


        cwd = os.getcwd()
        os.chdir(dirname)
        opts = [filename, '--skip-preprocess']
        self.p.go(opts)

        out_filename = filename.replace(".pdf", "_ocr.pdf")
        assert(os.path.exists(out_filename))
        for i,t in enumerate(self._iter_pdf(out_filename)):
            if len(expected) > i:
                for keyword in expected[i]:
                    assert(keyword in t)
            print ("\n----------------------\nPage %d\n" % i)
            print t
        os.remove(out_filename)
        os.chdir(cwd)

    #@pytest.mark.skipif(True, reason="just testing")
    @pytest.mark.parametrize("dirname, tgt_folder, filename, expected", [pdf_tests[0]])
    def test_standalone_email(self, dirname, tgt_folder, filename, expected):
        """
            Get coverage on the email after conversion of a single file.
            Use mock to stub out the smtpllib
        """
        # Run a single file conversion

        # Mock the smtplib to test the email functions
        with patch("smtplib.SMTP") as mock_smtp:
            cwd = os.getcwd()
            os.chdir(dirname)
            opts = [filename, "--preprocess", "--config=test_pypdfocr_config.yaml", "-m"]
            self.p.go(opts)

            out_filename = filename.replace(".pdf", "_ocr.pdf")
            assert(os.path.exists(out_filename))
            for i,t in enumerate(self._iter_pdf(out_filename)):
                if len(expected) > i:
                    for keyword in expected[i]:
                        assert(keyword in t)
                print ("\n----------------------\nPage %d\n" % i)
                print t
            os.remove(out_filename)
            os.chdir(cwd)
            
            # Assert the smtp calls
            instance = mock_smtp.return_value
            assert(instance.starttls.called)
            instance.login.assert_called_once_with("someone@gmail.com", "blah")
            assert(instance.sendmail.called)

    @patch('shutil.move')
    @pytest.mark.parametrize("config", [("test_pypdfocr_config.yaml"), ("test_pypdfocr_config_no_move_original.yaml")])
    @pytest.mark.parametrize("dirname, tgt_folder, filename, expected", pdf_tests[0:3])
    def test_standalone_filing(self, mock_move, config, dirname, tgt_folder, filename, expected):
        """
            Test filing of single pdf.  Also test moving of original file.

            Kind of hacked up right now, but it tries to test a lot of things (maybe too many)
        """

        # Mock the move function so we don't actually end up filing
        cwd = os.getcwd()
        if os.path.exists("temp"):
            os.chdir("temp")
            for d in [os.path.join('target', 'patents'), os.path.join('target','recipe')]:
                if os.path.exists(d):
                    os.removedirs(d)
            os.chdir(cwd)

        os.chdir(dirname)
        print("Current direcxtory: %s" % os.getcwd())
        #opts = [filename, "--config=test_pypdfocr_config.yaml", "-f"]
        opts = [filename, '--skip-preprocess', "--config=%s" % config, "-f"]
        self.p.go(opts)

        out_filename = filename.replace(".pdf", "_ocr.pdf")
        assert(os.path.exists(out_filename))
        for i,t in enumerate(self._iter_pdf(out_filename)):
            if len(expected) > i:
                for keyword in expected[i]:
                    assert(keyword in t)
            print ("\n----------------------\nPage %d\n" % i)
            print t
        os.remove(out_filename)
        os.chdir(cwd)
        
        # Assert the smtp calls
        calls = [call(out_filename,
                        os.path.abspath(os.path.join(tgt_folder,os.path.basename(out_filename))))]
        if not "no_move_original" in config:
            new_file_name = os.path.basename(filename).replace(".pdf", "_2.pdf")
            calls.append(call(filename,
                                os.path.abspath(os.path.join("temp","original", new_file_name))))
        mock_move.assert_has_calls(calls)

    def test_set_binaries(self):
        """ Test the setup_exteral_tools
        """
        self.p.config = {}
        self.p.config["tesseract"] = {"binary":"/usr/bin/tesseract"}
        self.p.config["ghostscript"] = {"binary":"/usr/bin/ghostscript"}
        self.p._setup_external_tools()
        if not os.name == 'nt':
            assert(self.p.ts.binary == "/usr/bin/tesseract")
            assert(self.p.gs.binary == "/usr/bin/ghostscript")
        else:
            assert(self.p.ts.binary == '"/usr/bin/tesseract"')
            assert(self.p.gs.binary == '"/usr/bin/ghostscript"')


