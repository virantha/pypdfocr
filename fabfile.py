from fabric.api import *
import os
 
  
def build_dist():
    if os.name == 'nt':
        # Call the pyinstaller
        local("python ../pyinstaller/pyinstaller.py pypdfocr_windows.spec --onefile")

def prep_release():
    # Build the documentation
    # Convert the README.md to README.rst
    local("pandoc README.md -f markdown -t rst -o README.rst")


