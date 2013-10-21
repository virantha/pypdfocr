"""
Something
"""

import sys, os
import re
import logging
import shutil
import time
import glob

from threading import Lock

from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler

        
class PyPdfWatcher(FileSystemEventHandler):
    """
        Watch a folder for new pdf files

        If new file event, then add it to queue with timestamp
        If file mofified event, then change timestamp in queue
        Every 10 seconds pop-off queue and if timestamp older than 10 seconds,
            process the file
        else, push it back onto queue
    """
    events = {}
    events_lock = Lock()

    def __init__(self, monitor_dir):
        FileSystemEventHandler.__init__(self)

        self.monitor_dir = monitor_dir
        self.scan_interval = 3 # If no updates in 3 seconds process file

    def start(self):
        while True:
            observer = Observer()
            observer.schedule(self, self.monitor_dir)
            observer.start()
            print("Starting to watch for new pdfs in %s" % (self.monitor_dir))
            try:
                while True:
                    time.sleep(self.scan_interval)
                    newFile = self.check_queue()
                    if newFile:
                        print("Starting conversion for %s" % (newFile))
                        yield newFile
                        print("Conversion completed")
            except KeyboardInterrupt:
                observer.stop()
            observer.join()

        
    def rename_file_with_spaces(self, pdf_filename):
        filepath, filename = os.path.split(pdf_filename)
        if ' ' in filename:
            newFilename = os.path.join(filepath, filename.replace(' ','_'))
            logging.debug("Renaming spaces")
            logging.debug("---> %s \n ------> %s" % (pdf_filename, newFilename))
            shutil.move(pdf_filename, newFilename) 
            return newFilename
        else:
            return pdf_filename

    def check_for_new_pdf(self,ev_path):
        if ev_path.endswith(".pdf"):
            if not ev_path.endswith("_ocr.pdf"):
                PyPdfWatcher.events_lock.acquire()
                if not ev_path in PyPdfWatcher.events:
                    PyPdfWatcher.events[ev_path] = time.time()
                    logging.info ("Adding %s to event queue" % ev_path)
                else:
                    if PyPdfWatcher.events[ev_path] == -1:
                        logging.info ( "%s removing from event queue" % (ev_path))
                        del PyPdfWatcher.events[ev_path]
                    else: 
                        newTime = time.time()
                        logging.debug ( "%s already in event queue, updating timestamp to %d" % (ev_path, newTime))
                        PyPdfWatcher.events[ev_path]  = newTime
                PyPdfWatcher.events_lock.release()

                      
              
    def on_created(self, event):
        logging.debug ("on_created: %s at time %d" % (event.src_path, time.time()))
        self.check_for_new_pdf(event.src_path)

    def on_moved(self, event):
        logging.debug ("on_moved: %s" % event.src_path)
        self.check_for_new_pdf(event.dest_path)

    def on_modified(self, event):
        logging.debug ("on_modified: %s" % event.src_path)
        self.check_for_new_pdf(event.src_path)

    def on_deleted(self,event):
        logging.debug ("on_deleted: %s" % event.src_path)
        pass 

    def check_queue(self):
        # Called at regular time intervals
        # Chech the events queue for events that have been there longer
        # than given time period
        now = time.time()
        PyPdfWatcher.events_lock.acquire()
        for monitored_file, timestamp in PyPdfWatcher.events.items():
            if timestamp == -1:
                del PyPdfWatcher.events[monitored_file]
            elif now - timestamp > self.scan_interval:
                logging.info("Processing new file %s" % (monitored_file))
                # Remove this file from the dict
                del PyPdfWatcher.events[monitored_file]
                monitored_file = self.rename_file_with_spaces(monitored_file)
                PyPdfWatcher.events[monitored_file] = -1 # Add back into queue and mark as not needing further action in the event handler
                PyPdfWatcher.events_lock.release()
                return monitored_file
        PyPdfWatcher.events_lock.release()
        return None



