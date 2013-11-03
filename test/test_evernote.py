#from pypdfocr import PyPDFOCR as P
import pypdfocr.pypdfocr_filer_evernote as P
import pytest
import os

import evernote.api.client
import evernote.edam.type.ttypes as Types
import hashlib

from mock import patch, call

class TestEvernote:

    def test_connecct(self):
        # Tricky mocking.  Need to mock the EvernoteClient import in pypdfocr_filer_evernote.py file
        with patch("pypdfocr.pypdfocr_filer_evernote.EvernoteClient") as mock_evernote_client:
            p = P.PyFilerEvernote("TOKEN")
            inst = mock_evernote_client.return_value
            assert(inst.get_user_store.called)

    @patch('shutil.move')
    def test_file_original(self, mock_move):
        with patch("pypdfocr.pypdfocr_filer_evernote.EvernoteClient") as mock_evernote_client:
            p = P.PyFilerEvernote("TOKEN")
            filename = os.path.join("pdfs","test_recipe.pdf")

            # First, test code that does not move original
            p.file_original(filename)
            assert (not mock_move.called)

            # Now test moving
            p.set_original_move_folder(os.path.join("temp", "original"))
            p.file_original(filename)
            mock_move.assert_called_with(filename, os.path.join("temp","original", "test_recipe_2.pdf"))

    @patch('os.remove')
    def test_move_to_folder(self, mock_remove):
        with patch("pypdfocr.pypdfocr_filer_evernote.EvernoteClient") as mock_evernote_client:
            p = P.PyFilerEvernote("TOKEN")
	    filename = os.path.join("pdfs", "test_recipe.pdf")
            foldername = 'recipe'
            with pytest.raises(AssertionError):
                p.move_to_matching_folder(filename, foldername)
            p.set_target_folder('target')
            with pytest.raises(AssertionError):
                p.move_to_matching_folder(filename, foldername)
            p.set_default_folder('default')
            p.move_to_matching_folder(filename, None)
            p.move_to_matching_folder(filename, foldername)
            
            mock_client = mock_evernote_client.return_value
            assert(mock_client.get_note_store.called)
            assert(mock_client.get_note_store.return_value.createNote.called)
            mock_remove.assert_called_with(filename)

            


    def test_create_note(self):
        with patch("pypdfocr.pypdfocr_filer_evernote.EvernoteClient") as mock_evernote_client:
            p = P.PyFilerEvernote("TOKEN")
            notebook = Types.Notebook()
            notebook.name = "recipe"
            filename = "pdfs/test_recipe.pdf"
            note = p._create_evernote_note(notebook, filename)
            xml = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
            assert(note.content.startswith(xml))

            md5 = hashlib.md5()
            with open(filename,'rb') as f: 
                pdf_bytes = f.read()
                md5.update(pdf_bytes)

            md5hash = md5.hexdigest()
            
            assert(md5hash in note.content)
            assert(note.resources[0].data.bodyHash == md5hash)


    def test_check_notebook(self):
        with patch("pypdfocr.pypdfocr_filer_evernote.EvernoteClient") as mock_evernote_client:
            p = P.PyFilerEvernote("TOKEN")
            p._check_and_make_notebook("new_notebook")
            # Let's assert that we tried to create a new notebook
            mock_client = mock_evernote_client.return_value
            assert(mock_client.get_note_store.called)
            create_func = mock_client.get_note_store.return_value.createNotebook
            update_func = mock_client.get_note_store.return_value.updateNotebook
            assert(create_func.called)
            assert(not update_func.called)
            notebook = create_func.call_args[0][0]
            assert(notebook.name == 'new_notebook')

            # Now, let's setup a value for the notebooks, so we test the code for
            # a "pre-exisiting" notebook
            test_notebook = Types.Notebook()
            test_notebook.name = "new_notebook"
            mock_client.get_note_store.return_value.listNotebooks.return_value = [test_notebook]
            p._check_and_make_notebook("new_notebook")

            # Now check that the code to update a notebook stack is correct
            test_notebook.stack = "new_stack"
            update_func = mock_client.get_note_store.return_value.updateNotebook
            p.set_target_folder("Boogie")
            p._check_and_make_notebook("new_notebook")
            # Check that the update call was called with correct arguments
            assert(update_func.called)
            notebook = update_func.call_args[0][0]
            assert(notebook.stack == 'Boogie')
            

    def test_add_folder_target(self):
        with patch("pypdfocr.pypdfocr_filer_evernote.EvernoteClient") as mock_evernote_client:
            p = P.PyFilerEvernote("TOKEN")
            p.add_folder_target("folder1", ["target1", "target2"])
            with pytest.raises(AssertionError):
                p.add_folder_target("folder1", ["target1", "target2"])
            p.add_folder_target("folder2", ["target1", "target2"])
            assert("folder1" in p.folder_targets.keys())
            assert("folder2" in p.folder_targets.keys())

                    
    
        
