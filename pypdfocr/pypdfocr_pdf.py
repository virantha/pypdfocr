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


# Following code is adapted and modified from hocr-pdf.py released under
# Apache License, Version 2.0 available at 
# https://code.google.com/p/hocr-tools/source/browse/hocr-pdf
#   - Code was improved to allow multi-page hocr files
"""
    Wrap pdf generation and text addition code
"""

from optparse import OptionParser
import sys, os
import re
import logging
import shutil
import time
import tempfile
import glob

import cStringIO
import base64
import zlib
import math

from cgi import escape
# Pkg to read multiple image tiffs
from PIL import Image
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.etree.ElementTree import ElementTree, ParseError
import xml.etree

# Import Pypdf2
from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter, utils

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus.paragraph import Paragraph

from pypdfocr_util import Retry
from functools import partial

class RotatedPara(Paragraph):
    """
        Used for rotating text, since the low-level rotate method in textobject's don't seem to 
        do anything
    """

    def __init__ (self, text, style, angle):
        Paragraph.__init__(self, text, style)
        self.angle = angle

    def draw(self):
        self.canv.saveState()
        self.canv.translate(0,0)
        self.canv.rotate(self.angle)
        Paragraph.draw(self)
        self.canv.restoreState()
    def beginText(self, x, y):
        t = self.canv.beginText(x,y)
        t.setTextRenderMode(3)  # Set to zero if you want the text to appear
        #t.setTextRenderMode(0)  # Set to zero if you want the text to appear
        return t

