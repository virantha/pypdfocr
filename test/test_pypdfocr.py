#from pypdfocr import PyPDFOCR as P
import pypdfocr.pypdfocr as P
import pytest
import os

from PyPDF2 import PdfFileReader


class TestPydfocr:

    def setup(self):
        self.p = P.PyPDFOCR()

    def _iter_pdf(self, filename):
        reader = PdfFileReader(filename)
        for pgnum in range(reader.getNumPages()):
            text = reader.getPage(pgnum).extractText()
            text = text.encode('ascii', 'ignore')
            text = text.replace('\n', ' ')
            yield text

    @pytest.mark.parametrize("dirname, filename, expected", [
        (".", "../test/pdfs/test_recipe.pdf", [ ["Spinach Recipe","Drain any excess"],
                                 ]),
        ("pdfs", "test_sherlock.pdf", [ ["Bohemia", "Trincomalee"], # Page 1
                           ["hundreds of times" ], # Page 2
                           ]),
        (".", "pdfs/test_patent.pdf", [ 
                           ["ASYNCHRONOUS", "subject to a", "20 Claims"], # Page 1
                           ["FOREIGN PATENT" ], # Page 2
                            ]),
    ])

    def test_standalone(self, dirname, filename, expected):
        """
            :param expected: List of keywords lists per page.  expected[0][1] is the second keyword to assert on page 1
        """
        # Run a single file conversion
        cwd = os.getcwd()
        os.chdir(dirname)
        opts = [filename]
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


