=======  ========   ======
Version  Date       Changes
-------  --------   ------

v0.9.1   10/11/16   Fixes (#43, #41)
v0.9.0   2/29/16    Fixed rotated page text, Mac OS X invisible fonts, and pdf merge slowdown
v0.8.5   2/21/16    Better ctrl-c and cleanup behavior
v0.8.4   2/18/16    Maintenance release
v0.8.3   2/18/16    Bug fix for multiprocessing on windows, ctrl-c interrupt, and integer keywords
v0.8.2   12/8/14    Fixed imagemagick invocation on windows.  Parallelized preprocessing and tesseract execution
v0.8.1   12/5/14    Added --skip-preprocess option, scan_interval option, and fixed too many open files bug during page overlay
v0.8.0   10/27/14   Added preprocessing to clean up prior to tesseract, bug fixes on file names with spaces/dots
v0.7.6   9/10/14    Fixed issue 17 rotation bug
v0.7.5   8/18/14    Update for Tesseract 3.03 .hocr filename change
v0.7.4   3/28/14    Bug fix on pdf assembly
v0.7.3   3/27/14    Modified internals to use single image per page (instead of multipage tiff). Also enabled orientation detection
v0.7.2   3/26/14    Switched from Pil to Pillow. Now uses original images from PDF in output pdf (no dpi/color/quality changes!)
v0.7.1   3/25/14    OCR Language is now an option
v0.7.0   3/25/14    Now honors original pdf resolution
v0.6.1   2/16/14    Bug fix for pdfs with only numbers in the filename
v0.6.0   1/16/14    Added filing based on filename match as fallback, added tesseract version check
v0.5.4   1/12/14    Fixed bug with reordering of text pages on certain platforms(glob)
v0.5.3   12/12/13   Fix to evernote server specification
v0.5.2   12/08/13   Fix to lowercase keywords
v0.5.1   11/02/13   Fixed a bunch of windows critical path handling issues
v0.5.0   10/30/13   Email status added, 90% test coverage
v0.4.1   10/28/13   Made HOCR parsing more robust
v0.4.0   10/28/13   Added early Evernote upload support
v0.3.1   10/24/13   Path fix on windows
v0.3.0   10/23/13   Added filing of converted pdfs using a configuration file to specify target directories based on keyword matches in the pdf text
v0.2.2   10/22/13   Added a console script to put the pypdfocr script into your bin
v0.2.1   10/22/13   Fix to initial packaging problem.
v0.2.0   10/21/13   Initial release.
=======  ========   ======