class PyPdf(object):
    """Class to create pdfs from images"""
    # Some regexes to compile once
    regex_bbox = re.compile('bbox((\s+\d+){4})')
    regex_baseline = re.compile('baseline((\s+[\d\.\-]+){2})')
    regex_fontspec = re.compile('x_font\s+(.+);\s+x_fsize\s+(\d+)')
    regex_textangle = re.compile('textangle\s+(\d+)')

    def __init__(self, gs):
        self.gs = gs # Pointer to ghostscript object


    def get_transform(self, rotation, tx, ty):
        # Code taken from here:
        # http://stackoverflow.com/questions/6041244/how-to-merge-two-landscape-pdf-pages-using-pypdf/17392824#17392824
        # Unclear why PyPDF2 builtin page rotation functions don't work
        translation = [[1, 0, 0],
                       [0, 1, 0],
                       [-tx,-ty,1]]
        rotation = math.radians(rotation)
        rotating = [[math.cos(rotation), math.sin(rotation),0],
                    [-math.sin(rotation),math.cos(rotation), 0],
                    [0,                  0,                  1]]
        rtranslation = [[1, 0, 0],
                       [0, 1, 0],
                       [tx,ty,1]]
        ctm = utils.matrixMultiply(translation, rotating)
        ctm = utils.matrixMultiply(ctm, rtranslation)

        return ctm[0][0], ctm[0][1], ctm[1][0], ctm[1][1], ctm[2][0], ctm[2][1]

    def mergeRotateAroundPointPage(self,page, page2, rotation, tx, ty):
        # Code taken from here:
        # http://stackoverflow.com/questions/6041244/how-to-merge-two-landscape-pdf-pages-using-pypdf/17392824#17392824
        # Unclear why PyPDF2 builtin page rotation functions don't work
        translation = [[1, 0, 0],
                       [0, 1, 0],
                       [-tx,-ty,1]]
        rotation = math.radians(rotation)
        rotating = [[math.cos(rotation), math.sin(rotation),0],
                    [-math.sin(rotation),math.cos(rotation), 0],
                    [0,                  0,                  1]]
        rtranslation = [[1, 0, 0],
                       [0, 1, 0],
                       [tx,ty,1]]
        ctm = utils.matrixMultiply(translation, rotating)
        ctm = utils.matrixMultiply(ctm, rtranslation)

        return page.mergeTransformedPage(page2, [ctm[0][0], ctm[0][1],
                                                 ctm[1][0], ctm[1][1],
                                                 ctm[2][0], ctm[2][1]])

    def overlay_hocr_pages(self, dpi, hocr_filenames, orig_pdf_filename):
        
        logging.debug("Going to overlay following files onto %s" % orig_pdf_filename)
        # Sort the hocr_filenames into natural keys!
        hocr_filenames.sort(key=lambda x: self.natural_keys(x[0] ))
        logging.debug(hocr_filenames)

        pdf_dir, pdf_basename = os.path.split(orig_pdf_filename)
        basename = os.path.splitext(pdf_basename)[0]
        pdf_filename = os.path.join(pdf_dir, "%s_ocr.pdf" % (basename))

        text_pdf_filenames = []
        for img_filename, hocr_filename in hocr_filenames:
            text_pdf_filename = self.overlay_hocr_page(dpi, hocr_filename, img_filename)
            logging.info("Created temp OCR'ed pdf containing only the text as %s" % (text_pdf_filename))
            text_pdf_filenames.append(text_pdf_filename)

        # Now, concatenate this text_pdfs into one single file.
        # This is a hack to save memory/running time when we have to do the actual merge with a writer

        all_text_filename = os.path.join(pdf_dir, "%s_text.pdf" % (basename))
        merger = PdfFileMerger()
        for text_pdf_filename in text_pdf_filenames:
            merger.append(PdfFileReader(file(text_pdf_filename, 'rb')))
        merger.write(all_text_filename)
        merger.close()
	del merger


        writer = PdfFileWriter()
        orig = open(orig_pdf_filename, 'rb')
        text_file = open(all_text_filename, 'rb')

        for orig_pg, text_pg in zip(self.iter_pdf_page(orig), self.iter_pdf_page(text_file)):
            orig_pg = self._get_merged_single_page(orig_pg, text_pg)
            writer.addPage(orig_pg)

        with open(pdf_filename, 'wb') as f:
            # Flush out this page merge so we can close the text_file
            writer.write(f)

        orig.close()
        text_file.close()

        # Windows sometimes locks the temp text file for no reason, so we need to retry a few times to delete
        for fn in text_pdf_filenames:
            #os.remove(fn)
            Retry(partial(os.remove, fn), tries=10, pause=3).call_with_retry() 

        os.remove(all_text_filename)
        logging.info("Created OCR'ed pdf as %s" % (pdf_filename))

        return pdf_filename

    def _get_merged_single_page(self, original_page, ocr_text_page):
        """
            Take two page objects, rotate the text page if necessary, and return the merged page
        """
        orig_rotation_angle = int(original_page.get('/Rotate', 0))

        if orig_rotation_angle != 0:
            logging.info("Original Rotation: %s" % orig_rotation_angle)
            self.mergeRotateAroundPointPage(original_page, ocr_text_page, orig_rotation_angle, ocr_text_page.mediaBox.getWidth()/2, ocr_text_page.mediaBox.getWidth()/2)
            # None of these commands worked for me:
            #orig_pg.rotateCounterClockwise(orig_rotation_angle)
            #orig_pg.mergeRotatedPage(text_pg,orig_rotation_angle)
        else:
            original_page.mergePage(ocr_text_page)
        original_page.compressContentStreams()
        return original_page


    def _get_img_dims(self, img_filename):
        """
            :rval: (width, height, dpi)
        """
        img = Image.open(img_filename)
        w,h = img.size
        dpi = img.info['dpi']
        width = w*72.0/dpi[0]
        height = h*72.0/dpi[1]
        del img
        return (width, height, dpi)

    def overlay_hocr_page(self, dpi, hocr_filename, img_filename):
        hocr_dir, hocr_basename = os.path.split(hocr_filename)
        img_dir, img_basename = os.path.split(img_filename)
        logging.debug("hocr_filename:%s, hocr_dir:%s, hocr_basename:%s" % (hocr_filename, hocr_dir, hocr_basename))
        assert(img_dir == hocr_dir)

        #basename = hocr_basename.split('.')[0]
        basename = os.path.splitext(hocr_basename)[0]
        pdf_filename = os.path.join("text_%s_ocr.pdf" % (basename))

        # Switch to the hocr directory to make this easier
        cwd = os.getcwd()
        if hocr_dir != "":
            os.chdir(hocr_dir)

        with open(pdf_filename, "wb") as f:
            logging.info("Overlaying hocr and creating text pdf %s" % pdf_filename)
            pdf = Canvas(f, pageCompression=1)
            pdf.setCreator('pypdfocr')
            pdf.setTitle(os.path.basename(hocr_filename))
            pdf.setPageCompression(1)

            width, height, dpi_jpg = self._get_img_dims(img_basename)
            pdf.setPageSize((width,height))
            logging.info("Page width=%f, height=%f" % (width, height))

            pg_num = 1

            logging.info("Adding text to page %s" % pdf_filename)
            self.add_text_layer(pdf,hocr_basename,pg_num,height,dpi)
            pdf.showPage()
            pdf.save()

        os.chdir(cwd)
        return os.path.join(hocr_dir, pdf_filename)

    def iter_pdf_page(self, f):
        reader = PdfFileReader(f)
        for pgnum in range(reader.getNumPages()):
            pg = reader.getPage(pgnum)
            yield pg

    def _atoi(self,text):
        return int(text) if text.isdigit() else text

    def natural_keys(self, text):
        '''
        alist.sort(key=natural_keys) sorts in human order
        http://nedbatchelder.com/blog/200712/human_sorting.html
        (See Toothy's implementation in the comments)
        '''
        return [ self._atoi(c) for c in re.split('(\d+)', text) ]

    def add_text_layer(self,pdf, hocrfile, page_num,height, dpi):
      """Draw an invisible text layer for OCR data.

        This function really needs to get cleaned up
        
      """
      hocr = ElementTree()
      try: 
        # It's possible tesseract has failed and written garbage to this hocr file, so we need to catch any exceptions
          hocr.parse(hocrfile)
      except Exception:
          logging.info("Error loading hocr, not adding any text")
          return 

      logging.debug(xml.etree.ElementTree.tostring(hocr.getroot()))
      for c in hocr.getroot():  # Find the <body> tag
          if c.tag != 'body':
              continue
      for page in c: # Each child in the body is a page tag
          if (page.attrib['class'] != "ocr_page"):
              assert ("Why is this hocr not paging properly??")
          if page.attrib['id'] == 'page_%d' %(page_num):
              break

      for line in page.findall(".//{http://www.w3.org/1999/xhtml}span"):
      #for line in page.findall(".//span"):
        if line.attrib['class'] != 'ocr_line':
          continue
        linebox = self.regex_bbox.search(line.attrib['title']).group(1).split()
        textangle = self.regex_textangle.search(line.attrib['title'])
        if textangle:
            textangle = self._atoi(textangle.group(1))
        else:
            textangle = 0

        try:
          baseline = self.regex_baseline.search(line.attrib['title']).group(1).split()
        except AttributeError:
          baseline = [ 0, 0 ]

        linebox = [float(i) for i in linebox]
        baseline = [float(i) for i in baseline]

        for word in line:
          if word.attrib['class'] != 'ocrx_word':
            continue
          word_text = []
          for child in word.iter():
              if child.text:
                  word_text.append(child.text)
          word.text = ' '.join(word_text)
          if word.text is None:
            continue
          logging.debug("word: %s, angle: %d" % ( word.text.strip(), textangle))


          box = self.regex_bbox.search(word.attrib['title']).group(1).split()
          #b = self.polyval(baseline, (box[0] + box[2]) / 2 - linebox[0]) + linebox[3]
          box = [float(i) for i in box]

          # Transform angle to x,y co-ords needed for proper text placement
          # We only support 0, 90, 180, 270!.  Anything else, we'll just use the normal orientation for now

          coords = { 0: (box[0], box[1]),
                    90: (box[0], box[3]),  # facing right
                    180: (box[2], box[3]), # upside down
                    270: (box[2], box[1]), # facing left
                    }
          x,y = coords.get(textangle, (box[0], box[1]))

          style = getSampleStyleSheet()
          normal = style["BodyText"]
          normal.alignment = TA_LEFT
          normal.leading = 0
          font_name, font_size = self._get_font_spec(word.attrib['title'])
          normal.fontName = "Helvetica"
          normal.fontSize = font_size

          para = RotatedPara(escape(word.text.strip()), normal, textangle)
          para.wrapOn(pdf, para.minWidth(), 100)  # Not sure what to use as the height  here
          para.drawOn(pdf, x*72/dpi, height - y*72/dpi)



    def polyval(self,poly, x):
      return x * poly[0] + poly[1]


    def _get_font_spec(self, tag):
        try:
            fontspec = self.regex_fontspec.search(tag).groups()
            fontname, fontsize = fontspec
        except Exception:
            fontname = ""
            fontsize = "8"
        return (fontname, self._atoi(fontsize))
