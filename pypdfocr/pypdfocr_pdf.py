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

# Pkg to read multiple image tiffs
from PIL import Image
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xml.etree.ElementTree import ElementTree, ParseError
import xml.etree

# Import Pypdf2
from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter, utils

class PyPdf(object):
    """Class to create pdfs from images"""

    def __init__(self, gs):
        self.load_invisible_font()
        self.gs = gs # Pointer to ghostscript object
        pass

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

    def overlay_hocr_pages(self, dpi, hocr_filenames, orig_pdf_filename, archive=False, archive_suffix="_orig.pdf"):
        
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


        writer = PdfFileWriter()
        orig = open(orig_pdf_filename, 'rb')
        orig_reader = PdfFileReader(orig)

        # Save  the properties
        pdf_info = orig_reader.getDocumentInfo()
        if pdf_info is not None:
            writer.addMetadata(pdf_info)

        writer.addMetadata({ '/PyPDFOCR': 'True' })

        # Loop through the pages
        for orig_pg, text_pg_filename in zip(self.iter_pdf_page(orig), text_pdf_filenames):
            text_file = open(text_pg_filename, 'rb')
            text_pg = self.iter_pdf_page(text_file).next()
            orig_rotation_angle = int(orig_pg.get('/Rotate', 0))

            if orig_rotation_angle != 0:
                logging.info("Original Rotation: %s" % orig_pg.get("/Rotate", 0))
                self.mergeRotateAroundPointPage(orig_pg, text_pg, orig_rotation_angle, text_pg.mediaBox.getWidth()/2, text_pg.mediaBox.getWidth()/2)

                # None of these commands worked for me:
                    #orig_pg.rotateCounterClockwise(orig_rotation_angle)
                    #orig_pg.mergeRotatedPage(text_pg,text_rotation_angle)
            else:
                orig_pg.mergePage(text_pg)
            orig_pg.compressContentStreams()
            writer.addPage(orig_pg)

            with open(pdf_filename, 'wb') as f:
                # Flush out this page merge so we can close the text_file
                writer.write(f)
            text_file.close()

        orig.close()

        for fn in text_pdf_filenames:
            os.remove(fn)

        print "Done on conversion: ", orig_pdf_filename
        if archive:
            original_filename = os.path.join(pdf_dir, "%s%s" % (basename, archive_suffix))
            ocr_filename = orig_pdf_filename
            print "Archiving PDF %s -> %s, %s -> %s" % (orig_pdf_filename, original_filename, pdf_filename, ocr_filename)
            os.rename(orig_pdf_filename, original_filename)
            os.rename(pdf_filename, ocr_filename)


        logging.info("Created OCR'ed pdf as %s" % (pdf_filename))
        return pdf_filename

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
      """Draw an invisible text layer for OCR data"""
      p1 = re.compile('bbox((\s+\d+){4})')
      p2 = re.compile('baseline((\s+[\d\.\-]+){2})')
      hocr = ElementTree()
      hocr.parse(hocrfile)
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
        linebox = p1.search(line.attrib['title']).group(1).split()

        try:
          baseline = p2.search(line.attrib['title']).group(1).split()
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
          logging.debug(word.text)
          #for child in word:
             #if child.tag:
                 #word.text = child.text

          if word.text is None:
            continue
          font_width = pdf.stringWidth(word.text.strip(), 'invisible', 8)
          if font_width <= 0:
            continue
          box = p1.search(word.attrib['title']).group(1).split()
          box = [float(i) for i in box]
          b = self.polyval(baseline, (box[0] + box[2]) / 2 - linebox[0]) + linebox[3]
          text = pdf.beginText()
          text.setTextRenderMode(3)  # double invisible
          text.setFont('invisible', 8)
          text.setTextOrigin(box[0] * 72 / dpi, height - b * 72 / dpi)
          box_width = (box[2] - box[0]) * 72 / dpi
          text.setHorizScale(100.0 * box_width / font_width)
          text.textLine(word.text.strip())
          #logging.debug( "Pg%s: %s" % (page_num,word.text.strip()))
          pdf.drawText(text)

    def polyval(self,poly, x):
      return x * poly[0] + poly[1]

