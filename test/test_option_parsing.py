#from pypdfocr import PyPDFOCR as P
import pypdfocr.pypdfocr as P
import pytest


class TestOptions:

    def setup(self):
        self.p = P.PyPDFOCR()


    def test_standalone(self):
        opts = ["blah.pdf"]
        self.p.get_options(opts)

        opts.append('-d')
        self.p.get_options(opts)
        assert(self.p.debug)

        opts.append('-v')
        self.p.get_options(opts)
        assert(self.p.verbose)

        opts.append('--preprocess')
        self.p.get_options(opts)
        assert(not self.p.skip_preprocess)

        assert(not self.p.enable_filing)
        assert(self.p.config == {})

    def test_standalone_filing(self):
        opts = ["blah.pdf"]
        opts.append('-f')

        # Assert that filing option requires a config file
        with pytest.raises(SystemExit):
            self.p.get_options(opts)

        # Assert that it checks that the config file is present
        opts.append('--config=test_option_config.yaml')
        self.p.get_options(opts)
        assert(self.p.enable_filing)
        assert(self.p.config)

    def test_standalone_filing_evernote(self):
        # Check when evernote is enabled
        opts = ["blah.pdf"]
        opts.append('-e')
        # Assert that it checks that the config file is present
        with pytest.raises(SystemExit):
            self.p.get_options(opts)

        opts.append('--config=test_option_config.yaml')
        self.p.get_options(opts)
        # Enabling -e should turn on filing too
        assert(self.p.enable_filing)
        assert(self.p.enable_evernote)
        assert(self.p.config)
        assert(not self.p.watch)

        opts.append('-f')
        self.p.get_options(opts)
        assert(self.p.enable_filing)
        assert(self.p.enable_evernote)
        assert(self.p.config)
        assert(not self.p.watch)

    def test_standalone_watch_conflict(self):
        # When pdf file is specified, we don't want to allow watch option
        opts = ["blah.pdf", '-w']
        with pytest.raises(SystemExit):
            self.p.get_options(opts)
                
    def test_watch_filing(self):
        opts = ['-w']
        # Catch watch without a dir
        with pytest.raises(SystemExit):
            self.p.get_options(opts)

        opts = ['-w temp']
        self.p.get_options(opts)
        assert(self.p.watch_dir)

        opts.append('--config=test_option_config.yaml')
        self.p.get_options(opts)
        assert(self.p.watch)
        assert(self.p.config)
        assert(not self.p.enable_filing)
        assert(not self.p.enable_evernote)

    def test_watch_filing_evernote(self):
        opts = ['-w temp', '-e', '--config=test_option_config.yaml']
        self.p.get_options(opts)
        assert(self.p.watch)
        assert(self.p.config)
        assert(self.p.enable_filing)
        assert(self.p.enable_evernote)

        opts = ['-w temp', '-f', '-e',  '--config=test_option_config.yaml']
        self.p.get_options(opts)
        assert(self.p.watch)
        assert(self.p.config)
        assert(self.p.enable_filing)
        assert(self.p.enable_evernote)

