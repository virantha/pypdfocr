#from pypdfocr import PyPDFOCR as P
from pypdfocr import pypdfocr as P
import os

from mock import patch, call

class TestPDFFiler:

    @patch('shutil.move')
    def test_file_by_filename(self, mock_move):
        """
            Test filing of single pdf based on filename.
        """

        # Mock the move function so we don't actually end up filing
        p = P.PyPDFOCR()
        cwd = os.getcwd()
        filename = os.path.join(os.path.dirname(__file__),
                                "pdfs",
                                "test_super_long_keyword.pdf")
        out_filename = filename.replace(".pdf", "_ocr.pdf")

        if os.path.exists(out_filename):
            os.remove(out_filename)

        print("Current directory: %s" % os.getcwd())
        #opts = [filename, "--config=test_pypdfocr_config.yaml", "-f"]
        conf_path = os.path.join(
            os.path.dirname(__file__), 'test_pypdfocr_config.yaml')

        opts = [filename, "--config={}".format(conf_path), "-f", "-n"]
        p.go(opts)

        assert(os.path.exists(out_filename))
        os.remove(out_filename)

        calls = [call(out_filename, os.path.abspath(os.path.join('temp', 'target','recipe', os.path.basename(out_filename))))]
        mock_move.assert_has_calls(calls)