# Glyphless variation of vedaal's invisible font retrieved from
# http://www.angelfire.com/pr/pgpf/if.html, which says:
# 'Invisible font' is unrestricted freeware. Enjoy, Improve, Distribute freely
    def load_invisible_font(self):
      font = """
    eJzdlk1sG0UUx/+zs3btNEmrUKpCPxikSqRS4jpfFURUagmkEQQoiRXgAl07Y3vL2mvt2ml8APXG
    hQPiUEGEVDhWVHyIC1REPSAhBOWA+BCgSoULUqsKcWhVBKjhzfPU+VCi3Flrdn7vzZv33ryZ3TUE
    gC6chsTx8fHck1ONd98D0jnS7jn26GPjyMIleZhk9fT0wcHFl1/9GRDPkTxTqHg1dMkzJH9CbbTk
    xbWlJfKEdB+Np0pBswi+nH/Nvay92VtfJp4nvEztUJkUHXsdksUOkveXK/X5FNuLD838ICx4dv4N
    I1e8+ZqbxwCNP2jyqXoV/fmhy+WW/2SqFsb1pX68SfEpZ/TCrI3aHzcP//jitodvYmvL+6Xcr5mV
    vb1ScCzRnPRPfz+LsRSWNasuwRrZlh1sx0E8AriddyzEDfE6EkglFhJDJO5u9fJbFJ0etEMB78D5
    4Djm/7kjT0wqhSNURyS+u/2MGJKRu+0ExNkrt1pJti9p2x6b3TBJgmUXuzgnDmI8UWMbkVxeinCw
    Mo311/l/v3rF7+01D+OkZYE0PrbsYAu+sSyxU0jLLtIiYzmBrFiwnCT9FcsdOOK8ZHbFleSn0znP
    nDCnxbnAnGT9JeYtrP+FOcV8nTlNnsoc3bBAD85adtCNRcsSffjBsoseca/lBE7Q09LiJOm/ttyB
    0+IqcwfncJt5q4krO5k7jV7uY+5m7mPebuLKUea7iHvk48w72OYF5rvZT8C8k/WvMN/Dc19j3s02
    bzPvZZv3me9j/ox5P9t/xdzPzPVJcc7yGnPL/1+GO1lPVTXM+VNWOTRRg0YRHgrUK5yj1kvaEA1E
    xAWiCtl4qJL2ADKkG6Q3XxYjzEcR0E9hCj5KtBd1xCxp6jV5mKP7LJBr1nTRK2h1TvU2w0akCmGl
    5lWbBzJqMJsdyaijQaCm/FK5HqspHetoTtMsn4LO0T2mlqcwmlTVOT/28wGhCVKiNANKLiJRlxqB
    F603axQznIzRhDSq6EWZ4UUs+xud0VHsh1U1kMlmNwu9kTuFaRqpURU0VS3PVmZ0iE7gct0MG/8+
    2fmUvKlfRLYmisd1w8pk1LSu1XUlryM1MNTH9epTftWv+16gIh1oL9abJZyjrfF5a4qccp3oFAcz
    Wxxx4DpvlaKKxuytRDzeth5rW4W8qBFesvEX8RFRmLBHoB+TpCmRVCCb1gFCruzHqhhW6+qUF6tC
    pL26nlWN2K+W1LhRjxlVGKmRTFYVo7CiJug09E+GJb+QocMCPMWBK1wvEOfRFF2U0klK8CppqqvG
    pylRc2Zn+XDQWZIL8iO5KC9S+1RekOex1uOyZGR/w/Hf1lhzqVfFsxE39B/ws7Rm3N3nDrhPuMfc
    w3R/aE28KsfY2J+RPNp+j+KaOoCey4h+Dd48b9O5G0v2K7j0AM6s+5WQ/E0wVoK+pA6/3bup7bJf
    CMGjwvxTsr74/f/F95m3TH9x8o0/TU//N+7/D/ScVcA=
    """
      ttf = cStringIO.StringIO(zlib.decompress(base64.decodestring(font)))
      pdfmetrics.registerFont(TTFont('invisible', ttf))

